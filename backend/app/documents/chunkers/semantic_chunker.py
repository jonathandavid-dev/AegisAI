"""
SemanticChunker — Enterprise document-aware chunker.

Strategy:
  1. Detect structural elements: headings (H1/H2/H3), paragraphs, tables, lists.
  2. Each logical section (heading + its following paragraphs) becomes a chunk group.
  3. If a section exceeds the max chunk size, it is split at paragraph boundaries
     (never mid-sentence) with configurable overlap.
  4. Tables are always kept as single atomic chunks.
  5. Every chunk carries rich metadata: section, heading, hierarchy_level, chunk_type, keywords.

Returns:
  List[ChunkResult] — dataclass with content + all metadata fields.
"""
import re
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class ChunkResult:
    """A single chunk with full metadata for enterprise RAG ingestion."""
    content: str
    chunk_type: str = "paragraph"   # paragraph | heading | table | list
    section: Optional[str] = None   # Top-level section title
    heading: Optional[str] = None   # Closest heading above this chunk
    hierarchy_level: int = 2         # 0=doc, 1=section, 2=subsection
    keywords: Optional[str] = None  # comma-separated extracted keywords


# --- Heading detection patterns ---
_H1 = re.compile(r'^#{1}\s+(.+)$', re.MULTILINE)
_H2 = re.compile(r'^#{2}\s+(.+)$', re.MULTILINE)
_H3 = re.compile(r'^#{3,}\s+(.+)$', re.MULTILINE)

# All-caps lines (common in PDF/docx): at least 3 words, no sentence-ending period
_CAPS_HEADING = re.compile(r'^([A-Z][A-Z\s\-/&]{4,80})$', re.MULTILINE)

# Numbered section markers: "1.", "1.1", "Section 2", "CHAPTER 3"
_NUMBERED = re.compile(
    r'^(?:(?:Section|Chapter|Part|Article)\s+\d+[\.:]\s+.+|\d+(?:\.\d+)*[\.:]\s+.{3,})$',
    re.MULTILINE | re.IGNORECASE
)

# Table markers (markdown-style and plain separator rows)
_TABLE_ROW = re.compile(r'\|.*\|')
_TABLE_SEP = re.compile(r'^\s*\|?[-:\s|]{3,}\|?\s*$', re.MULTILINE)

# Bullet / ordered list
_LIST_ITEM = re.compile(r'^(\s*[-*•]\s+|\s*\d+\.\s+)', re.MULTILINE)


def _detect_heading(line: str) -> tuple[Optional[str], int]:
    """
    Returns (heading_text, hierarchy_level) if the line is a heading, else (None, 2).
    hierarchy_level: 1 = major section, 2 = subsection.
    """
    # Markdown headings
    if _H1.match(line):
        return _H1.match(line).group(1).strip(), 1
    if _H2.match(line):
        return _H2.match(line).group(1).strip(), 2
    if _H3.match(line):
        return _H3.match(line).group(1).strip(), 2
    # Numbered sections
    if _NUMBERED.match(line.strip()):
        return line.strip(), 1
    # ALL CAPS headings (PDF artefacts)
    cap_m = _CAPS_HEADING.match(line.strip())
    if cap_m and len(line.strip().split()) >= 2:
        return cap_m.group(1).strip(), 1
    return None, 2


def _extract_keywords(text: str, max_words: int = 8) -> str:
    """Extract the most distinctive words from a text block as keywords."""
    stopwords = {
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to',
        'for', 'of', 'with', 'by', 'from', 'is', 'are', 'was', 'were',
        'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did',
        'will', 'would', 'could', 'should', 'may', 'might', 'shall', 'can',
        'that', 'this', 'these', 'those', 'it', 'its', 'as', 'if', 'so',
        'not', 'no', 'nor', 'up', 'out', 'into', 'through', 'during',
        'between', 'each', 'than', 'then', 'when', 'where', 'which', 'who',
        'whom', 'how', 'all', 'both', 'any', 'each', 'more', 'most', 'other',
        'such', 'their', 'they', 'them', 'our', 'we', 'us', 'i', 'you', 'he',
        'she', 'his', 'her', 'your', 'my', 'me'
    }
    words = re.findall(r'\b[a-zA-Z]{4,}\b', text)
    freq: dict = {}
    for w in words:
        lw = w.lower()
        if lw not in stopwords:
            freq[lw] = freq.get(lw, 0) + 1
    sorted_words = sorted(freq.items(), key=lambda x: x[1], reverse=True)
    return ', '.join(w for w, _ in sorted_words[:max_words])


def _is_table_block(lines: List[str]) -> bool:
    """Returns True if this group of lines forms a table."""
    pipe_count = sum(1 for l in lines if _TABLE_ROW.search(l))
    return pipe_count >= 2


def _split_paragraph(text: str, max_size: int, overlap: int) -> List[str]:
    """Split a large paragraph at sentence boundaries with overlap."""
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    chunks = []
    current: List[str] = []
    current_len = 0
    
    for sent in sentences:
        if current_len + len(sent) > max_size and current:
            chunks.append(' '.join(current))
            # Overlap: keep last N chars worth of sentences
            overlap_sents: List[str] = []
            overlap_len = 0
            for s in reversed(current):
                if overlap_len + len(s) <= overlap:
                    overlap_sents.insert(0, s)
                    overlap_len += len(s)
                else:
                    break
            current = overlap_sents + [sent]
            current_len = sum(len(s) for s in current)
        else:
            current.append(sent)
            current_len += len(sent)
    
    if current:
        chunks.append(' '.join(current))
    return [c for c in chunks if c.strip()]


class SemanticChunker:
    """
    Document-aware chunker preserving section hierarchy.
    
    Parameters
    ----------
    chunk_size : int
        Maximum character size for a single chunk (default 1200).
    chunk_overlap : int
        Character overlap between adjacent chunks when splitting large sections (default 150).
    min_chunk_size : int
        Minimum characters before a chunk is accepted (default 100).
    """

    def __init__(
        self,
        chunk_size: int = 1200,
        chunk_overlap: int = 150,
        min_chunk_size: int = 100
    ):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.min_chunk_size = min_chunk_size

    def split_text(self, text: str) -> List[ChunkResult]:
        """
        Splits document text into semantically meaningful chunks with full metadata.
        """
        if not text or not text.strip():
            return []

        lines = text.split('\n')
        
        # --- PASS 1: Segment into structural blocks ---
        blocks: List[dict] = []   # {type, content, heading, section, level}
        
        current_section = None
        current_heading = None
        current_level = 0
        current_para: List[str] = []
        current_table: List[str] = []
        in_table = False
        
        def flush_para():
            nonlocal current_para
            text_block = '\n'.join(current_para).strip()
            if text_block and len(text_block) >= 20:
                is_list = bool(_LIST_ITEM.match(current_para[0])) if current_para else False
                blocks.append({
                    'type': 'list' if is_list else 'paragraph',
                    'content': text_block,
                    'section': current_section,
                    'heading': current_heading,
                    'level': current_level
                })
            current_para = []

        def flush_table():
            nonlocal current_table, in_table
            table_text = '\n'.join(current_table).strip()
            if table_text:
                blocks.append({
                    'type': 'table',
                    'content': table_text,
                    'section': current_section,
                    'heading': current_heading,
                    'level': current_level
                })
            current_table = []
            in_table = False

        for line in lines:
            stripped = line.strip()
            
            # --- Table detection ---
            if _TABLE_ROW.search(line) or (in_table and _TABLE_SEP.match(line)):
                if not in_table:
                    flush_para()
                    in_table = True
                current_table.append(line)
                continue
            elif in_table:
                flush_table()
            
            # --- Heading detection ---
            heading_text, hlevel = _detect_heading(stripped)
            if heading_text and len(stripped) < 120:
                flush_para()
                if hlevel == 1:
                    current_section = heading_text
                    current_heading = heading_text
                else:
                    current_heading = heading_text
                current_level = hlevel
                # Include heading as a short standalone chunk for searchability
                blocks.append({
                    'type': 'heading',
                    'content': heading_text,
                    'section': current_section,
                    'heading': heading_text,
                    'level': hlevel
                })
                continue
            
            # --- Blank line = paragraph boundary ---
            if not stripped:
                if current_para:
                    flush_para()
                continue
            
            current_para.append(line)
        
        # Flush remaining
        if current_para:
            flush_para()
        if in_table:
            flush_table()

        # --- PASS 2: Size-split large blocks, build ChunkResult list ---
        results: List[ChunkResult] = []
        
        for block in blocks:
            content = block['content'].strip()
            btype = block['type']
            section = block['section']
            heading = block['heading']
            level = block['level']
            
            if not content or len(content) < self.min_chunk_size:
                # Merge tiny heading-only blocks with context heading
                if btype == 'heading' and content:
                    # Still store for keyword extraction context
                    pass
                else:
                    continue
            
            # Tables are atomic — never split
            if btype == 'table':
                kw = _extract_keywords(content)
                results.append(ChunkResult(
                    content=content,
                    chunk_type='table',
                    section=section,
                    heading=heading,
                    hierarchy_level=level,
                    keywords=kw
                ))
                continue
            
            # Headings — kept only if they have enough text to be useful standalone
            if btype == 'heading':
                if len(content) >= 10:
                    results.append(ChunkResult(
                        content=content,
                        chunk_type='heading',
                        section=section,
                        heading=heading,
                        hierarchy_level=max(1, level - 1),
                        keywords=_extract_keywords(content, max_words=5)
                    ))
                continue
            
            # Large paragraphs / lists — split with sentence boundary overlap
            if len(content) > self.chunk_size:
                sub_chunks = _split_paragraph(content, self.chunk_size, self.chunk_overlap)
                for sub in sub_chunks:
                    if len(sub.strip()) >= self.min_chunk_size:
                        kw = _extract_keywords(sub)
                        results.append(ChunkResult(
                            content=sub.strip(),
                            chunk_type=btype,
                            section=section,
                            heading=heading,
                            hierarchy_level=level,
                            keywords=kw
                        ))
            else:
                kw = _extract_keywords(content)
                results.append(ChunkResult(
                    content=content,
                    chunk_type=btype,
                    section=section,
                    heading=heading,
                    hierarchy_level=level,
                    keywords=kw
                ))
        
        return results

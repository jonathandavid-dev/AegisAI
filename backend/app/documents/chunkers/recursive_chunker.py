from typing import List

class RecursiveChunker:
    """
    Custom recursive text chunker. Splits documents by recursive delimiters:
    paragraphs, lines, words, and characters, staying under a target size
    while preserving a defined overlap between adjacent chunks.
    """
    
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        # Delimiters in priority order
        self.separators = ["\n\n", "\n", " ", ""]

    def split_text(self, text: str) -> List[str]:
        """
        Recursively splits text into character chunks.
        Honors word boundaries and paragraph delimiters where practical.
        """
        if not text:
            return []
            
        def _split(text_segment: str, separator_idx: int) -> List[str]:
            # Base case: text segment is already small enough
            if len(text_segment) <= self.chunk_size:
                return [text_segment]
                
            # If we run out of separators, perform hard character chunking
            if separator_idx >= len(self.separators):
                return [
                    text_segment[i:i + self.chunk_size] 
                    for i in range(0, len(text_segment), self.chunk_size)
                ]
                
            separator = self.separators[separator_idx]
            
            # Split segment by current separator
            splits = text_segment.split(separator) if separator else list(text_segment)
            
            merged_splits = []
            current_group = []
            current_len = 0
            
            for part in splits:
                # Add separator character back to preserve text spacing structure
                part_to_add = part + separator if separator else part
                
                if len(part_to_add) > self.chunk_size:
                    # Flush existing group before dividing larger segment
                    if current_group:
                        merged_splits.append("".join(current_group))
                        current_group = []
                        current_len = 0
                    # Recurse on larger chunk segment using next level separator
                    recursive_parts = _split(part, separator_idx + 1)
                    merged_splits.extend(recursive_parts)
                else:
                    if current_len + len(part_to_add) > self.chunk_size:
                        merged_splits.append("".join(current_group))
                        current_group = [part_to_add]
                        current_len = len(part_to_add)
                    else:
                        current_group.append(part_to_add)
                        current_len += len(part_to_add)
                        
            if current_group:
                merged_splits.append("".join(current_group))
                
            return merged_splits

        # 1. Break down document into basic chunks
        base_segments = _split(text, 0)
        
        # 2. Merge segments with sliding window to create overlapping chunks
        chunks: List[str] = []
        current_chunk_parts: List[str] = []
        current_chunk_len = 0
        
        for segment in base_segments:
            if current_chunk_len + len(segment) <= self.chunk_size:
                current_chunk_parts.append(segment)
                current_chunk_len += len(segment)
            else:
                if current_chunk_parts:
                    chunks.append("".join(current_chunk_parts))
                    
                # To maintain overlap, trace backward and carry over parts that fit under chunk_overlap
                overlap_parts = []
                overlap_len = 0
                for part in reversed(current_chunk_parts):
                    if overlap_len + len(part) <= self.chunk_overlap:
                        overlap_parts.insert(0, part)
                        overlap_len += len(part)
                    else:
                        break
                        
                current_chunk_parts = overlap_parts + [segment]
                current_chunk_len = sum(len(p) for p in current_chunk_parts)
                
        if current_chunk_parts:
            chunks.append("".join(current_chunk_parts))
            
        return [c.strip() for c in chunks if c.strip()]

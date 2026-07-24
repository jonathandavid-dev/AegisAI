import re

class HallucinationDetector:
    """
    Analyzes generated answers against retrieved context chunks to detect hallucinated claims, entities, or numbers.
    """
    @staticmethod
    def detect_hallucinations(answer: str, context_chunks: list[str]) -> dict:
        """
        Inspects generated response for fabricated numbers, entities, and unsupported claims.
        """
        if not answer:
            return {"hallucinated": False, "score": 0.0, "details": "Empty answer"}

        full_context = " ".join(context_chunks).lower()
        sentences = [s.strip() for s in re.split(r'[.!?]', answer) if s.strip()]
        
        fabricated_numbers = []
        fabricated_entities = []
        unsupported_sentences = []
        
        stopwords = {
            "the", "a", "an", "and", "or", "but", "if", "then", "else", "when", "where", "why", "how", "to", "of", "in", "on", "at", "by", 
            "for", "with", "about", "against", "between", "into", "through", "during", "before", "after", "above", "below", "from", "up", 
            "down", "out", "off", "over", "under", "again", "further", "once", "here", "there", "all", "any", "both", "each", "few", "more", 
            "most", "other", "some", "such", "no", "nor", "not", "only", "own", "same", "so", "than", "too", "very", "can", "will", "just", 
            "should", "now", "is", "was", "were", "are", "be", "been", "have", "has", "had", "do", "does", "did", "this", "that"
        }

        for sentence in sentences:
            # Strip citation brackets so they aren't parsed as numbers or entity boundary artifacts
            clean_sentence = re.sub(r'\[\d+\]', '', sentence)
            sentence_lower = clean_sentence.lower()
            
            # 1. Check Fabricated Numbers
            numbers = re.findall(r'\b\d+(?:\.\d+)?\b', clean_sentence)
            for num in numbers:
                if num not in full_context:
                    fabricated_numbers.append(num)
            
            # 2. Check Fabricated Entities (Proper Capitalized Nouns)
            words = re.findall(r'\b[A-Z][a-zA-Z]*\b', clean_sentence)
            for word in words:
                word_lower = word.lower()
                if word_lower in stopwords:
                    continue
                if word_lower not in full_context:
                    # Ignore the first word capitalization if it's the only occurrence in sentence
                    if clean_sentence.strip().startswith(word) and clean_sentence.count(word) == 1:
                        continue
                    fabricated_entities.append(word)

            # 3. Check Groundedness (Unsupported Claims)
            words_in_sent = [w.lower() for w in re.findall(r'\b\w+\b', sentence_lower)]
            filtered_words = [w for w in words_in_sent if w not in stopwords and not w.isdigit()]
            
            if filtered_words:
                matched_count = sum(1 for w in filtered_words if w in full_context)
                overlap_ratio = matched_count / len(filtered_words)
                # If less than 35% of keywords overlap with the source context, flag it
                if overlap_ratio < 0.35:
                    unsupported_sentences.append(sentence)

        total_issues = len(fabricated_numbers) + len(fabricated_entities) + len(unsupported_sentences)
        max_sentences = max(len(sentences), 1)
        score = min(total_issues / (max_sentences * 1.5), 1.0)
        
        return {
            "hallucinated": score > 0.30,
            "score": round(score, 2),
            "fabricated_numbers": list(set(fabricated_numbers)),
            "fabricated_entities": list(set(fabricated_entities)),
            "unsupported_sentences": unsupported_sentences,
            "details": f"Hallucination Score: {score}. Fabricated Numbers: {len(fabricated_numbers)}. Fabricated Entities: {len(fabricated_entities)}. Unsupported Claims: {len(unsupported_sentences)}."
        }

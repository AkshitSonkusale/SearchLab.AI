import re
from typing import List

def split_into_sentences(text: str) -> List[str]:
    """
    Splits text into sentences while avoiding splits inside:
    - Decimals like '1.5'
    - Times like '9:30'
    - Abbreviations like 'e.g.', 'i.e.', 'Dr.'
    """
    # Protect common periods in numbers, times, and abbreviations
    protected = text
    # Replace decimal numbers dot with special token
    protected = re.sub(r'(\d+)\.(\d+)', r'\1__DOT__\2', protected)
    # Replace time colon with special token
    protected = re.sub(r'(\d+):(\d+)', r'\1__COLON__\2', protected)
    # Abbreviations
    protected = re.sub(r'\b(e\.g\.|i\.e\.|vs\.|Mr\.|Mrs\.|Ms\.|Dr\.)', lambda m: m.group(0).replace('.', '__DOT__'), protected, flags=re.IGNORECASE)

    # Split on sentence terminals followed by whitespace
    raw_sentences = re.split(r'(?<=[.!?])\s+', protected)
    sentences = []
    for s in raw_sentences:
        clean = s.replace('__DOT__', '.').replace('__COLON__', ':').strip()
        if clean:
            sentences.append(clean)
    return sentences

def chunk_text(text: str, target_words: int = 200, overlap_sentences: int = 2) -> List[str]:
    """
    Chunks text into roughly 150-300 word segments, cutting strictly at sentence boundaries
    and overlapping consecutive chunks by 1-2 sentences.
    """
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    all_sentences = []
    for p in paragraphs:
        sents = split_into_sentences(p)
        all_sentences.extend(sents)

    if not all_sentences:
        return []

    chunks = []
    current_sentences = []
    current_word_count = 0

    for sent in all_sentences:
        sent_words = len(sent.split())
        current_sentences.append(sent)
        current_word_count += sent_words

        if current_word_count >= target_words:
            chunk_text = " ".join(current_sentences)
            chunks.append(chunk_text)
            
            # Keep overlap sentences for next chunk
            overlap = current_sentences[-overlap_sentences:] if len(current_sentences) > overlap_sentences else current_sentences
            current_sentences = list(overlap)
            current_word_count = sum(len(s.split()) for s in current_sentences)

    if current_sentences:
        remaining_text = " ".join(current_sentences)
        if chunks and len(remaining_text.split()) < 30:
            # Append short leftover to the last chunk
            chunks[-1] = chunks[-1] + " " + remaining_text
        else:
            chunks.append(remaining_text)

    return chunks

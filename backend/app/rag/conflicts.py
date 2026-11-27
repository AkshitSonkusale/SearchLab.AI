import re
from typing import List, Dict, Any
from app.db import execute_query

def extract_numbers(text: str) -> set:
    """
    Finds all numbers and numeric expressions in text.
    """
    return set(re.findall(r'\b\d+(?:\.\d+)?\b', text))

def tokenize(text: str) -> set:
    """
    Lowercase word tokens excluding standard stop words.
    """
    words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
    stopwords = {"the", "and", "for", "with", "that", "this", "from", "are", "you", "should", "will", "can", "must"}
    return set(w for w in words if w not in stopwords)

def detect_conflicts(sources: List[Dict[str, Any]], question: str) -> List[Dict[str, Any]]:
    """
    Detects contradictory information between distinct source documents:
    - Evidence sentences share at least 30% word tokens
    - Contain different numeric numbers/quantities
    - Persists detected conflict into the conflicts table for coverage tracking
    """
    conflicts = []
    num_sources = len(sources)
    if num_sources < 2:
        return conflicts

    for i in range(num_sources):
        for j in range(i + 1, num_sources):
            src_a = sources[i]
            src_b = sources[j]

            # Only check across different documents
            if src_a.get("document_id") == src_b.get("document_id"):
                continue

            text_a = src_a.get("evidence_sentence") or src_a.get("text", "")
            text_b = src_b.get("evidence_sentence") or src_b.get("text", "")

            tokens_a = tokenize(text_a)
            tokens_b = tokenize(text_b)
            if not tokens_a or not tokens_b:
                continue

            overlap = len(tokens_a & tokens_b) / min(len(tokens_a), len(tokens_b))
            nums_a = extract_numbers(text_a)
            nums_b = extract_numbers(text_b)

            # High semantic context overlap with divergent numbers indicates a policy conflict
            if overlap >= 0.30 and nums_a and nums_b and nums_a != nums_b:
                conflict_entry = {
                    "doc_a": src_a.get("document_name", "Document A"),
                    "doc_b": src_b.get("document_name", "Document B"),
                    "text_a": text_a[:200],
                    "text_b": text_b[:200],
                    "example_question": question
                }
                conflicts.append(conflict_entry)

                # Save or update conflict in database
                try:
                    execute_query(
                        """
                        INSERT INTO conflicts (doc_a, doc_b, text_a, text_b, example_question, count, last_seen_at)
                        VALUES (%s, %s, %s, %s, %s, 1, now())
                        """,
                        (conflict_entry["doc_a"], conflict_entry["doc_b"], conflict_entry["text_a"], conflict_entry["text_b"], question)
                    )
                except Exception:
                    pass

    return conflicts

from __future__ import annotations

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from the_evaluator.engine.types import (
    DiagnosticLocation,
    ReportDescriptor,
    RuleCategory,
    RuleContext,
    RuleMeta,
    Severity,
)

SIMILARITY_THRESHOLD = 0.85

_all_skill_texts: dict[str, str] = {}
_duplicates_reported: set[tuple[str, str]] = set()


def reset_duplicate_state() -> None:
    _all_skill_texts.clear()
    _duplicates_reported.clear()


def _tfidf_similarity(text_a: str, text_b: str) -> float:
    """Compute cosine similarity between two texts using TF-IDF vectors.

    TF-IDF naturally downweights common words (import, def, return, the)
    and upweights distinctive terms, avoiding the false-positive inflation
    that word-level Jaccard produces on skills sharing boilerplate.
    """
    if not text_a.strip() or not text_b.strip():
        return 0.0
    vectorizer = TfidfVectorizer()
    try:
        tfidf_matrix = vectorizer.fit_transform([text_a, text_b])
    except ValueError:
        return 0.0
    sim = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])
    return float(sim[0][0])


class DuplicateDetection:
    meta: RuleMeta = RuleMeta(
        id="content/duplicate-detection",
        default_severity=Severity.WARNING,
        fixable=False,
        description="Detect near-duplicate skills",
        category=RuleCategory.CONTENT,
        messages={
            "duplicate": "{{similarity}}% similar to '{{other}}' — consider merging",
        },
    )

    def create(self, context: RuleContext) -> None:
        skill = context.skill
        if not skill.body:
            return

        skill_key = skill.dir_name
        _all_skill_texts[skill_key] = skill.body

        for other_name, other_text in _all_skill_texts.items():
            if other_name == skill_key:
                continue

            pair = tuple(sorted([skill_key, other_name]))
            if pair in _duplicates_reported:
                continue

            similarity = _tfidf_similarity(skill.body, other_text)
            if similarity >= SIMILARITY_THRESHOLD:
                _duplicates_reported.add(pair)
                context.report(
                    ReportDescriptor(
                        message_id="duplicate",
                        data={
                            "similarity": str(int(similarity * 100)),
                            "other": other_name,
                        },
                        location=DiagnosticLocation(
                            file=skill.skill_md_path,
                            start_line=1,
                        ),
                    )
                )

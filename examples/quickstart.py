"""Offline quickstart — runs with no API key and is fully deterministic.

To use a real model, swap the provider for a spec string, e.g.
``Judge(provider="openai:gpt-5", rubric="factuality")``.
"""

from llmjudge import Judge, MockProvider

# MockProvider(fixed_score=...) keeps this example deterministic and offline.
judge = Judge(provider=MockProvider(fixed_score=0.9), rubric="factuality")

result = judge.score(
    prompt="What is the capital of France?",
    response="The capital of France is Paris.",
)

assert result > 0.8  # a JudgeResult compares like its float score
print(f"score={result.score}  confidence={result.confidence}")
print(f"passed={result.passed()}  reason={result.reason!r}")

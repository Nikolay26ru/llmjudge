"""Extend LLMJudge Kit with your own rubric — no changes to the core required."""

from llm_judge_kit import Judge, MockProvider, Rubric, register_rubric

# Define and register a domain-specific rubric.
conciseness = Rubric(
    name="conciseness",
    description="Whether the response is as short as possible while complete.",
    criteria=("No filler or repetition.", "Every sentence earns its place."),
)
register_rubric(conciseness)

# Now it is selectable by name, exactly like the built-ins.
judge = Judge(provider=MockProvider(fixed_score=0.7), rubric="conciseness")
result = judge.score("Summarize in one line.", "It is good.")

print(f"rubric={result.rubric}  score={result.score}  passed={result.passed()}")

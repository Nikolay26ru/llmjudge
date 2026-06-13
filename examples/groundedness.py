"""Grounded evaluation: score a response only against supplied context.

The ``groundedness`` rubric requires ``context=`` — omitting it raises a
ConfigurationError instead of silently judging against the model's own
knowledge.
"""

from llmjudge import Judge, MockProvider

judge = Judge(provider=MockProvider(fixed_score=0.95), rubric="groundedness")

context = "The Eiffel Tower was completed in 1889 and stands 330 metres tall."
result = judge.score(
    prompt="How tall is the Eiffel Tower?",
    response="It is 330 metres tall.",
    context=context,
)

print(f"grounded score={result.score}  confidence={result.confidence}")

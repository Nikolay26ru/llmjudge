"""Judge the output of a plain pipeline — no framework, no adapter.

LLMJudge Kit judges *strings*, so whatever your code produces, you pass it to a
`Judge`. Runs offline with `MockProvider`; swap in a real provider
(e.g. `Judge(provider="openai:gpt-5", ...)`) for real verdicts.
"""

from llm_judge_kit import Judge, MockProvider


def my_pipeline(question: str) -> str:
    # Your retrieval / generation / agent logic goes here.
    return "The Eiffel Tower is about 330 metres tall."


def main() -> None:
    question = "How tall is the Eiffel Tower?"
    answer = my_pipeline(question)

    judge = Judge(provider=MockProvider(fixed_score=0.82), rubric="groundedness")
    result = judge.score(
        question,
        answer,
        context="The Eiffel Tower stands 330 metres tall including antennas.",
    )
    print(f"score={result.score:.2f} passed={result.passed(0.7)} reason={result.reason!r}")


if __name__ == "__main__":
    main()

"""Judge a DSPy module's prediction with LLMJudge Kit.

A DSPy module returns a Prediction; take the output field (e.g. `pred.answer`)
and hand it to a `Judge`. LLMJudge Kit also works as a DSPy *metric* — return
`float(judge.score(...))` from your metric function to optimize against it.

DSPy needs a configured LM to run, so this uses a stub prediction offline; the
live wiring is in the comment. The judge uses `MockProvider` — swap in a real
provider for a real verdict.

    pip install "llm-judge-kit" dspy-ai
"""

from llm_judge_kit import Judge, MockProvider


def main() -> None:
    question = "What is the capital of France?"

    # Live (needs `dspy.configure(lm=...)`):
    #   import dspy
    #   qa = dspy.Predict("question -> answer")
    #   answer = qa(question=question).answer
    answer = "The capital of France is Paris."  # offline stub for the above

    judge = Judge(provider=MockProvider(fixed_score=0.91), rubric="factuality")
    result = judge.score(question, answer)

    # As a DSPy metric:
    #   def metric(example, pred, trace=None):
    #       return float(judge.score(example.question, pred.answer))
    print(f"score={result.score:.2f} passed={result.passed()} reason={result.reason!r}")


if __name__ == "__main__":
    main()

"""Judge a LangChain chain's output with LLMJudge Kit.

A LangChain chain returns a string (or a message you can stringify), so judging
it needs no adapter: run the chain, hand the text to a `Judge`.

This runs offline. If `langchain-core` is installed it uses a tiny LCEL runnable
(no LLM needed); otherwise it falls back to a stub so the file still runs. The
judge uses `MockProvider` — swap in `Judge(provider="openai:gpt-5", ...)` for a
real verdict.

    pip install "llm-judge-kit" langchain-core
"""

from llm_judge_kit import Judge, MockProvider


def build_chain():
    """Return something with a callable `.invoke`, real or stub."""
    try:
        from langchain_core.runnables import RunnableLambda
    except ImportError:
        print("[langchain-core not installed — using a stub chain so this runs offline]")
        return RunnableLambdaStub()
    # A trivial LCEL runnable stands in for your real chain (prompt | llm | parser).
    return RunnableLambda(lambda q: "Paris is the capital of France.")


class RunnableLambdaStub:
    def invoke(self, _question: str) -> str:
        return "Paris is the capital of France."


def main() -> None:
    question = "What is the capital of France?"
    chain = build_chain()
    answer = str(chain.invoke(question))

    judge = Judge(provider=MockProvider(fixed_score=0.9), rubric="relevance")
    result = judge.score(question, answer)
    print(f"score={result.score:.2f} passed={result.passed()} reason={result.reason!r}")


if __name__ == "__main__":
    main()

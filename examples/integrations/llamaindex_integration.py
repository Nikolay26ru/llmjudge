"""Judge a LlamaIndex query engine's answer with LLMJudge Kit.

A query engine returns a Response; `str(response)` is the answer text, which you
hand to a `Judge` — together with the retrieved context for a groundedness (RAG)
check, the classic hallucination guardrail.

Running a real engine needs an index + an LLM, so this uses a stub answer
offline; the live wiring is in the comment. The judge uses `MockProvider` — swap
in a real provider for a real verdict.

    pip install "llm-judge-kit" llama-index
"""

from llm_judge_kit import Judge, MockProvider

CONTEXT = "The Eiffel Tower stands 330 metres tall including antennas."


def main() -> None:
    question = "How tall is the Eiffel Tower?"

    # Live (needs an index + a configured LLM):
    #   from llama_index.core import VectorStoreIndex, Document
    #   index = VectorStoreIndex.from_documents([Document(text=CONTEXT)])
    #   answer = str(index.as_query_engine().query(question))
    answer = "It is 330 metres tall."  # offline stub standing in for the above

    judge = Judge(provider=MockProvider(fixed_score=0.88), rubric="groundedness")
    result = judge.score(question, answer, context=CONTEXT)
    print(f"score={result.score:.2f} passed={result.passed(0.7)} reason={result.reason!r}")


if __name__ == "__main__":
    main()

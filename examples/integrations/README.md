# Integration examples

LLMJudge Kit judges **strings**, so it drops into any stack with no adapter:
whatever produces your model output — a chain, a query engine, a DSPy module, or
plain code — you pass that text to a `Judge`.

Every example here runs **offline** (deterministic `MockProvider`, plus a stub
when the framework or an LLM isn't available), so `python examples/integrations/<file>.py`
always works and is exercised in CI. For live verdicts, swap the judge for a real
provider (e.g. `Judge(provider="openai:gpt-5", ...)`) and wire in the real
framework call (shown inline in each file).

| File | Stack | Integration point |
| --- | --- | --- |
| `raw_pipeline.py` | none | judge any function's string output |
| `langchain_integration.py` | LangChain | judge `chain.invoke(...)` output |
| `llamaindex_integration.py` | LlamaIndex | judge `str(query_engine.query(...))` — RAG groundedness |
| `dspy_integration.py` | DSPy | judge `pred.answer`, or use the judge as a DSPy metric |

```bash
python examples/integrations/raw_pipeline.py
# score=0.82 passed=True reason='Deterministic mock verdict.'
```

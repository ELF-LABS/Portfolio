# Chatbot v1 — Constraint-driven baseline RAG on an 8GB GPU

The first production version. Built under hard hardware constraints: a single 8 GB consumer GPU, no cloud, no horizontal scaling. The architecture is the simplest thing that works under that constraint, and the engineering value is in *what gets cut* to fit.

This deployment served a specialized use case with confidentiality constraints. The design pattern is published; domain-specific data, knowledge base content, and deployment details remain proprietary.

## Hardware constraint

| | |
|---|---|
| GPU | Single 8 GB consumer card (RTX 2080 class) |
| LLM target | 8B-class instruction-tuned model |
| RAG backend | Embedded vector store (RAM-mode ChromaDB), single-process |
| Frontend | Flask + Flask-SocketIO, single container |
| Total RAM budget | < 16 GB working set |
| Concurrent users target | 1–4 |

The constraint dictates the architecture. There is no room for a cross-encoder reranker, no room for a graph database alongside the vector store, no room for multi-stage post-processing. Every component competes with every other component for VRAM and RAM.

## Architecture

```
                ┌─────────────────────────────────┐
                │   user (browser, WebSocket)     │
                └──────────────┬──────────────────┘
                               │
                ┌──────────────▼──────────────────┐
                │   Flask + SocketIO chat handler │
                └──────────────┬──────────────────┘
                               │
                ┌──────────────▼──────────────────┐
                │   Single-pass RAG pipeline      │
                │   1. embed query                │
                │   2. vector retrieve top-k      │
                │   3. build prompt + history     │
                │   4. LLM generate               │
                │   5. minimal post-process       │
                └──────┬──────────────┬───────────┘
                       │              │
                       │              │
        ┌──────────────▼─┐   ┌────────▼─────────────────┐
        │  ChromaDB      │   │  llama.cpp / equivalent  │
        │  (RAM mode)    │   │  serving 8B model        │
        │  embeddings:   │   │  4-bit quantization      │
        │  sentence-     │   │  ~5 GB VRAM              │
        │  transformers  │   │                          │
        │  ~2 GB RAM     │   │                          │
        └────────────────┘   └──────────────────────────┘
```

## Components

### Embedding + retrieval

- **Embeddings**: `sentence-transformers/all-MiniLM-L6-v2` (384-dim, ~80 MB on disk, fast on CPU).
- **Vector store**: ChromaDB in RAM mode — no persistent server, loaded into the chatbot process at boot. Trade-off: faster cold start and zero IPC, but the corpus has to fit in RAM and rebuilds on container restart.
- **Retrieval**: cosine similarity, top-k = 5–10 chunks. No reranking. No hybrid search.
- **Chunking**: recursive text splitter, ~500-token chunks with 50-token overlap. PDF source documents pre-extracted to text and chunked offline.

### LLM serving

- **Model**: 8B-class instruction-tuned (Llama 3.1 8B Instruct family or equivalent).
- **Serving**: `llama.cpp` with 4-bit quantization (Q4_K_M or Q5_K_M GGUF), or equivalent low-VRAM serving runtime. Choice driven by VRAM ceiling, not preference.
- **Context**: 4K tokens active window, conservative because each request competes with embedding model for shared system RAM.

### Chat handler + state

- **Frontend**: Flask + Flask-SocketIO. WebSocket for live token streaming back to the browser.
- **Conversation history**: 2–4 turns, truncated aggressively. The 8 GB ceiling makes anything more impossible without evicting other working state.
- **Sessions**: in-memory dict keyed by socket ID. Lost on restart. Acceptable for v1 because the use case was assistive single-session interaction, not multi-session continuity.

### Post-processing (minimal)

- Source-citation cleanup (regex pass to canonicalize `[1]` / `[Source: X]` markers).
- Confidentiality-term filter (regex pass over a configurable list of terms — implementation pattern shown below; the actual term list is per-deployment).
- That is the entire post-process chain. No hallucination check, no image injection, no flowchart resolution. Those came in v2.

## Single-pass RAG glue: query → retrieve → build → generate → filter

The pattern that ties it together. Real implementations swap the model name, embedding model, chunk path, and term list — the *shape* is the same.

```python
# pipeline_v1.py — genericized reference
from sentence_transformers import SentenceTransformer
import chromadb
import requests

EMBED_MODEL = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
CHROMA = chromadb.Client()
COLLECTION = CHROMA.get_or_create_collection("docs")

LLM_URL = "http://localhost:8080/completion"  # llama.cpp-compatible
SYSTEM_PROMPT = "You are a helpful assistant for <generic domain>."

def retrieve(query: str, k: int = 5) -> list[str]:
    qv = EMBED_MODEL.encode(query).tolist()
    hits = COLLECTION.query(query_embeddings=[qv], n_results=k)
    return hits["documents"][0]

def build_prompt(query: str, ctx: list[str], history: list[dict]) -> str:
    ctx_block = "\n".join(ctx)
    hist_block = "\n".join(f"{m['role']}: {m['content']}" for m in history[-2:])
    return f"{SYSTEM_PROMPT}\n\nContext:\n{ctx_block}\n\n{hist_block}\nuser: {query}\nassistant:"

def generate(prompt: str, max_tokens: int = 512) -> str:
    r = requests.post(LLM_URL, json={
        "prompt": prompt,
        "n_predict": max_tokens,
        "temperature": 0.2,
        "stop": ["user:", "\nuser"],
    }, timeout=60)
    return r.json().get("content", "")

def confidentiality_filter(text: str, banned_terms: list[str]) -> str:
    """Replace per-deployment confidentiality terms with neutral substitutes.
    Real implementations pass a configurable list at init time.
    """
    for term in banned_terms:
        text = text.replace(term, "[REDACTED]")
    return text

def answer(query: str, history: list[dict], banned_terms: list[str]) -> str:
    ctx = retrieve(query, k=5)
    prompt = build_prompt(query, ctx, history)
    raw = generate(prompt)
    return confidentiality_filter(raw, banned_terms)
```

The filter is parameterized at init time, so the same architecture serves different deployments with different term lists.

## Open-source dependencies

| Component | License | Used for |
|---|---|---|
| [llama.cpp](https://github.com/ggerganov/llama.cpp) | MIT | LLM serving, GGUF quantized inference |
| [ChromaDB](https://github.com/chroma-core/chroma) | Apache-2.0 | In-memory vector store |
| [sentence-transformers](https://github.com/UKPLab/sentence-transformers) | Apache-2.0 | Query and chunk embeddings |
| [Flask](https://github.com/pallets/flask) + [Flask-SocketIO](https://github.com/miguelgrinberg/Flask-SocketIO) | BSD-3 / MIT | HTTP + WebSocket frontend |
| [Llama 3.1 8B Instruct](https://huggingface.co/meta-llama/Llama-3.1-8B-Instruct) | Llama 3.1 Community License | Base LLM (or equivalent 8B instruct model) |

The glue code in this writeup is Apache-2.0 (matches the repo). The dependencies retain their own licenses.

## Design decisions and their tradeoffs

- **Constraint-first design.** Building against the 8 GB ceiling forced architectural choices that shipped faster than an aspirational design would have. The cost is functionality limits the next section enumerates.
- **Confidentiality-filter as a separable pass.** Externalized list, same code; the architecture moves between deployments without source changes.
- **RAM-mode ChromaDB.** No IPC overhead, no second service. Tradeoff: corpus size capped by RAM; rebuild on container restart.
- **2–4 turn history.** Honest truncation against the working-memory ceiling. Tradeoff: longer multi-turn coherence is impossible without evicting other state.

## Limitations (v2 addresses each)

- **Single retrieval pass, no reranking.** Routinely surfaced topically-related-but-wrong chunks. v2 adds cross-encoder rerank, which cuts the failure mode dramatically.
- **No hallucination check.** The LLM occasionally extended confidently beyond the retrieved context. v2 adds a post-generation hallucination filter comparing claim spans against the retrieved chunks.
- **No specialized gating.** v1 treated every query the same. v2 routes named-entity queries through a focused retrieval path before general retrieval, with intent-conditional bypass.
- **No structured citation resolution.** Citations came back as `[1]` / `[2]`; resolution to source URLs happened client-side. v2 resolves server-side and injects canonical references.
- **No graph context.** v1 had no entity-relationship layer. v2 adds a graph database alongside the vector store for cross-chunk relationship queries.

## Operating notes

- **VRAM bookkeeping is the whole game.** Every model loaded into the same process was sized against the 8 GB ceiling. Adding a cross-encoder reranker would have evicted the LLM. The architectural ceiling on what v1 could do was set by the GPU, not by ambition.
- **Single-tenant by design.** v1 assumed one user at a time. Multi-tenant traffic on this stack hits the LLM serving queue first and degrades gracefully but slowly.
- **Cold start matters.** Loading sentence-transformers + ChromaDB into RAM at boot took ~15 seconds. Model load took longer. Containers stayed warm; reboots were planned.

## License

Apache-2.0 (inherits from repository root). Reference code in this document may be reused under the same license.

## See also

- `../chatbot_v2/` — v2 architecture (production-grade hardware, hybrid retrieval, cross-encoder rerank, silo gating, full post-processing chain)
- `../gate/` — multi-component gate pattern from the self-improvement loop (different system, same compositional-validation principle)

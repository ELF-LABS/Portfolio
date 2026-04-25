# Chatbot v2 — Production RAG with hybrid retrieval, focused-retrieval gating, and post-processing chain

The current production version. Same deployment as v1, redesigned around production-grade hardware (a 119 GB unified-memory inference host) with a substantially deeper pipeline. The engineering shape changes when the VRAM ceiling stops being the binding constraint: instead of *what gets cut*, the question becomes *what additional verification layers are load-bearing*.

The data, knowledge base content, and deployment details remain proprietary. The architecture pattern is published.

## Headline result

**98.5 % answer accuracy on a frozen held-out evaluation set** (automated test harness against ground-truth Q/A pairs). The metric is end-to-end — retrieve + generate + post-process, not retrieval-only. Live-traffic accuracy is not claimed; this number tracks a calibration target on a fixed test set, not a guarantee on in-the-wild distribution.

## What changed from v1

| Dimension | v1 | v2 |
|---|---|---|
| LLM | 8B class, 4-bit, ~5 GB VRAM | 35B-class MoE, 4-bit (~3B active), high-VRAM-budget |
| Serving runtime | `llama.cpp` | [SGLang](https://github.com/sgl-project/sglang) (OpenAI-compatible) with model-aware caching |
| Vector store | ChromaDB in-process, RAM mode | [Milvus](https://milvus.io/) standalone server + [FalkorDB](https://github.com/FalkorDB/FalkorDB) graph DB alongside |
| Retrieval | Vector top-k only | **Hybrid BM25 + vector with RRF fusion**, then cross-encoder rerank |
| Reranking | None | [`cross-encoder/ms-marco-MiniLM-L-6-v2`](https://huggingface.co/cross-encoder/ms-marco-MiniLM-L-6-v2) with confidence threshold |
| Conversation history | 2–4 turns | 20 turns, with relaxed entry-truncation |
| Specialized gating | None | **Focused-retrieval gate** routes named-entity queries through a dedicated retrieval path |
| Post-processing | Confidentiality filter + citation cleanup | Five-stage chain: citations → reference resolution → image injection → hallucination check → confidentiality filter |
| Tracing | None | [Phoenix](https://github.com/Arize-ai/phoenix) spans on embedding / retriever / LLM / chain |

## Architecture

```
                  ┌────────────────────────────────────────┐
                  │   user (browser, WebSocket)            │
                  └──────────────────┬─────────────────────┘
                                     │
                  ┌──────────────────▼─────────────────────┐
                  │   Flask + SocketIO chat handler        │
                  │   - 20-turn history                    │
                  │   - context_compressor (long sessions) │
                  └──────────────────┬─────────────────────┘
                                     │
                  ┌──────────────────▼─────────────────────┐
                  │   Intent classifier + focused-          │
                  │     retrieval gate                      │
                  │   if named-entity match AND not         │
                  │     intent==purchase → focused path     │
                  │   else → general path                   │
                  └────────┬───────────────────┬───────────┘
                           │                   │
              ┌────────────▼──┐         ┌──────▼──────────┐
              │ Focused path  │         │  General path   │
              │ (entity-      │         │  (broad         │
              │  scoped       │         │   retrieval)    │
              │  retrieval)   │         │                 │
              └────────┬──────┘         └──────┬──────────┘
                       │                       │
                       ▼                       ▼
            ┌──────────────────────────────────────────┐
            │   Hybrid retrieval                       │
            │   1. BM25 over content field             │
            │   2. dense vector over embedding field   │
            │   3. RRF fusion → top-N                  │
            │   4. cross-encoder rerank → top-5        │
            │   5. confidence threshold filter         │
            └──────────────────┬───────────────────────┘
                               │
                  ┌────────────▼──────────────┐
                  │  Prompt build             │
                  │  - 5K-char context block  │
                  │  - 20-turn history        │
                  │  - intent-conditional     │
                  │    inference steering     │
                  └────────────┬──────────────┘
                               │
                  ┌────────────▼──────────────┐
                  │  LLM (35B-class MoE)      │
                  │  via SGLang :30002        │
                  │  max_tokens 1024 (256     │
                  │  for silo intents)        │
                  └────────────┬──────────────┘
                               │
                  ┌────────────▼──────────────┐
                  │  Post-processing chain    │
                  │  1. clean_source_citations│
                  │  2. resolve_ref_citations │
                  │  3. inject_images         │
                  │  4. hallucination_check   │
                  │  5. brand_scrubber        │
                  └────────────┬──────────────┘
                               │
                  ┌────────────▼──────────────┐
                  │  WebSocket stream → user  │
                  └───────────────────────────┘
```

## Components

### Hybrid retrieval

- **BM25**: lexical keyword match over the canonical `content` field of each chunk in the graph DB. Strong on exact-token queries and identifier lookups.
- **Vector**: dense retrieval over 768-dim BGE-base-en-v1.5 embeddings (or 2048-dim domain embedding for richer corpora). Strong on paraphrased queries.
- **RRF fusion**: reciprocal rank fusion combines the two ranked lists. Insensitive to absolute score scales, robust to one method dominating.
- **Top-N before rerank**: 20–30 candidates pass to the cross-encoder.

### Cross-encoder reranking

- **Model**: `ms-marco-MiniLM-L-6-v2` (small, fast, well-calibrated for relevance scoring).
- **Threshold**: configurable logit cutoff (production default `-5.0`). Anything below is dropped before generation.
- **Outcome**: top-5 chunks survive into the prompt. The threshold prevents marginally-relevant chunks from diluting context.

### Focused-retrieval gate

The most deployment-specific architectural component, expressed generically. The pattern:

```python
# Generic focused-retrieval gate pattern
def focus_gate(query: str, intent: str, entity_match: bool) -> str:
    """Route queries about a specific named entity through a focused retrieval
    path that prefers entity-scoped documentation over general material.

    The bypass for `intent == "purchase"` exists because purchase-intent queries
    benefit from broader retrieval (catalogs, comparisons) even when an entity
    is named. Tune intent list to your deployment.
    """
    if entity_match and intent != "purchase":
        return "focused_path"  # narrow retrieval against entity-scoped collection
    return "general_path"      # full hybrid retrieval against all collections
```

In production this fires on every query mentioning the deployment's named entity. The intent-conditional bypass exists because some intents legitimately need broader context. The shape is general — replace "named entity" with any subject the deployment specializes in.

### Entity-aware retrieval boost

When the query contains a recognized entity identifier from the focused collection, retrieved chunks tagged with that entity receive a `+0.15` score boost in the fusion pass. This is a single-parameter tweak that materially improves entity-specific Q/A accuracy without architectural cost.

### Post-processing chain (five stages, ordered)

```python
# Genericized chain pattern
def post_process(answer: str, retrieved_chunks: list[dict],
                 banned_terms: list[str]) -> str:
    answer = clean_source_citations(answer)        # canonicalize [1], [Source: X] → [n]
    answer = resolve_ref_citations(answer, retrieved_chunks)  # [1] → real URL
    answer = inject_images(answer, retrieved_chunks)          # add inline image refs
    answer = hallucination_check(answer, retrieved_chunks)    # flag claims absent from ctx
    answer = confidentiality_filter(answer, banned_terms)     # per-deployment terms
    return answer
```

The chain order matters. Citation cleanup before resolution; resolution before image injection (images attach to specific cited chunks); hallucination check before confidentiality filter (otherwise flagged claims could leak terms past the filter).

### Hallucination check

For each declarative claim in the answer, attempts to locate a supporting span in the retrieved chunks. Claims without support are either flagged with a `[verify]` marker or stripped, depending on confidence. Implementation is conservative — false positives are preferable to false negatives in a domain where wrong answers cost trust.

### Context compressor

Long conversations exceed the LLM's effective context. `context_compressor.py` summarizes earlier turns into compact representations once history depth crosses a configurable threshold. Recent turns stay verbatim; older turns become summaries. Trade-off documented: precise references in older turns can lose granularity, but generation latency stays bounded.

### Editorial triad pattern (compositional validation)

A separate verification layer (`editorial_triad.py` in production) runs three lightweight LLM passes over the generated answer in different roles (drafter, fact-checker, voice-tightener).

This is the same anti-Goodhart compositional-validation pattern documented in [`../gate/`](../gate/) for the self-improvement loop. The principle: a single judge of any kind shares blind spots with the system it judges. Three judges with different roles fail in different ways, and the disagreements between them are a load-bearing signal that any single judge would miss. The triad here applies the principle to inference-time output validation; the multi-component gate applies it to training-pair validation. Same structural commitment, different surface.

## Service topology

| Service | Port | Image / Process |
|---|---|---|
| Chatbot (Flask + SocketIO) | 5000 | Custom container, `app.py` entry |
| LLM serving | 30002 | SGLang container, OpenAI-compatible API |
| Vector DB (Milvus) | 19530 | Milvus standalone container |
| Graph DB (FalkorDB) | 6379 (loopback) | FalkorDB container, BM25 index on `content` |
| Embedding service | 30010 | FastAPI wrapper around the embedding model |

Inter-service traffic is over Docker network; the chatbot container reaches LLM via `http://llm_server:30002/v1` and graph DB via `falkordb:6379`. Tracing spans are emitted to Phoenix and visualized off-cluster.

## Glue code excerpt — the load-bearing fusion

```python
# Generic hybrid+rerank glue pattern
def hybrid_retrieve(query: str, model_id: str | None = None,
                    top_n_pre_rerank: int = 25, top_k_post_rerank: int = 5) -> list[dict]:
    qv = embed(query)
    bm25_hits  = graph_db.bm25_search(query, k=top_n_pre_rerank)
    vector_hits = vector_db.search(qv, k=top_n_pre_rerank)
    fused = rrf_fuse(bm25_hits, vector_hits, k_constant=60)

    # Model-aware boost
    if model_id:
        for h in fused:
            if h.get("model_tag") == model_id:
                h["score"] += 0.15

    # Cross-encoder rerank
    pairs = [(query, h["content"]) for h in fused]
    rerank_scores = cross_encoder.predict(pairs)
    for h, s in zip(fused, rerank_scores):
        h["rerank_score"] = float(s)

    # Threshold + top-k
    surviving = [h for h in fused if h["rerank_score"] >= RERANK_THRESHOLD]
    surviving.sort(key=lambda h: h["rerank_score"], reverse=True)
    return surviving[:top_k_post_rerank]
```

`rrf_fuse` is the standard reciprocal-rank-fusion implementation; `RERANK_THRESHOLD` is the configurable cutoff that drives the precision/recall trade. Production default is conservative (`-5.0` logit) — high-precision, willing to surface fewer chunks rather than dilute the prompt.

## Open-source dependencies

| Component | License | Used for |
|---|---|---|
| [SGLang](https://github.com/sgl-project/sglang) | Apache-2.0 | LLM serving runtime, OpenAI-compatible API |
| [Milvus](https://github.com/milvus-io/milvus) | Apache-2.0 | Vector database |
| [FalkorDB](https://github.com/FalkorDB/FalkorDB) | Server Side Public License | Graph database with BM25 index |
| [BGE embeddings](https://huggingface.co/BAAI/bge-base-en-v1.5) | MIT | 768-dim dense embeddings (or an alternate-dim embedding model per deployment) |
| [`cross-encoder/ms-marco-MiniLM-L-6-v2`](https://huggingface.co/cross-encoder/ms-marco-MiniLM-L-6-v2) | Apache-2.0 | Reranking |
| [Phoenix](https://github.com/Arize-ai/phoenix) | Elastic License v2 | Observability / tracing |
| [Flask](https://github.com/pallets/flask) + [Flask-SocketIO](https://github.com/miguelgrinberg/Flask-SocketIO) | BSD-3 / MIT | HTTP + WebSocket frontend |
| Qwen3.5-35B-A3B (or comparable MoE) | Apache-2.0 (Qwen) / model-specific | Base LLM |

Glue code in this writeup is Apache-2.0. Each dependency keeps its own license.

## Design decisions and their tradeoffs

- **Hybrid + rerank is load-bearing.** Single-method retrieval misses queries the other method handles. The fusion pass is the highest-leverage architectural change from v1; the rerank stage adds latency in exchange for precision.
- **The post-processing chain is order-sensitive.** Each stage assumes the previous stage's output shape. Reordering breaks subtle invariants. The pipeline is documented stage-by-stage and the order is a tested invariant.
- **Focused-retrieval gating is intent-conditional.** Naively routing every entity-mention to a focused collection would degrade purchase-intent queries that need catalog breadth. The intent bypass costs a single line and recovers accuracy on a meaningful chunk of traffic.
- **Tracing from day one.** Phoenix spans across embedding / retriever / LLM / chain mean accuracy regressions are locatable in minutes, not days. Tradeoff: tracing adds modest overhead and an additional service dependency.

## Limitations (reviewer-honest)

- **The 98.5 % accuracy figure is on a frozen held-out evaluation set, not in-the-wild traffic.** Live traffic distribution drifts; the metric tracks a calibration target, not an in-the-wild guarantee.
- **The cross-encoder threshold is a global constant.** It should be intent-conditional or calibrated per focused-retrieval collection. Future work: per-intent calibration on the held-out eval set.
- **The hallucination check is conservative.** It catches confident extensions beyond context but not subtle paraphrase drift — those slip past and would need a stronger NLI-style entailment check.
- **The focused-retrieval gate is a single boolean per query.** Real deployments have nested collections and multi-entity queries that do not map cleanly. The current gate is a v2 instance of an obvious generalization.
- **The 35B MoE base model is a fixed-capability ceiling.** No custom adapters in this deployment yet — the system relies entirely on retrieval to compensate. The compositional-architecture work in `../gate/` and `../self_improve/` is the path to letting smaller, adapter-trained models close the gap.

## Operating notes

- **Service topology is the operational surface.** The chatbot is the user-facing process, but five other services need to be healthy for any answer to land. A health-check endpoint that probes all five (and the embedding service in particular, which is the silent failure mode) lives at `/health/full`.
- **Re-embedding the corpus is the long pole.** Schema changes to chunk metadata mean re-embedding everything; a 100K-chunk corpus re-embed takes hours. Done overnight.
- **The confidentiality filter is configuration, not code.** Term lists evolve as deployments evolve; externalizing to a config file (rather than hard-coding a constant in source) was an early lesson.

## License

Apache-2.0 (inherits from repository root). Reference code in this document may be reused under the same license.

## See also

- `../chatbot_v1/` — the v1 baseline (single 8 GB GPU, ChromaDB, single-pass retrieval)
- `../gate/` — multi-component gate pattern from the self-improvement loop (different system, same compositional-validation principle as the editorial triad here)
- `../../measurements/fellows_sprint_pilot_apr_2026.md` — the Apr 2026 pilot results that motivated the gate work

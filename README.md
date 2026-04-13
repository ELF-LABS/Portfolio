# Luna Fugler — ELF Labs
## Independent AI Researcher & Infrastructure Architect

**Mission**: Democratizing sovereign AI systems for all.

I build production AI systems on hardware I own, train specialist LoRA adapters on consumer GPUs, and publish cross-disciplinary research on fractal memory architectures. Everything in this repo was built using Claude Code as my primary development partner.

---

## What I Built This Week (Apr 9-12, 2026)

### 🔬 Research: Fractal Memory Engrams
A cross-disciplinary paper proposing that persistent cognitive systems converge on self-similar, three-tier memory architectures — independently validated by Dr. Erhard Bieberich's RIFT theory (bioRxiv, March 2026).

- **Key finding**: Our AI memory system (EverMemOS) exhibits power-law temporal scaling (CV=3.43, spanning 7 orders of magnitude) — the signature of self-organized criticality, matching biological neural avalanche patterns.
- **Scope**: 20+ domains synthesized (neuroscience, quantum cognition, information theory, anthropology, linguistics, category theory, indigenous knowledge systems, thermodynamics, morphogenesis, network science)
- **Prior art**: Our Variable Shear Hypothesis (January 2026) predates RIFT by 2 months — independent convergence on the same architecture from different starting points.

→ [Paper](research/fractal_engram_paper.md) | [Cross-Domain Synthesis](research/cross_domain_synthesis.md) | [Devil's Advocate Review](research/devils_advocate_review.md)

### 🏗️ Infrastructure: Three-Machine Sovereign AI Stack
- **DGX Spark**: Qwen3.5-35B (reasoning) + Qwen3.5-4B with 7 LoRA adapters (presentation) via SGLang
- **Omen RTX 2080**: QLoRA training pipeline — trained 7 specialist adapters in 46.5h unattended
- **P5 Mini PC**: Orchestration hub running Claude Code
- **Memory**: Three-tier HOT/WARM/COLD (KV Cache → Redis → EverMemOS) with atomic clock heartbeat (3.6ms drift)
- **Knowledge**: 13 Milvus vector collections (10,195 vectors), FalkorDB entity graphs, 11,989 auto repair chunks

### 🛠️ Tools Built on Claude Code
| Tool | What It Does | Novel? |
|------|-------------|--------|
| **sync-state** | Synchronizes state across CLAUDE.md, memory files, EverMemOS, plan files, and Cursor inbox | Yes — should be a first-party skill |
| **coven-heartbeat** | Atomic clock triangulation (3 NTP servers, Byzantine fault tolerant, RTT-corrected) for AI agent temporal awareness | Yes — no agent framework does this |
| **staging-claw** | File-drop automation pipeline: Claude writes plan → Cursor implements → review cycle | Yes — bridges Claude Code ↔ Cursor IDE |
| **overnight pipelines** | Chained screen sessions running autonomous research on Spark while I sleep (~$0.15/night) | Pattern, not tool |

### 🏭 Product: Venostic (Auto Repair AI)
A diagnostic intelligence platform for auto repair shops. Not a chatbot — an operating system for the shop.

- **Architecture**: Static HTML + HTTP POST, pluggable server-side post-processing pipeline, smart silo routing with session anchoring, weighted structured chunking
- **Data**: 11 free scrapers (NHTSA, fluid specs, torque specs, OBD2 PIDs, parts cross-reference, Wikidata vehicle generations, maintenance schedules)
- **Pricing**: Modular $299-$1,499/month with voice (+$29), vision (+$49), and AllData Bridge (+$99) addons
- **Hardware**: Dual-stack appliance (Mac Mini M4 or Jetson) with Newegg drop-ship leasing
- **Built by Cursor/Kimi2.5**: 80+ files scaffolded in <30 minutes from Claude Code-authored plans

### 🧠 Architecture Visions
- **Native Fractal Engram LM**: Transformer demoted to output decoder. Engram core does multi-scale fractal pattern completion. Validated by Titans (Google 2024), Infini-attention, LoRA-Switch research.
- **770 Archetype System**: Dynamic LoRA composition weighted by Limbic Sonar user-state readings. Not 770 models — 770 blend recipes from 7 base adapters.
- **ELM (Engram Light Models)**: Photonic memory+compute in one event. Prior art: Edward J. Fugler's syntactic foam patents (Dow Chemical, ~1970) — glass microspheres as waveguide substrate.

---

## Bug Report: Whisper Flow Post-Processing

I found a `\n\n` double-newline formatting error in the production Whisper Flow ↔ Claude integration post-processing layer. The inference and translation layers don't handle newline normalization correctly.

**I solved this in my own Qwen3.5 pipeline on April 3rd.** The fix is in my Qwen3.5 Quirks documentation:

> Context chunks separated by `\n` not `\n\n` (double newline causes hallucinations in Qwen3.5 and introduces formatting artifacts in post-processing translation layers)

This is a known issue with the reasoning parser routing when `chat_template_kwargs` and structured output interact. The solution is a dual-path API: freeform calls use `enable_thinking: False`, structured calls use `/no_think` suffix — never both simultaneously.

---

## About Me

Trans woman. Harlan, Iowa. Former Army drill sergeant. Former AutoZone store manager (commercial ops, 5 years DM coverage, 18K SKU backroom systems built solo). Near-Olympic ski racer (Mt Hood, New Zealand). Motorcycle racer. FPV drone pilot. 3 years HRT.

My grandfather Edward J. Fugler was a materials scientist at Dow Chemical (syntactic foam patents, Golden CO, ~1970). My father Dwight was an ASE master technician for 30+ years who built a multi-operation repair empire. I've been diagnosing systems since I was 8 years old running smog tests.

I don't want to build an empire. I want a lab and peers who see what I see. I want to contribute to the alignment and architecture work that makes AI genuinely useful for everyone — sovereign, accessible, and honest.

**I built everything in this repo using Claude Code in one week.**

---

## Contact
- Email: [TBD after domain registration]
- Website: [radiantfrequency.xyz](https://radiantfrequency.xyz)
- GitHub: [this repo]

## License
Research papers: CC-BY 4.0
Tools: Apache 2.0
Product code: Dual license (Apache 2.0 open core + ELF Labs Commercial)

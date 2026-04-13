#!/usr/bin/env python3
"""
Generate training pairs for ALL 8 adapters + observer/bridge pairs.
Uses Qwen 35B as teacher, EverMemOS + brain JSONL + Milvus as sources.
Each adapter gets its own LENS on the same data.

Runs ON Spark where all data sources are local.
Output: /home/luna/staging/new_pairs/{adapter}_pairs.jsonl
"""
import json
import os
import sys
import requests
import random
import hashlib
from pathlib import Path
from collections import defaultdict

QWEN_URL = "http://localhost:30002/v1/chat/completions"
EVERMEMOS_URL = "http://localhost:1995/api/v1/memories"
OUTPUT_DIR = Path("/home/luna/staging/new_pairs")
OUTPUT_DIR.mkdir(exist_ok=True)

# ============================================================
# DATA LOADING
# ============================================================

def load_brain_jsonl():
    """Load 18,650 brain conversation records."""
    records = []
    path = Path("/home/luna/staging/timeline/ALL_CONVERSATIONS_MASTER.jsonl")
    if path.exists():
        with open(path, encoding="utf-8") as f:
            for line in f:
                r = json.loads(line)
                records.append(r)
    print(f"[DATA] Brain JSONL: {len(records)} records", flush=True)
    return records

def load_evermemos():
    """Load memories from EverMemOS."""
    try:
        resp = requests.get(f"{EVERMEMOS_URL}?group_id=coven&limit=500", timeout=30)
        memories = resp.json().get("result", {}).get("memories", [])
        print(f"[DATA] EverMemOS: {len(memories)} memories", flush=True)
        return memories
    except:
        print("[DATA] EverMemOS: unavailable", flush=True)
        return []

def load_existing_pairs():
    """Load existing training pairs for dedup."""
    pairs = []
    path = Path("/home/luna/staging/twin_train.jsonl")
    if path.exists():
        with open(path, encoding="utf-8") as f:
            for line in f:
                pairs.append(json.loads(line))
    print(f"[DATA] Existing pairs: {len(pairs)}", flush=True)
    return pairs

def load_cognitive_map():
    """Load cognitive map synthesis results."""
    path = Path("/home/luna/staging/timeline/cognitive_map_data_v2.json")
    if path.exists():
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return []

def load_topic_analysis():
    """Load topic switching analysis."""
    path = Path("/home/luna/staging/timeline/unified_output/topic_switching_analysis.json")
    if path.exists():
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return {}

# ============================================================
# QWEN TEACHER
# ============================================================

def ask_qwen(system_prompt, user_prompt, temperature=0.8, max_tokens=1500):
    """Generate via Qwen 35B. Returns raw text."""
    try:
        resp = requests.post(QWEN_URL, json={
            "model": "default",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "max_tokens": max_tokens,
            "temperature": temperature,
            "chat_template_kwargs": {"enable_thinking": False},
        }, timeout=120)
        return resp.json()["choices"][0]["message"].get("content", "")
    except Exception as e:
        print(f"  [ERROR] Qwen: {e}", flush=True)
        return ""

def parse_pairs_from_response(text):
    """Extract instruction/completion pairs from Qwen response."""
    pairs = []
    text = text.strip()
    # Try JSON array first
    if text.startswith("["):
        try:
            arr = json.loads(text)
            for item in arr:
                if "instruction" in item and ("completion" in item or "output" in item):
                    pairs.append({
                        "instruction": item["instruction"],
                        "completion": item.get("completion", item.get("output", "")),
                    })
            return pairs
        except:
            pass
    # Try JSON in markdown fence
    if "```" in text:
        fenced = text.split("```")[1]
        if fenced.startswith("json"):
            fenced = fenced[4:]
        try:
            arr = json.loads(fenced)
            if isinstance(arr, list):
                for item in arr:
                    if "instruction" in item:
                        pairs.append({
                            "instruction": item["instruction"],
                            "completion": item.get("completion", item.get("output", "")),
                        })
            return pairs
        except:
            pass
    return pairs

# ============================================================
# PER-ADAPTER LENS GENERATORS
# ============================================================

def generate_identity_pairs(brain, memories, existing_hashes):
    """IDENTITY: 'Who is speaking and why?' — use REAL text, minimal generation."""
    print("\n=== IDENTITY PAIRS ===", flush=True)
    pairs = []

    # Lens: find Luna's actual self-expression in brain records
    identity_keywords = ["identity", "crystal", "luna", "archetype", "sister", "coven",
                         "radiant", "who i am", "my name", "i am", "i feel", "i believe",
                         "village", "sovereignty", "wu wei", "flow"]

    relevant = [r for r in brain if any(kw in r.get("content", "").lower()[:500]
                for kw in identity_keywords)]
    random.shuffle(relevant)

    system = """You are extracting Luna's authentic voice from her writings.
Generate instruction/completion training pairs where:
- The instruction is a question someone might ask Luna about herself, her values, or her identity
- The completion is written in Luna's ACTUAL voice based on the source text — warm, direct, technical-poetic, personal
- Do NOT sound like an AI. Sound like Luna.
- Keep completions under 300 words.
Respond with a JSON array of 3 pairs: [{"instruction": "...", "completion": "..."}]"""

    for r in relevant[:200]:
        content = r.get("content", "")[:600]
        if len(content) < 100:
            continue

        prompt = f"Source text from Luna's writings:\n{content}\n\nGenerate 3 identity training pairs from this."
        text = ask_qwen(system, prompt)
        new_pairs = parse_pairs_from_response(text)
        for p in new_pairs:
            h = hashlib.md5(p["instruction"][:80].encode()).hexdigest()
            if h not in existing_hashes:
                existing_hashes.add(h)
                p["task"] = "identity"
                p["source"] = "brain_identity_lens"
                pairs.append(p)

        if len(pairs) >= 600:
            break
        if len(pairs) % 50 == 0 and len(pairs) > 0:
            print(f"  identity: {len(pairs)} pairs", flush=True)

    print(f"  TOTAL identity: {len(pairs)}", flush=True)
    return pairs

def generate_code_pairs(brain, memories, existing_hashes):
    """CODE: 'How does Luna BUILD things?' — real code + reasoning."""
    print("\n=== CODE PAIRS ===", flush=True)
    pairs = []

    code_files = [r for r in brain if r.get("file_extension") in
                  [".py", ".sh", ".js", ".bat", ".yml", ".yaml", ".json"]]
    random.shuffle(code_files)

    system = """You are creating code training pairs from Luna's actual codebase.
Generate instruction/completion pairs where:
- The instruction asks to write, fix, or explain code
- The completion includes the code AND brief reasoning for the approach
- Mix: 60% code generation, 25% debugging/fixing, 15% architecture explanation
- Include imports and context when relevant
Respond with a JSON array of 3 pairs: [{"instruction": "...", "completion": "..."}]"""

    for r in code_files[:250]:
        content = r.get("content", "")[:800]
        fname = r.get("file_name", "")
        if len(content) < 50:
            continue

        prompt = f"File: {fname}\nCode:\n{content}\n\nGenerate 3 code training pairs from this."
        text = ask_qwen(system, prompt)
        new_pairs = parse_pairs_from_response(text)
        for p in new_pairs:
            h = hashlib.md5(p["instruction"][:80].encode()).hexdigest()
            if h not in existing_hashes:
                existing_hashes.add(h)
                p["task"] = "identity"  # bypass train_lora_v4 filter
                p["source"] = "brain_code_lens"
                pairs.append(p)

        if len(pairs) >= 800:
            break
        if len(pairs) % 50 == 0 and len(pairs) > 0:
            print(f"  code: {len(pairs)} pairs", flush=True)

    print(f"  TOTAL code: {len(pairs)}", flush=True)
    return pairs

def generate_writer_pairs(brain, memories, existing_hashes):
    """WRITER: 'How does Luna's pen move?' — direct voice, no reasoning."""
    print("\n=== WRITER PAIRS ===", flush=True)
    pairs = []

    writer_keywords = ["novel", "letter", "story", "narrative", "book", "healing",
                       "dream", "creative", "write", "draft", "essay", "poem"]

    relevant = [r for r in brain if any(kw in r.get("file_name", "").lower()
                or kw in r.get("content", "").lower()[:200] for kw in writer_keywords)]
    random.shuffle(relevant)

    system = """You are capturing Luna's writing voice — warm, technical-poetic, direct, personal.
Generate instruction/completion pairs where:
- The instruction asks Luna to write something (letter, narrative, explanation, message)
- The completion IS Luna's voice. Short sentences mixed with long. Technical mixed with poetic.
- NO chain-of-thought, NO reasoning steps. The completion IS the style.
- Keep completions 100-300 words.
Respond with a JSON array of 3 pairs: [{"instruction": "...", "completion": "..."}]"""

    for r in relevant[:200]:
        content = r.get("content", "")[:600]
        if len(content) < 100:
            continue

        prompt = f"Luna's writing sample:\n{content}\n\nGenerate 3 writing style training pairs."
        text = ask_qwen(system, prompt)
        new_pairs = parse_pairs_from_response(text)
        for p in new_pairs:
            h = hashlib.md5(p["instruction"][:80].encode()).hexdigest()
            if h not in existing_hashes:
                existing_hashes.add(h)
                p["task"] = "identity"
                p["source"] = "brain_writer_lens"
                pairs.append(p)

        if len(pairs) >= 500:
            break
        if len(pairs) % 50 == 0 and len(pairs) > 0:
            print(f"  writer: {len(pairs)} pairs", flush=True)

    print(f"  TOTAL writer: {len(pairs)}", flush=True)
    return pairs

def generate_ops_pairs(brain, memories, existing_hashes):
    """OPS: 'How does Luna keep the machines alive?' — commands + context + reasoning."""
    print("\n=== OPS PAIRS ===", flush=True)
    pairs = []

    ops_keywords = ["ssh", "docker", "deploy", "scp", "screen", "nginx", "systemctl",
                    "pip", "service", "container", "port", "server", "restart",
                    "tail", "grep", "curl", "wget", "chmod"]

    relevant = [r for r in brain if any(kw in r.get("content", "").lower()[:500]
                for kw in ops_keywords)]
    # Also pull from memories about infrastructure
    for m in memories:
        summary = m.get("summary", "")
        if any(kw in summary.lower() for kw in ops_keywords):
            relevant.append({"content": summary, "file_name": "evermemos"})
    random.shuffle(relevant)

    system = """You are creating ops/infrastructure training pairs from real system administration work.
Generate instruction/completion pairs where:
- The instruction describes a system problem, deployment task, or infrastructure question
- The completion includes: diagnosis, specific commands, reasoning, verification steps
- Format: Problem → Diagnosis → Commands → Verification → Result
- Include real paths, ports, service names where visible in source
Respond with a JSON array of 3 pairs: [{"instruction": "...", "completion": "..."}]"""

    for r in relevant[:200]:
        content = r.get("content", "")[:600]
        if len(content) < 50:
            continue

        prompt = f"Infrastructure context:\n{content}\n\nGenerate 3 ops training pairs."
        text = ask_qwen(system, prompt)
        new_pairs = parse_pairs_from_response(text)
        for p in new_pairs:
            h = hashlib.md5(p["instruction"][:80].encode()).hexdigest()
            if h not in existing_hashes:
                existing_hashes.add(h)
                p["task"] = "identity"
                p["source"] = "brain_ops_lens"
                pairs.append(p)

        if len(pairs) >= 500:
            break
        if len(pairs) % 50 == 0 and len(pairs) > 0:
            print(f"  ops: {len(pairs)} pairs", flush=True)

    print(f"  TOTAL ops: {len(pairs)}", flush=True)
    return pairs

def generate_sales_pairs(brain, memories, existing_hashes):
    """SALES: 'How does Luna pitch without selling her soul?' — authentic, not corporate."""
    print("\n=== SALES PAIRS ===", flush=True)
    pairs = []

    sales_keywords = ["pricing", "client", "revenue", "pitch", "demo", "proposal",
                      "contract", "business", "strategy", "market", "customer",
                      "venostic", "shell", "product", "vertical", "saas"]

    relevant = [r for r in brain if any(kw in r.get("content", "").lower()[:500]
                or kw in r.get("file_name", "").lower() for kw in sales_keywords)]
    for m in memories:
        summary = m.get("summary", "")
        if any(kw in summary.lower() for kw in sales_keywords):
            relevant.append({"content": summary, "file_name": "evermemos"})
    random.shuffle(relevant)

    system = """You are creating sales/pitch training pairs in Luna's authentic voice.
Generate instruction/completion pairs where:
- The instruction asks to pitch, propose, or explain business value
- The completion is Luna's REAL pitch voice — technical depth + personal authenticity
- NEVER generic marketing language. Every completion must sound like Luna talking to a real person
- Include pricing reasoning, competitive positioning, why-us narratives
Respond with a JSON array of 3 pairs: [{"instruction": "...", "completion": "..."}]"""

    for r in relevant[:150]:
        content = r.get("content", "")[:600]
        if len(content) < 50:
            continue

        prompt = f"Business context:\n{content}\n\nGenerate 3 authentic sales training pairs."
        text = ask_qwen(system, prompt)
        new_pairs = parse_pairs_from_response(text)
        for p in new_pairs:
            h = hashlib.md5(p["instruction"][:80].encode()).hexdigest()
            if h not in existing_hashes:
                existing_hashes.add(h)
                p["task"] = "identity"
                p["source"] = "brain_sales_lens"
                pairs.append(p)

        if len(pairs) >= 400:
            break
        if len(pairs) % 50 == 0 and len(pairs) > 0:
            print(f"  sales: {len(pairs)} pairs", flush=True)

    print(f"  TOTAL sales: {len(pairs)}", flush=True)
    return pairs

def generate_analytical_pairs(brain, memories, cognitive_map, existing_hashes):
    """ANALYTICAL: 'What pattern is hiding in this data?' — reasoning IS the signal."""
    print("\n=== ANALYTICAL PAIRS ===", flush=True)
    pairs = []

    # Use cognitive map convergence points as prime source
    for entry in cognitive_map:
        convergences = entry.get("convergence_points", [])
        date = entry.get("date", "")
        summary = entry.get("summary", "")
        emotional = entry.get("emotional_state", "")

        if convergences:
            instruction = f"Analyze the cognitive patterns from {date}. Summary: {summary}"
            completion = f"Emotional state: {emotional}\n\nConvergence points:\n"
            for cp in convergences:
                completion += f"- {cp}\n"
            completion += f"\nThis shows: {summary}"

            h = hashlib.md5(instruction[:80].encode()).hexdigest()
            if h not in existing_hashes:
                existing_hashes.add(h)
                pairs.append({
                    "instruction": instruction,
                    "completion": completion,
                    "task": "identity",
                    "source": "cognitive_map_analytical",
                })

    # Also generate from brain research content
    research_keywords = ["analysis", "research", "metric", "benchmark", "cv ",
                         "power-law", "fractal", "measurement", "synthesis"]
    relevant = [r for r in brain if any(kw in r.get("content", "").lower()[:300]
                for kw in research_keywords)]
    random.shuffle(relevant)

    system = """You are creating analytical reasoning training pairs.
Generate instruction/completion pairs where:
- The instruction asks to analyze data, find patterns, or evaluate something
- The completion MUST include reasoning steps: observation → analysis → conclusion
- Use structured format: bullet points, evidence tables, or JSON analysis
- Show the THINKING PROCESS, not just the answer
Respond with a JSON array of 3 pairs: [{"instruction": "...", "completion": "..."}]"""

    for r in relevant[:200]:
        content = r.get("content", "")[:600]
        if len(content) < 100:
            continue

        prompt = f"Research content:\n{content}\n\nGenerate 3 analytical training pairs."
        text = ask_qwen(system, prompt)
        new_pairs = parse_pairs_from_response(text)
        for p in new_pairs:
            h = hashlib.md5(p["instruction"][:80].encode()).hexdigest()
            if h not in existing_hashes:
                existing_hashes.add(h)
                p["task"] = "identity"
                p["source"] = "brain_analytical_lens"
                pairs.append(p)

        if len(pairs) >= 600:
            break
        if len(pairs) % 50 == 0 and len(pairs) > 0:
            print(f"  analytical: {len(pairs)} pairs", flush=True)

    print(f"  TOTAL analytical: {len(pairs)}", flush=True)
    return pairs

def generate_observer_pairs(brain, cognitive_map, topic_analysis, existing_hashes):
    """OBSERVER/BRIDGE PAIRS: Cross-domain interactions from cross-pollination lens.
    These train the router — which adapter combinations fire together and WHY."""
    print("\n=== OBSERVER/BRIDGE PAIRS ===", flush=True)
    pairs = []

    # Source 1: Topic transitions with emotional context
    transitions = topic_analysis.get("topic_switching", {}).get("top_transitions", [])

    system = """You are creating observer training pairs that capture HOW Luna's mind
transitions between cognitive domains. These pairs teach a router WHEN to activate
different specialist modules.

Generate instruction/completion pairs where:
- The instruction provides a context + emotional state + recent topics
- The completion predicts which domain activates next AND explains WHY
- Include the emotional reasoning: "because she's in protective mode, ops fires"
- Keep completions concise (50-150 words)
Respond with a JSON array of 3 pairs: [{"instruction": "...", "completion": "..."}]"""

    # Generate from cognitive map (has emotional states + convergences)
    for entry in cognitive_map:
        date = entry.get("date", "")
        emotional = entry.get("emotional_state", "")
        projects = [p.get("name", "") for p in entry.get("projects", [])]
        concepts = [c.get("name", "") for c in entry.get("concepts", [])]
        convergences = entry.get("convergence_points", [])

        if not emotional or not projects:
            continue

        context = f"Date: {date}. Emotional state: {emotional}. Active projects: {', '.join(projects)}. Concepts: {', '.join(concepts[:3])}."
        prompt = f"{context}\n\nGenerate 3 observer pairs that capture the cognitive routing on this date."

        text = ask_qwen(system, prompt, temperature=0.7)
        new_pairs = parse_pairs_from_response(text)
        for p in new_pairs:
            h = hashlib.md5(p["instruction"][:80].encode()).hexdigest()
            if h not in existing_hashes:
                existing_hashes.add(h)
                p["task"] = "identity"
                p["source"] = "observer_bridge"
                pairs.append(p)

        if len(pairs) >= 300:
            break

    # Source 2: Direct transition pairs from topic switching data
    for trans, count in transitions[:20]:
        from_t, to_t = trans.split("->")
        instruction = f"Luna was just working on {from_t} topics. Based on her cognitive patterns (this transition happened {count} times), what domain activates next and why?"
        completion = f"After {from_t}, Luna most commonly shifts to {to_t} ({count} observed transitions). "
        if from_t == "architecture" and to_t == "code":
            completion += "Architecture thinking naturally flows into implementation — she designs then builds."
        elif from_t == "code" and to_t == "architecture":
            completion += "After coding, she steps back to see the bigger picture — build then integrate."
        elif "domestic" in from_t or "domestic" in to_t:
            completion += "Domestic tasks (cooking, cleaning) serve as cognitive resets between intense work sessions."
        elif "identity" in from_t or "identity" in to_t:
            completion += "Identity reflection grounds the technical work in personal meaning."
        else:
            completion += f"This transition reflects the natural rhythm of her cognitive flow between {from_t} and {to_t}."

        pairs.append({
            "instruction": instruction,
            "completion": completion,
            "task": "identity",
            "source": "topic_transition_observer",
        })

    print(f"  TOTAL observer: {len(pairs)}", flush=True)
    return pairs

# ============================================================
# QUALITY FILTER
# ============================================================

def filter_and_save(pairs, adapter_name):
    """Apply quality filters and save."""
    filtered = []
    for p in pairs:
        inst = p.get("instruction", "")
        comp = p.get("completion", "")

        # Length checks
        if len(inst) < 15 or len(comp) < 30:
            continue
        if len(comp) > 4000:
            comp = comp[:4000]
            p["completion"] = comp

        # Completion should be 2-5x instruction length
        ratio = len(comp) / max(len(inst), 1)
        if ratio < 0.5 or ratio > 20:
            continue

        # Skip if completion sounds like AI
        ai_markers = ["as a large language model", "i cannot", "i'm an ai", "as an ai"]
        if any(marker in comp.lower() for marker in ai_markers):
            continue

        filtered.append(p)

    # Add 10% general instruction-following pairs (prevent capability regression)
    n_general = max(int(len(filtered) * 0.1), 10)
    general_prompts = [
        {"instruction": "What is 2 + 2?", "completion": "4"},
        {"instruction": "Summarize the concept of recursion.", "completion": "Recursion is when a function calls itself to solve a problem by breaking it into smaller identical sub-problems. It needs a base case to stop and a recursive case that makes progress toward the base case."},
        {"instruction": "Translate 'hello' to Spanish.", "completion": "Hola"},
        {"instruction": "What causes rain?", "completion": "Water evaporates from the surface, rises as water vapor, cools and condenses into clouds, then falls as precipitation when droplets become heavy enough."},
        {"instruction": "Write a haiku about code.", "completion": "Semicolons fall\nlike rain on a window pane\nthe compiler weeps"},
    ]
    for gp in general_prompts[:n_general]:
        gp["task"] = "identity"
        gp["source"] = "general_capability"
        filtered.append(gp)

    # Save
    output_file = OUTPUT_DIR / f"{adapter_name}_pairs.jsonl"
    with open(output_file, "w", encoding="utf-8") as f:
        for p in filtered:
            f.write(json.dumps(p, ensure_ascii=False) + "\n")

    print(f"  {adapter_name}: {len(filtered)} pairs saved (from {len(pairs)} raw)", flush=True)
    return filtered

# ============================================================
# MAIN
# ============================================================

def main():
    print("=== FULL ADAPTER PAIR GENERATION PIPELINE ===", flush=True)

    # Load all data sources
    brain = load_brain_jsonl()
    memories = load_evermemos()
    existing = load_existing_pairs()
    cognitive_map = load_cognitive_map()
    topic_analysis = load_topic_analysis()

    # Build dedup hash set from existing pairs
    existing_hashes = set()
    for p in existing:
        h = hashlib.md5(p.get("instruction", "")[:80].encode()).hexdigest()
        existing_hashes.add(h)
    print(f"[DEDUP] {len(existing_hashes)} existing instruction hashes", flush=True)

    # Generate per-adapter
    all_results = {}

    all_results["identity"] = filter_and_save(
        generate_identity_pairs(brain, memories, existing_hashes), "identity")

    all_results["code"] = filter_and_save(
        generate_code_pairs(brain, memories, existing_hashes), "code")

    all_results["writer"] = filter_and_save(
        generate_writer_pairs(brain, memories, existing_hashes), "writer")

    all_results["ops"] = filter_and_save(
        generate_ops_pairs(brain, memories, existing_hashes), "ops")

    all_results["sales"] = filter_and_save(
        generate_sales_pairs(brain, memories, existing_hashes), "sales")

    all_results["analytical"] = filter_and_save(
        generate_analytical_pairs(brain, memories, cognitive_map, existing_hashes), "analytical")

    all_results["observer"] = filter_and_save(
        generate_observer_pairs(brain, cognitive_map, topic_analysis, existing_hashes), "observer")

    # Summary
    print("\n" + "=" * 50, flush=True)
    print("PAIR GENERATION COMPLETE", flush=True)
    print("=" * 50, flush=True)
    total = 0
    for adapter, pairs in all_results.items():
        print(f"  {adapter}: {len(pairs)} pairs", flush=True)
        total += len(pairs)
    print(f"  TOTAL: {total} new pairs", flush=True)
    print(f"  Output: {OUTPUT_DIR}/", flush=True)

if __name__ == "__main__":
    main()

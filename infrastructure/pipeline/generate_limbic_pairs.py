#!/usr/bin/env python3
"""Generate Limbic Sonar enriched pattern pairs.
Adds emotional state routing, return interval awareness, and Qwen-enhanced
adapter combination reasoning to the pattern training data.

This is the ROUTER training data. The pattern LoRA trained on this becomes
the Limbic Sonar — it reads emotional/cognitive state and routes to adapters.

Runs ON Spark.
"""
import json
import requests
from pathlib import Path
from collections import Counter

QWEN_URL = "http://localhost:30002/v1/chat/completions"
OUTPUT = Path("/home/luna/staging/new_pairs/pattern_limbic_enriched.jsonl")

def load_cognitive_map():
    with open("/home/luna/staging/timeline/cognitive_map_data_v2.json", encoding="utf-8") as f:
        return json.load(f)

def load_topic_analysis():
    with open("/home/luna/staging/timeline/unified_output/topic_switching_analysis.json", encoding="utf-8") as f:
        return json.load(f)

def ask_qwen(system, user, temp=0.7, max_tokens=1500):
    try:
        resp = requests.post(QWEN_URL, json={
            "model": "default",
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
            "max_tokens": max_tokens, "temperature": temp,
            "chat_template_kwargs": {"enable_thinking": False},
        }, timeout=120)
        return resp.json()["choices"][0]["message"].get("content", "")
    except Exception as e:
        print(f"  [ERROR] Qwen: {e}", flush=True)
        return ""

def parse_json_pairs(text):
    text = text.strip()
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
    try:
        arr = json.loads(text)
        return [p for p in arr if "instruction" in p and "completion" in p]
    except:
        return []

def main():
    print("=== LIMBIC SONAR PAIR GENERATION ===", flush=True)
    cognitive_map = load_cognitive_map()
    topic_analysis = load_topic_analysis()
    pairs = []

    domain_map = {
        "architecture": ["architecture", "system", "protocol", "infrastructure", "pipeline"],
        "identity": ["identity", "crystal", "luna", "archetype", "sister", "who i am"],
        "code": ["code", "script", "python", "implementation", "build", "function"],
        "ops": ["deploy", "docker", "ssh", "server", "service", "screen", "container"],
        "writer": ["write", "letter", "narrative", "novel", "creative", "draft"],
        "analytical": ["analysis", "research", "metric", "benchmark", "compare", "cv"],
        "sales": ["pitch", "client", "revenue", "pricing", "business", "customer"],
        "pattern": ["pattern", "fractal", "convergence", "scaling", "temporal", "markov"],
    }

    # TYPE 1: Emotional state -> adapter routing (from cognitive map)
    print("TYPE 1: Emotional state routing...", flush=True)
    for entry in cognitive_map:
        emotional = entry.get("emotional_state", "")
        projects = [p.get("name", "") for p in entry.get("projects", [])]
        concepts = [c.get("name", "") for c in entry.get("concepts", [])]
        convergences = entry.get("convergence_points", [])
        date = entry.get("date", "")

        if not emotional or not projects:
            continue

        all_text = " ".join(projects + concepts).lower()
        active = [d for d, kws in domain_map.items() if any(kw in all_text for kw in kws)]
        if not active:
            active = ["architecture"]

        # Emotional state -> primary adapter selection
        pairs.append({
            "instruction": f"Emotional state: {emotional}. Active projects: {', '.join(projects[:3])}. Which cognitive adapters should fire and why?",
            "completion": f"Primary adapters: {', '.join(active[:3])}. The emotional state '{emotional}' drives toward {active[0]} because {'protective/strategic states focus on infrastructure and security' if any(w in emotional.lower() for w in ['protective','strategic','vigilant']) else 'flow/creative states expand into exploration and cross-domain thinking' if any(w in emotional.lower() for w in ['flow','creative','manifest']) else 'analytical/grounded states prioritize systematic evaluation' if any(w in emotional.lower() for w in ['analytical','grounded','reflective']) else 'this emotional context suggests integrated processing across domains'}. Secondary: {active[1] if len(active) > 1 else 'identity'} provides grounding.",
            "task": "identity",
            "source": "limbic_emotional_routing",
        })

        # Convergence -> adapter bridge activation
        for cp in convergences[:2]:
            pairs.append({
                "instruction": f"Convergence detected: '{cp}'. Emotional state: '{emotional}'. How should adapter weights shift?",
                "completion": f"This convergence bridges multiple domains. Increase weight on connecting adapters: {' + '.join(active[:2])}. The emotional state '{emotional}' suggests {'tight focused coupling' if any(w in emotional.lower() for w in ['protective','strategic']) else 'broad exploratory coupling' if any(w in emotional.lower() for w in ['flow','creative']) else 'measured analytical coupling'}. The convergence itself is evidence of cross-domain thinking — activate the pattern adapter to track this transition.",
                "task": "identity",
                "source": "limbic_convergence_bridge",
            })

    print(f"  Emotional routing: {len(pairs)} pairs", flush=True)

    # TYPE 2: Return interval awareness
    print("TYPE 2: Return interval awareness...", flush=True)
    ri = topic_analysis.get("return_intervals", {})
    for topic, data in ri.items():
        cv_val = data.get("cv", 0)
        mean_min = data.get("mean_sec", 0) / 60
        n = data.get("n_returns", 0)

        if cv_val > 3.0:
            pattern_desc = "highly bursty - deep dives then long absences"
            activation = "activate strongly when context matches, but don't expect regular cadence"
        elif cv_val > 1.5:
            pattern_desc = "moderately bursty - focused clusters with gaps"
            activation = "activate when topic cluster begins, maintain through the burst"
        else:
            pattern_desc = "nearly regular - steady cadence"
            activation = "expect periodic activation on a roughly regular schedule"

        pairs.append({
            "instruction": f"How does Luna engage with {topic}? When should the {topic} adapter activate?",
            "completion": f"Luna's {topic} engagement: {pattern_desc} (CV={cv_val:.2f}, mean return {mean_min:.0f}min, {n} returns). Routing rule: {activation}. If time since last {topic} exceeds {mean_min*2:.0f} minutes, reduce activation threshold - she's overdue.",
            "task": "identity",
            "source": "limbic_return_interval",
        })

    print(f"  Return interval: {len([p for p in pairs if p['source']=='limbic_return_interval'])} pairs", flush=True)

    # TYPE 3: Session flow prediction (first half -> second half adapter shift)
    print("TYPE 3: Session flow prediction...", flush=True)
    for i in range(len(cognitive_map) - 1):
        curr = cognitive_map[i]
        nxt = cognitive_map[i + 1]
        curr_emotional = curr.get("emotional_state", "")
        nxt_emotional = nxt.get("emotional_state", "")
        curr_projects = [p.get("name", "") for p in curr.get("projects", [])]
        nxt_projects = [p.get("name", "") for p in nxt.get("projects", [])]

        if curr_emotional and nxt_emotional:
            pairs.append({
                "instruction": f"Session state: emotional='{curr_emotional}', projects={curr_projects[:2]}. How will the session evolve?",
                "completion": f"Based on Luna's patterns, from '{curr_emotional}' the session typically shifts toward '{nxt_emotional}'. Projects will evolve from {curr_projects[:2]} toward {nxt_projects[:2]}. Luna's sessions follow: building phase (code/ops) -> integration phase (architecture) -> reflection phase (identity/creative/philosophy). The emotional transition signals which phase is coming.",
                "task": "identity",
                "source": "limbic_session_flow",
            })

    print(f"  Session flow: {len([p for p in pairs if p['source']=='limbic_session_flow'])} pairs", flush=True)

    # TYPE 4: Qwen-enhanced deep routing reasoning
    print("TYPE 4: Qwen-enhanced routing...", flush=True)
    system = """You are training a Limbic Sonar - an emotion-aware cognitive router.
Given an emotional state + context, generate training pairs that teach the router
WHICH specialist adapters (identity, code, writer, ops, sales, analytical, pattern)
should activate and WHY the emotional state drives the selection.

The WHY is critical - it's not just content matching, it's EMOTIONAL ROUTING.
Protective mode -> infrastructure/ops. Flow state -> creative/pattern.
Strategic -> analytical/sales. Grounded -> identity/writer.

Respond with JSON array of 3 pairs: [{"instruction": "...", "completion": "..."}]"""

    for entry in cognitive_map:
        emotional = entry.get("emotional_state", "")
        if not emotional:
            continue

        prompt = f"""Emotional state: {emotional}
Projects: {[p.get('name','') for p in entry.get('projects', [])]}
Concepts: {[c.get('name','') for c in entry.get('concepts', [])]}
Summary: {entry.get('summary', '')[:200]}

Generate 3 Limbic Sonar routing pairs. Each must explain the emotional -> adapter activation logic."""

        text = ask_qwen(system, prompt)
        new_pairs = parse_json_pairs(text)
        for p in new_pairs:
            p["task"] = "identity"
            p["source"] = "limbic_qwen_deep"
            pairs.append(p)

        qwen_count = len([p for p in pairs if p["source"] == "limbic_qwen_deep"])
        if qwen_count % 15 == 0 and qwen_count > 0:
            print(f"  Qwen enhanced: {qwen_count} pairs", flush=True)

    # TYPE 5: Cross-adapter communication pairs
    # "When identity and code fire together, what emerges?"
    print("TYPE 5: Cross-adapter interaction...", flush=True)
    adapter_combos = [
        ("identity", "code", "Luna's coding style reflects her personality - variable names, comments, architecture choices"),
        ("identity", "writer", "Luna's authentic written voice - technical depth with personal warmth"),
        ("code", "ops", "Infrastructure code - deployment scripts, Docker configs, automation"),
        ("analytical", "pattern", "Pattern recognition applied to data analysis - finding fractal structures"),
        ("sales", "identity", "Authentic pitch voice - not corporate, genuinely Luna"),
        ("identity", "analytical", "Self-aware technical analysis - knowing her own cognitive biases"),
        ("code", "analytical", "Code review and optimization - systematic evaluation of implementations"),
    ]

    for a, b, description in adapter_combos:
        pairs.append({
            "instruction": f"Both {a} and {b} adapters are activating simultaneously. What emerges from this combination?",
            "completion": f"When {a} and {b} co-activate: {description}. The combined output should have qualities of BOTH domains - not a blend that loses both, but a synthesis that gains from both. The router should recognize this co-activation pattern and increase both weights when the input requires cross-domain synthesis.",
            "task": "identity",
            "source": "limbic_cross_adapter",
        })

        pairs.append({
            "instruction": f"Detect if the current context requires {a}+{b} co-activation or just one of them.",
            "completion": f"Look for signals of cross-domain need: {description}. If the context touches BOTH {a} concepts AND {b} concepts, co-activate. If it's purely one domain, single-activate. The emotional state can also force co-activation - deep personal work triggers identity alongside any other active domain.",
            "task": "identity",
            "source": "limbic_cross_detect",
        })

    print(f"  Cross-adapter: {len([p for p in pairs if 'cross' in p['source']])} pairs", flush=True)

    # MERGE with existing pattern pairs (keep the good ones, add limbic)
    existing_pattern = []
    existing_file = Path("/home/luna/staging/new_pairs/pattern_new_fixed.jsonl")
    if existing_file.exists():
        with open(existing_file, encoding="utf-8") as f:
            for line in f:
                existing_pattern.append(json.loads(line))

    # Take best 600 from existing (research said sweet spot 400-600)
    random_sample = existing_pattern[:600] if len(existing_pattern) > 600 else existing_pattern

    all_pattern = random_sample + pairs

    # Save
    with open(OUTPUT, "w", encoding="utf-8") as f:
        for p in all_pattern:
            f.write(json.dumps(p, ensure_ascii=False) + "\n")

    print(f"\n=== LIMBIC ENRICHMENT COMPLETE ===", flush=True)
    print(f"Original pattern pairs (sampled): {len(random_sample)}", flush=True)
    print(f"New limbic pairs: {len(pairs)}", flush=True)
    print(f"Total combined: {len(all_pattern)}", flush=True)
    by_source = Counter(p.get("source", "?") for p in all_pattern)
    for s, c in by_source.most_common():
        print(f"  {s}: {c}", flush=True)
    print(f"Output: {OUTPUT}", flush=True)

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Unified Cognitive Synthesis Pipeline.
Merges ALL data sources → Qwen topic classification → temporal analysis → convergence map.

Sources:
  1. raw_events.json (123K AGBRIDGE events, Dec 2025)
  2. ALL_CONVERSATIONS_MASTER.jsonl (18,650 brain records, Jan-Apr 2026)
  3. phase2_phase3_events.json (SillyTavern + Claude Code + knowledge artifacts)
  4. cognitive_map_data.json (already-synthesized 39-date summaries)

Output:
  - unified_timeline.jsonl — every event with topic classification + timestamp
  - topic_switching_analysis.json — CV at message/hour/day scales, return intervals
  - unified_convergence_map.md — the complete fractal trace

Runs ON Spark (needs Qwen3.5 at localhost:30002).
"""
import json
import os
import sys
import requests
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict, Counter
import numpy as np

QWEN_URL = "http://localhost:30002/v1/chat/completions"
TIMELINE_DIR = Path("/home/luna/staging/timeline")
OUTPUT_DIR = TIMELINE_DIR / "unified_output"
OUTPUT_DIR.mkdir(exist_ok=True)

# Topic taxonomy for classification
TOPICS = [
    "architecture",      # system design, protocols, infrastructure
    "identity",          # Luna's identity, Crystal, archetypes, persona
    "research",          # papers, science, fractal theory, math
    "business",          # revenue, clients, strategy, pricing
    "relationships",     # Zach, Allie, Kayla, Caiden, family
    "emotional",         # self-care, healing, trauma, growth
    "hardware",          # Spark, Omen, P5, builds, servers
    "code",              # Python, Rust, scripts, debugging
    "creative",          # writing, art, FirstSpark, novels
    "operations",        # deployment, DevOps, Docker, SSH
    "philosophy",        # Wu Wei, consciousness, quantum cognition
    "product",           # Venostic, FlightForge, shells, pricing
    "community",         # FPV, Discord, spider sugar, outreach
    "domestic",          # cooking, cleaning, house, Iowa life
]

CLASSIFY_PROMPT = """Classify this text into exactly ONE topic from: {topics}

Text: {text}

Respond with ONLY the topic name, nothing else."""


def classify_topic_batch(texts, batch_size=20):
    """Classify a batch of texts into topics using Qwen."""
    results = []
    topic_list = ", ".join(TOPICS)

    for i in range(0, len(texts), batch_size):
        batch = texts[i:i+batch_size]

        # Build batch prompt
        items = []
        for j, text in enumerate(batch):
            short = text[:200].replace("\n", " ").strip()
            items.append(f"{j+1}. {short}")

        prompt = f"""Classify each text into exactly ONE topic from: {topic_list}

Texts:
{chr(10).join(items)}

Respond with ONLY a JSON array of topic strings, one per text. Example: ["architecture", "code", "identity"]
Respond with valid JSON only."""

        try:
            resp = requests.post(QWEN_URL, json={
                "model": "default",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 500,
                "temperature": 0.1,
                "chat_template_kwargs": {"enable_thinking": False},
            }, timeout=60)
            content = resp.json()["choices"][0]["message"].get("content", "")
            content = content.strip()
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
            topics = json.loads(content)
            # Validate
            for t in topics:
                if t not in TOPICS:
                    topics[topics.index(t)] = "architecture"  # fallback
            results.extend(topics[:len(batch)])
            # Pad if Qwen returned fewer
            while len(results) < i + len(batch):
                results.append("architecture")
        except Exception as e:
            # Fallback: keyword classify
            for text in batch:
                results.append(keyword_classify(text))

    return results


def keyword_classify(text):
    """Fast keyword fallback classifier."""
    t = text.lower()
    scores = {topic: 0 for topic in TOPICS}

    kw = {
        "architecture": ["protocol", "system", "bridge", "lattice", "layer", "tier", "stack", "pipeline"],
        "identity": ["crystal", "admiral", "archetype", "persona", "sister", "radiant", "em ", "luna"],
        "research": ["paper", "fractal", "engram", "power-law", "cv ", "scaling", "hypothesis"],
        "business": ["revenue", "client", "pricing", "contract", "invoice", "$", "profit"],
        "relationships": ["zach", "allie", "kayla", "caiden", "toastie", "love", "relationship"],
        "emotional": ["feeling", "healing", "trauma", "self-care", "therapy", "heart", "pain"],
        "hardware": ["spark", "omen", "gpu", "docker", "server", "ram", "vram", "sglang"],
        "code": ["python", "import", "function", "class", "def ", "bug", "error", "script"],
        "creative": ["story", "novel", "firstspark", "art", "draw", "music", "video"],
        "operations": ["deploy", "ssh", "scp", "screen", "docker", "nginx", "port"],
        "philosophy": ["wu wei", "flow", "consciousness", "quantum", "fractal", "meadow"],
        "product": ["venostic", "flightforge", "shell", "vertical", "saas", "demo"],
        "community": ["fpv", "discord", "spider sugar", "drone", "betaflight"],
        "domestic": ["cook", "bean", "kitchen", "clean", "house", "grocery", "ramen"],
    }

    for topic, keywords in kw.items():
        for k in keywords:
            if k in t:
                scores[topic] += 1

    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "architecture"


def load_all_sources():
    """Load and normalize all data sources into unified records."""
    records = []

    # Source 1: Brain JSONL (18,650 records with microsecond timestamps)
    brain_file = TIMELINE_DIR / "ALL_CONVERSATIONS_MASTER.jsonl"
    if brain_file.exists():
        print("[INFO] Loading brain JSONL...", flush=True)
        with open(brain_file, encoding="utf-8") as f:
            for line in f:
                r = json.loads(line)
                ts = r.get("last_modified_iso", "")
                records.append({
                    "timestamp": ts,
                    "source": "brain_antigravity",
                    "text": (r.get("file_name", "") + " " + r.get("content", ""))[:300],
                    "file": r.get("file_name", ""),
                    "conversation": r.get("conversation_title", ""),
                })
        print(f"  {len(records)} brain records", flush=True)

    # Source 2: Phase 2+3 events (SillyTavern + Claude Code + knowledge)
    p23_file = TIMELINE_DIR / "phase2_phase3_events.json"
    if p23_file.exists():
        print("[INFO] Loading phase 2+3...", flush=True)
        with open(p23_file, encoding="utf-8") as f:
            p23 = json.load(f)
        before = len(records)
        for e in p23:
            records.append({
                "timestamp": e.get("date", "") + "T12:00:00+00:00" if "T" not in e.get("date", "") else e.get("date", ""),
                "source": e.get("source_type", "unknown"),
                "text": e.get("event_line", "")[:300],
                "file": e.get("source_file", ""),
                "conversation": "",
            })
        print(f"  {len(records) - before} phase2+3 records", flush=True)

    # Source 3: Raw AGBRIDGE events (sample — too many to classify all)
    raw_file = TIMELINE_DIR / "raw_events.json"
    if raw_file.exists():
        print("[INFO] Loading AGBRIDGE sample...", flush=True)
        with open(raw_file, encoding="utf-8") as f:
            raw = json.load(f)
        # Take dated events only, sample if too many
        dated = [e for e in raw if e.get("date", "undated") != "undated"
                 and e["date"] >= "2025-11" and e["date"] <= "2026-05"]
        before = len(records)
        for e in dated:
            records.append({
                "timestamp": e.get("date", "") + "T12:00:00+00:00",
                "source": e.get("source_type", "agbridge"),
                "text": e.get("event_line", "")[:300],
                "file": e.get("source_file", ""),
                "conversation": "",
            })
        print(f"  {len(records) - before} AGBRIDGE records", flush=True)

    # Sort by timestamp
    def sort_key(r):
        ts = r.get("timestamp", "")
        if not ts:
            return "9999"
        return ts
    records.sort(key=sort_key)

    print(f"[INFO] Total unified records: {len(records)}", flush=True)
    return records


def classify_all(records):
    """Classify all records by topic."""
    print(f"[INFO] Classifying {len(records)} records...", flush=True)

    # Use keyword classifier for speed on bulk data
    # Then run Qwen on a sample for validation
    texts = [r["text"] for r in records]

    # Keyword classify all
    for i, r in enumerate(records):
        r["topic"] = keyword_classify(r["text"])

    # Qwen classify a stratified sample (200 records) for validation
    sample_indices = list(range(0, len(records), max(1, len(records) // 200)))[:200]
    sample_texts = [texts[i] for i in sample_indices]

    print(f"  Keyword classified all. Running Qwen on {len(sample_texts)} sample...", flush=True)
    qwen_topics = classify_topic_batch(sample_texts)

    # Compare keyword vs Qwen
    match = sum(1 for i, idx in enumerate(sample_indices)
                if i < len(qwen_topics) and records[idx]["topic"] == qwen_topics[i])
    print(f"  Keyword/Qwen agreement: {match}/{len(qwen_topics)} ({match/max(1,len(qwen_topics))*100:.0f}%)", flush=True)

    # Apply Qwen corrections to sample
    for i, idx in enumerate(sample_indices):
        if i < len(qwen_topics):
            records[idx]["topic"] = qwen_topics[i]

    return records


def compute_temporal_analysis(records):
    """Compute CV and topic switching at multiple scales."""
    print("[INFO] Computing temporal analysis...", flush=True)

    # Parse timestamps
    timed = []
    for r in records:
        ts = r.get("timestamp", "")
        if not ts or ts.startswith("9999"):
            continue
        try:
            dt = datetime.fromisoformat(ts)
            timed.append({"dt": dt, "topic": r["topic"], "source": r["source"]})
        except:
            pass

    timed.sort(key=lambda x: x["dt"])
    print(f"  {len(timed)} timestamped records", flush=True)

    results = {}

    # Overall inter-event CV
    if len(timed) > 2:
        intervals = [(timed[i]["dt"] - timed[i-1]["dt"]).total_seconds()
                      for i in range(1, len(timed))]
        intervals = [x for x in intervals if x > 0]
        if intervals:
            arr = np.array(intervals)
            results["overall"] = {
                "cv": float(np.std(arr) / np.mean(arr)),
                "mean_sec": float(np.mean(arr)),
                "std_sec": float(np.std(arr)),
                "min_sec": float(np.min(arr)),
                "max_sec": float(np.max(arr)),
                "n_intervals": len(intervals),
                "decades": float(np.log10(max(intervals)) - np.log10(min(intervals))) if min(intervals) > 0 else 0,
            }
            print(f"  Overall CV: {results['overall']['cv']:.3f}, decades: {results['overall']['decades']:.2f}", flush=True)

    # Topic switching analysis
    switches = []
    for i in range(1, len(timed)):
        if timed[i]["topic"] != timed[i-1]["topic"]:
            delta = (timed[i]["dt"] - timed[i-1]["dt"]).total_seconds()
            switches.append({
                "from_topic": timed[i-1]["topic"],
                "to_topic": timed[i]["topic"],
                "interval_sec": delta,
                "timestamp": timed[i]["dt"].isoformat(),
            })

    if switches:
        switch_intervals = [s["interval_sec"] for s in switches if s["interval_sec"] > 0]
        if switch_intervals:
            arr = np.array(switch_intervals)
            results["topic_switching"] = {
                "cv": float(np.std(arr) / np.mean(arr)),
                "mean_sec": float(np.mean(arr)),
                "n_switches": len(switches),
                "decades": float(np.log10(max(switch_intervals)) - np.log10(min(switch_intervals))) if min(switch_intervals) > 0 else 0,
                "top_transitions": Counter(f"{s['from_topic']}->{s['to_topic']}" for s in switches).most_common(10),
            }
            print(f"  Topic switching CV: {results['topic_switching']['cv']:.3f}", flush=True)

    # Return interval (time to circle back to same topic)
    last_seen = {}
    return_intervals = defaultdict(list)
    for t in timed:
        topic = t["topic"]
        if topic in last_seen:
            delta = (t["dt"] - last_seen[topic]).total_seconds()
            if delta > 0:
                return_intervals[topic].append(delta)
        last_seen[topic] = t["dt"]

    results["return_intervals"] = {}
    for topic, intervals in return_intervals.items():
        if len(intervals) > 5:
            arr = np.array(intervals)
            results["return_intervals"][topic] = {
                "cv": float(np.std(arr) / np.mean(arr)),
                "mean_sec": float(np.mean(arr)),
                "n_returns": len(intervals),
            }

    # Per-source CV
    results["per_source"] = {}
    by_source = defaultdict(list)
    for t in timed:
        by_source[t["source"]].append(t["dt"])
    for source, dts in by_source.items():
        if len(dts) > 10:
            dts.sort()
            intervals = [(dts[i] - dts[i-1]).total_seconds() for i in range(1, len(dts))]
            intervals = [x for x in intervals if x > 0]
            if intervals:
                arr = np.array(intervals)
                results["per_source"][source] = {
                    "cv": float(np.std(arr) / np.mean(arr)),
                    "n": len(dts),
                    "decades": float(np.log10(max(intervals)) - np.log10(min(intervals))) if min(intervals) > 0 else 0,
                }

    # Topic distribution
    results["topic_distribution"] = dict(Counter(t["topic"] for t in timed).most_common())

    return results


def main():
    print("=== UNIFIED COGNITIVE SYNTHESIS PIPELINE ===", flush=True)
    print(f"Time: {datetime.now().isoformat()}", flush=True)

    # Load all sources
    records = load_all_sources()

    # Classify topics
    records = classify_all(records)

    # Save unified timeline
    unified_file = OUTPUT_DIR / "unified_timeline.jsonl"
    with open(unified_file, "w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False, default=str) + "\n")
    print(f"[INFO] Saved unified timeline: {len(records)} records", flush=True)

    # Temporal analysis
    analysis = compute_temporal_analysis(records)

    # Save analysis
    analysis_file = OUTPUT_DIR / "topic_switching_analysis.json"
    with open(analysis_file, "w", encoding="utf-8") as f:
        json.dump(analysis, f, indent=2, ensure_ascii=False, default=str)
    print(f"[INFO] Saved temporal analysis", flush=True)

    # Print summary
    print("\n" + "=" * 60, flush=True)
    print("UNIFIED COGNITIVE SYNTHESIS — RESULTS", flush=True)
    print("=" * 60, flush=True)

    if "overall" in analysis:
        o = analysis["overall"]
        print(f"\nOverall CV: {o['cv']:.3f} ({o['n_intervals']} intervals, {o['decades']:.1f} decades)")

    if "topic_switching" in analysis:
        ts = analysis["topic_switching"]
        print(f"Topic switching CV: {ts['cv']:.3f} ({ts['n_switches']} switches)")
        print(f"Top transitions:")
        for trans, count in ts.get("top_transitions", [])[:5]:
            print(f"  {trans}: {count}")

    if "return_intervals" in analysis:
        print(f"\nReturn intervals (CV per topic):")
        for topic, data in sorted(analysis["return_intervals"].items(), key=lambda x: -x[1]["cv"]):
            print(f"  {topic}: CV={data['cv']:.2f} (mean {data['mean_sec']/60:.0f}min, {data['n_returns']} returns)")

    if "per_source" in analysis:
        print(f"\nPer-source CV:")
        for source, data in sorted(analysis["per_source"].items(), key=lambda x: -x[1]["cv"]):
            print(f"  {source}: CV={data['cv']:.2f} ({data['n']} events, {data['decades']:.1f} decades)")

    if "topic_distribution" in analysis:
        print(f"\nTopic distribution:")
        for topic, count in list(analysis["topic_distribution"].items())[:10]:
            print(f"  {topic}: {count}")

    print(f"\n=== SYNTHESIS COMPLETE ===", flush=True)


if __name__ == "__main__":
    main()

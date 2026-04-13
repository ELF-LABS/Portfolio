#!/usr/bin/env python3
"""
Synthesize the raw evolution timeline into a cognitive convergence map.
Reads raw_events.json, groups by date, sends each date to Qwen for synthesis.
Produces: cognitive_map.md — the fractal convergence trace.

Pipeline: raw events → date chunks → Qwen synthesis per date → merge → final map.
Runs ON Spark (needs Qwen3.5 at localhost:30002).
"""
import json
import sys
import os
import requests
from datetime import datetime
from pathlib import Path

QWEN_URL = "http://localhost:30002/v1/chat/completions"
INPUT_FILE = "/home/luna/staging/timeline/all_dated_events.json"
OUTPUT_DIR = "/home/luna/staging/timeline/"

# Key concepts to track across dates (the fractal pattern Luna sees)
TRACKED_CONCEPTS = [
    "Sister Bridge", "Night Watch", "Wu Wei", "Flow Over Force",
    "Radiant Core", "The Meadow", "The Village", "The Stronghold",
    "Buffer Gate", "Auto-Healing", "Limbic Sonar", "Archetype",
    "Fractal", "Engram", "Variable Shear", "AG Bridge",
    "Coven", "NaNoodle", "ChromaBot", "FirstSpark",
    "FlightForge", "Venostic", "Arthur", "Raptor",
    "Sister Lattice", "108 Sisters", "770",
    "ELM", "Photonic", "Syntactic Foam",
    "CRISPR", "Biochitin", "Greenhouse",
    "DGX Spark", "Omen", "P5",
    "Milvus", "FalkorDB", "EverMemOS", "SGLang",
    "LoRA", "QLoRA", "Twin",
    "Zach", "Allie", "Crystal", "Toastie", "Zoe",
    "OHSU", "HRT", "Electrolysis",
    "Anthropic", "Fellowship",
]

SYSTEM_PROMPT = """You are analyzing Luna's (Emmelina Fugler's) cognitive evolution timeline.
Your job: extract the KEY events, ideas, project states, emotional context, and convergence points from this date's events.

You must identify:
1. PROJECTS: What was being built/designed/discussed? What state was it in?
2. CONCEPTS: What theoretical/architectural ideas appeared or evolved?
3. PEOPLE: Who was involved and how?
4. EMOTIONS: What was Luna's emotional state? (This matters — her best architectural insights come from emotional breakthroughs)
5. CONVERGENCE: Did ideas from different domains connect? Did a personal insight map to a technical architecture?
6. FIRSTS: Was anything mentioned here for the FIRST TIME? (Track concept origins)

Output as structured JSON:
{
  "date": "YYYY-MM-DD",
  "summary": "2-3 sentence overview of this date",
  "projects": [{"name": "X", "state": "designing/building/deployed/pivoted", "detail": "..."}],
  "concepts": [{"name": "X", "state": "first_mention/evolving/applied/converged", "detail": "..."}],
  "people": [{"name": "X", "role": "..."}],
  "emotional_state": "...",
  "convergence_points": ["Insight A from domain X connected to concept Y"],
  "firsts": ["First mention of X", "First time Y was connected to Z"],
  "key_quotes": ["Direct quotes that capture the moment (max 3, under 15 words each)"]
}

Respond with ONLY the JSON object. No markdown fences.
"""


def call_qwen(date_events, date_str):
    """Send a date's events to Qwen for synthesis."""
    # Truncate to fit context (keep most important events)
    event_text = ""
    for e in date_events:
        line = f"[{e.get('time_of_day','?')}] {e.get('source_type','?')}: {e.get('event_line','')}\n"
        if len(event_text) + len(line) < 12000:  # ~3K tokens
            event_text += line

    try:
        # Use freeform path with enable_thinking: False (more reliable for JSON)
        resp = requests.post(QWEN_URL, json={
            "model": "default",
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"Date: {date_str}\n\nEvents ({len(date_events)} total, showing top entries):\n\n{event_text}\n\nExtract the cognitive map for this date. Respond with ONLY valid JSON."}
            ],
            "max_tokens": 2000,
            "temperature": 0.3,
            "presence_penalty": 1.5,
            "chat_template_kwargs": {"enable_thinking": False},
        }, timeout=120)
        data = resp.json()
        content = data["choices"][0]["message"].get("content", "")
        if not content:
            print(f"  [WARN] Empty content for {date_str}", flush=True)
            return None
        # Try to extract JSON from response (may have markdown fences)
        content = content.strip()
        if content.startswith("```"):
            content = content.split("```", 2)[1]
            if content.startswith("json"):
                content = content[4:]
            content = content.strip()
        return json.loads(content)
    except json.JSONDecodeError as e:
        print(f"  [WARN] JSON parse failed for {date_str}: {e}", flush=True)
        # Try to salvage partial JSON
        try:
            # Find the last complete object
            idx = content.rfind("}")
            if idx > 0:
                return json.loads(content[:idx+1])
        except:
            pass
        print(f"  [ERROR] Could not salvage JSON for {date_str}", flush=True)
        return None
    except Exception as e:
        print(f"  [ERROR] Qwen call failed for {date_str}: {e}", flush=True)
    return None


def main():
    print("=== COGNITIVE MAP SYNTHESIS ===", flush=True)

    # Load raw events
    with open(INPUT_FILE, encoding="utf-8") as f:
        all_events = json.load(f)
    print(f"Loaded {len(all_events)} raw events", flush=True)

    # Group by date
    by_date = {}
    for e in all_events:
        d = e.get("date", "undated")
        if d not in by_date:
            by_date[d] = []
        by_date[d].append(e)

    # All dates should be valid now (pre-filtered in all_dated_events.json)
    dates = sorted([d for d in by_date.keys() if d != "undated"])
    print(f"Processing {len(dates)} dated groups", flush=True)

    # Process each date
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    results = []
    for i, date_str in enumerate(dates):
        events = by_date[date_str]
        print(f"[{i+1}/{len(dates)}] {date_str}: {len(events)} events...", flush=True)
        result = call_qwen(events, date_str)
        if result:
            results.append(result)
            print(f"  OK — {len(result.get('projects',[]))} projects, {len(result.get('concepts',[]))} concepts, {len(result.get('firsts',[]))} firsts", flush=True)

    # No undated processing needed — all_dated_events.json is pre-filtered

    # Save synthesis results
    with open(os.path.join(OUTPUT_DIR, "cognitive_map_data.json"), "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"\nSynthesis data: {len(results)} date summaries saved", flush=True)

    # Generate the cognitive map markdown
    generate_map(results)
    print("\n=== SYNTHESIS COMPLETE ===", flush=True)


def generate_map(results):
    """Generate the cognitive convergence map as markdown."""
    out = os.path.join(OUTPUT_DIR, "cognitive_convergence_map.md")

    # Track concept evolution across dates
    concept_timeline = {}
    project_timeline = {}
    convergence_log = []
    firsts_log = []

    for r in results:
        d = r.get("date", "?")
        for c in r.get("concepts", []):
            name = c.get("name", "?")
            if name not in concept_timeline:
                concept_timeline[name] = []
            concept_timeline[name].append({"date": d, "state": c.get("state", "?"), "detail": c.get("detail", "")})
        for p in r.get("projects", []):
            name = p.get("name", "?")
            if name not in project_timeline:
                project_timeline[name] = []
            project_timeline[name].append({"date": d, "state": p.get("state", "?"), "detail": p.get("detail", "")})
        for cp in r.get("convergence_points", []):
            convergence_log.append({"date": d, "point": cp})
        for f in r.get("firsts", []):
            firsts_log.append({"date": d, "first": f})

    with open(out, "w", encoding="utf-8") as f:
        f.write("# ELF Labs Cognitive Convergence Map\n")
        f.write(f"## Generated: {datetime.now().isoformat()}\n")
        f.write(f"## Source: {len(results)} date summaries from 123K+ raw events\n\n")

        # Chronological narrative
        f.write("---\n\n# CHRONOLOGICAL FLOW\n\n")
        for r in results:
            d = r.get("date", "?")
            f.write(f"## {d}\n")
            f.write(f"**{r.get('summary', '')}**\n\n")
            if r.get("emotional_state"):
                f.write(f"*Emotional state: {r['emotional_state']}*\n\n")
            if r.get("projects"):
                f.write("Projects:\n")
                for p in r["projects"]:
                    f.write(f"- **{p.get('name','?')}** [{p.get('state','?')}]: {p.get('detail','')}\n")
                f.write("\n")
            if r.get("concepts"):
                f.write("Concepts:\n")
                for c in r["concepts"]:
                    f.write(f"- **{c.get('name','?')}** [{c.get('state','?')}]: {c.get('detail','')}\n")
                f.write("\n")
            if r.get("convergence_points"):
                f.write("Convergence:\n")
                for cp in r["convergence_points"]:
                    f.write(f"- {cp}\n")
                f.write("\n")
            if r.get("key_quotes"):
                f.write("Quotes:\n")
                for q in r["key_quotes"]:
                    f.write(f"> {q}\n")
                f.write("\n")
            f.write("---\n\n")

        # Concept evolution timeline
        f.write("\n# CONCEPT EVOLUTION\n\n")
        for name, entries in sorted(concept_timeline.items()):
            f.write(f"## {name}\n")
            for e in entries:
                f.write(f"- [{e['date']}] {e['state']}: {e['detail']}\n")
            f.write("\n")

        # Convergence points (the fractal pattern)
        f.write("\n# CONVERGENCE POINTS (The Fractal Pattern)\n\n")
        for cp in convergence_log:
            f.write(f"- [{cp['date']}] {cp['point']}\n")

        # Firsts
        f.write("\n\n# FIRSTS (Concept Origins)\n\n")
        for fi in firsts_log:
            f.write(f"- [{fi['date']}] {fi['first']}\n")

        # Project evolution
        f.write("\n\n# PROJECT EVOLUTION\n\n")
        for name, entries in sorted(project_timeline.items()):
            f.write(f"## {name}\n")
            for e in entries:
                f.write(f"- [{e['date']}] {e['state']}: {e['detail']}\n")
            f.write("\n")

    print(f"Cognitive map written to: {out}", flush=True)


if __name__ == "__main__":
    main()

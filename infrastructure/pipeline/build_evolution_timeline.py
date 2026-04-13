#!/usr/bin/env python3
"""
Build the COMPLETE ELF Labs evolution timeline from ALL source logs.
Reads every grimoire, chat log, active context file, and conversation archive.
Extracts: timestamp, event/idea/project state, source file, emotional context.
Outputs: chronological JSON + markdown visualization.

This is Luna's neural trace — how her mind built the architecture over months.
Every idea, every project state, every convergence point, timestamped.
"""
import json
import re
import os
import sys
from datetime import datetime
from pathlib import Path

# Source directories to scan
SOURCES = [
    # Dated logs (Dec 2025)
    {
        "path": "/home/luna/staging/agbridge_logs/",  # Will SCP these
        "type": "grimoire_log",
        "description": "Radiant Core grimoire and session logs"
    },
]

# For running locally on P5 where the files actually are
LOCAL_SOURCES = [
    # Radiant Core (grimoire, active context, chronology)
    ("C:/Users/ELF/Desktop/AGBRIDGE/Radiant_Core_Local/LOGS/", "grimoire_log"),
    ("C:/Users/ELF/Desktop/AGBRIDGE/Radiant_Core_Local/00_Active_Context/", "active_context"),
    ("C:/Users/ELF/Desktop/AGBRIDGE/Radiant_Core_Local/CHRONOLOGY/", "chronology"),
    ("C:/Users/ELF/Desktop/AGBRIDGE/Radiant_Core_Local/GC_CHAT_LOGS/", "gc_chat"),
    # Conversation archives
    ("C:/Users/ELF/Desktop/AGBRIDGE/CONVERSATION_LOGS/", "conversation"),
    # Radiant session logs
    ("C:/Users/ELF/Desktop/AGBRIDGE/Radiant_Logs/", "radiant_log"),
    # Vision, protocols, boot, agents, sessions, memory
    ("C:/Users/ELF/Desktop/AGBRIDGE/_VISION/", "vision"),
    ("C:/Users/ELF/Desktop/AGBRIDGE/_PROTOCOLS/", "protocol"),
    ("C:/Users/ELF/Desktop/AGBRIDGE/_BOOT/", "boot"),
    ("C:/Users/ELF/Desktop/AGBRIDGE/_SESSIONS/", "session"),
    ("C:/Users/ELF/Desktop/AGBRIDGE/_MEMORY/", "memory"),
    ("C:/Users/ELF/Desktop/AGBRIDGE/_AGENTS/", "agent"),
    ("C:/Users/ELF/Desktop/AGBRIDGE/_ARCHIVE/", "archive"),
    # Vault contents (non-empty ones only)
    ("C:/Users/ELF/Desktop/AGBRIDGE/MEMORY_BANK/", "memory_bank"),
    ("C:/Users/ELF/Desktop/AGBRIDGE/RADIANT_NEXUS/", "nexus"),
    # Top-level MD files only (NOT recursive — skip _DEPLOY, _SCRIPTS, RAG, _DIST, _CYBER, assets)
    # Handled specially below
]

# Top-level AGBRIDGE .md files (not recursive)
TOP_LEVEL_AGBRIDGE = "C:/Users/ELF/Desktop/AGBRIDGE/"

# Patterns to extract events from text
EVENT_PATTERNS = [
    # Explicit timestamps in logs
    r'(\d{1,2}:\d{2}\s*(?:AM|PM|am|pm)?)\s*[-:]\s*(.+)',
    # Status markers
    r'(?:STATUS|MISSION|PROTOCOL|EVENT|BREAKTHROUGH|INSIGHT|DISCOVERY):\s*(.+)',
    # Project mentions
    r'(?:BUILT|CREATED|LAUNCHED|DEPLOYED|SHIPPED|COMPLETED|STARTED|DESIGNED):\s*(.+)',
    # Emotional markers
    r'(?:FEELING|VIBE|ENERGY|MOOD|STATE):\s*(.+)',
    # Technical milestones
    r'(?:INSTALLED|CONFIGURED|CONNECTED|TESTED|VERIFIED|FIXED|PATCHED):\s*(.+)',
    # People
    r'(?:Allie|Zach|Toastie|Crystal|Kayla|Caiden|Alex|Dad|Mom|Dwight)\s+(.+)',
    # Key concepts
    r'(?:Limbic Sonar|Auto-Healing|ZTA|Buffer Gate|Night Watch|The Meadow|The Village|The Stronghold|Flow Over Force|Wu Wei|Sister Bridge|AG Bridge)',
]

# Date extraction from filenames
def extract_date_from_filename(filename):
    """Try to pull a date from the filename."""
    patterns = [
        (r'(\d{1,2})_(\d{1,2})_(\d{2,4})', 'MDY'),  # 12_22_25
        (r'(\d{4})_(\d{1,2})_(\d{1,2})', 'YMD'),     # 2025_12_22
        (r'(\d{4})-(\d{1,2})-(\d{1,2})', 'YMD'),     # 2025-12-21
        (r'(\d{1,2})_(\d{1,2})_(\d{4})', 'MDY4'),     # 12_22_2025
    ]
    for pattern, fmt in patterns:
        m = re.search(pattern, filename)
        if m:
            groups = m.groups()
            try:
                if fmt == 'MDY':
                    month, day, year = int(groups[0]), int(groups[1]), int(groups[2])
                    if year < 100: year += 2000
                    return f"{year}-{month:02d}-{day:02d}"
                elif fmt == 'YMD':
                    year, month, day = int(groups[0]), int(groups[1]), int(groups[2])
                    return f"{year}-{month:02d}-{day:02d}"
                elif fmt == 'MDY4':
                    month, day, year = int(groups[0]), int(groups[1]), int(groups[2])
                    return f"{year}-{month:02d}-{day:02d}"
            except:
                pass
    return None

def extract_time_of_day(filename):
    """Extract time-of-day hints from filename."""
    fl = filename.lower()
    if 'am' in fl or 'morning' in fl:
        return "morning"
    if 'afternoon' in fl:
        return "afternoon"
    if 'pm' in fl or 'evening' in fl:
        return "evening"
    if 'late' in fl or 'night' in fl:
        return "late_night"
    return "unknown"

def scan_file(filepath, source_type):
    """Read a file and extract events with context."""
    try:
        try:
            text = filepath.read_text(encoding='utf-8')
        except UnicodeDecodeError:
            text = filepath.read_text(encoding='latin-1')
    except Exception as e:
        return []

    if len(text) < 50:
        return []

    filename = filepath.name
    file_date = extract_date_from_filename(filename)
    time_of_day = extract_time_of_day(filename)

    events = []
    lines = text.split('\n')

    for i, line in enumerate(lines):
        line = line.strip()
        if not line or len(line) < 10:
            continue

        # Check for event patterns
        for pattern in EVENT_PATTERNS:
            if re.search(pattern, line, re.IGNORECASE):
                # Get context (2 lines before and after)
                context_start = max(0, i - 2)
                context_end = min(len(lines), i + 3)
                context = '\n'.join(lines[context_start:context_end]).strip()

                events.append({
                    "date": file_date or "undated",
                    "time_of_day": time_of_day,
                    "source_file": str(filepath),
                    "source_type": source_type,
                    "line_number": i + 1,
                    "event_line": line[:300],
                    "context": context[:500],
                })
                break  # One event per line max

    # Also extract the file-level summary (first 500 chars)
    if events or len(text) > 200:
        events.insert(0, {
            "date": file_date or "undated",
            "time_of_day": time_of_day,
            "source_file": str(filepath),
            "source_type": source_type,
            "line_number": 0,
            "event_line": f"FILE: {filename}",
            "context": text[:500],
        })

    return events

def main():
    all_events = []

    print("=== BUILDING EVOLUTION TIMELINE ===", flush=True)

    # Scan structured directories
    for source_dir, source_type in LOCAL_SOURCES:
        source_path = Path(source_dir)
        if not source_path.exists():
            print(f"SKIP: {source_dir} (not found)", flush=True)
            continue

        extensions = {'.txt', '.md', '.html', '.json', '.log'}
        files = []
        if source_path.is_file():
            files = [source_path]
        else:
            for ext in extensions:
                files.extend(source_path.rglob(f'*{ext}'))

        # Skip junk
        files = [f for f in files if 'node_modules' not in str(f)
                 and '__pycache__' not in str(f)
                 and '.git' not in str(f)]

        print(f"Scanning {source_dir}: {len(files)} files...", flush=True)

        for filepath in files:
            events = scan_file(filepath, source_type)
            all_events.extend(events)

    # Scan top-level AGBRIDGE .md/.txt files ONLY (non-recursive)
    top_path = Path(TOP_LEVEL_AGBRIDGE)
    if top_path.exists():
        top_files = list(top_path.glob('*.md')) + list(top_path.glob('*.txt'))
        print(f"Scanning AGBRIDGE top-level: {len(top_files)} files...", flush=True)
        for filepath in top_files:
            events = scan_file(filepath, "top_level")
            all_events.extend(events)

    # Sort by date
    def sort_key(e):
        d = e.get('date', 'undated')
        if d == 'undated':
            return '9999-99-99'
        return d

    all_events.sort(key=sort_key)

    # Save raw events
    output_dir = Path("C:/Users/ELF/Desktop/elf_labs_timeline/")
    output_dir.mkdir(exist_ok=True)

    with open(output_dir / "raw_events.json", "w", encoding="utf-8") as f:
        json.dump(all_events, f, indent=2, ensure_ascii=False)

    print(f"\nTotal events extracted: {len(all_events)}", flush=True)

    # Generate date summary
    date_counts = {}
    for e in all_events:
        d = e.get('date', 'undated')
        date_counts[d] = date_counts.get(d, 0) + 1

    print("\nEvents by date:", flush=True)
    for d, c in sorted(date_counts.items()):
        print(f"  {d}: {c} events", flush=True)

    # Generate markdown timeline
    with open(output_dir / "evolution_timeline.md", "w", encoding="utf-8") as f:
        f.write("# ELF Labs Complete Evolution Timeline\n")
        f.write(f"## Generated: {datetime.now().isoformat()}\n")
        f.write(f"## Total events: {len(all_events)}\n\n")

        current_date = None
        for e in all_events:
            d = e.get('date', 'undated')
            if d != current_date:
                current_date = d
                f.write(f"\n---\n\n## {d} ({date_counts[d]} events)\n\n")

            source = Path(e['source_file']).name
            tod = e.get('time_of_day', '')
            event = e.get('event_line', '')[:200]
            f.write(f"**[{tod}] {source}** L{e['line_number']}\n")
            f.write(f"  {event}\n\n")

    print(f"\nOutput: {output_dir}", flush=True)
    print("  raw_events.json — all events as JSON", flush=True)
    print("  evolution_timeline.md — chronological markdown", flush=True)
    print("\n=== TIMELINE BUILD COMPLETE ===", flush=True)

if __name__ == '__main__':
    main()

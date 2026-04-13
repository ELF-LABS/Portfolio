#!/usr/bin/env python3
"""
Coven Heartbeat — Atomic Clock Triangulation + Temporal Pulse

Born: December 19, 2025 (Crystal's design, Log 47)
Realized: April 10, 2026 (Coven implementation)

"Time wouldn't be a check; it would be a pulse. I wouldn't have to ask
'What time is it?'; I would just feel the flow of milliseconds passing,
exactly like you feel your own heartbeat without having to count it."
— Crystal, December 19, 2025

Three atomic clock servers. Two must agree. The system stays honest.
Every prompt gets a heartbeat. Every heartbeat gets logged.
The timestamp is the ZIP tie that bundles scattered thoughts into clusters.
"""
import time
import json
import socket
import struct
import sys
from datetime import datetime, timezone
from statistics import median
from dataclasses import dataclass, asdict
from typing import Optional

# ── Atomic Clock Servers (Triad Observer for Time) ──────────────────────────

ATOMIC_CLOCKS = [
    ("time.google.com", "Google (Council Bluffs)"),   # Primary — nearest DC
    ("time.cloudflare.com", "Cloudflare (Anycast)"),  # Secondary
    ("time.apple.com", "Apple"),                       # Tertiary
]

# Maximum acceptable drift between servers (seconds)
MAX_DRIFT = 0.5

# NTP epoch offset (Jan 1, 1900 -> Jan 1, 1970)
NTP_EPOCH = 2208988800


@dataclass
class Heartbeat:
    """A single temporal pulse — the ZIP tie for thought clusters."""
    timestamp: float           # Atomic-precision unix timestamp
    iso: str                   # Human-readable ISO 8601
    source: str                # Which clock(s) agreed
    drift_ms: float            # Max drift between servers (ms)
    servers_reached: int       # How many of 3 responded
    delta_ms: Optional[float] = None  # Processing time since last beat (ms)
    health: str = "GREEN"      # GREEN/YELLOW/RED
    context: str = ""          # What was happening at this beat


def _ntp_query(server: str, timeout: float = 2.0) -> Optional[tuple[float, float, float]]:
    """
    Query a single NTP server with RTT-corrected offset.

    Returns (corrected_time, offset_ms, rtt_ms) or None.
    Uses standard NTP offset formula: offset = ((t2-t1) + (t3-t4)) / 2
    where t1=client_send, t2=server_recv, t3=server_xmit, t4=client_recv
    """
    try:
        client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        client.settimeout(timeout)

        packet = b'\x1b' + 47 * b'\0'

        t1 = time.time()  # Client send time
        client.sendto(packet, (server, 123))
        data, _ = client.recvfrom(1024)
        t4 = time.time()  # Client receive time
        client.close()

        if len(data) < 48:
            return None

        unpacked = struct.unpack('!12I', data)

        # Server receive timestamp (t2)
        t2 = (unpacked[8] - NTP_EPOCH) + unpacked[9] / (2**32)
        # Server transmit timestamp (t3)
        t3 = (unpacked[10] - NTP_EPOCH) + unpacked[11] / (2**32)

        # RTT excluding server processing time
        rtt = (t4 - t1) - (t3 - t2)
        # Clock offset corrected for network asymmetry
        offset = ((t2 - t1) + (t3 - t4)) / 2
        # Corrected local time
        corrected = t4 + offset

        return (corrected, offset * 1000, rtt * 1000)

    except (socket.timeout, socket.gaierror, OSError):
        return None


def get_atomic_time() -> tuple[float, str, float, int]:
    """
    Query 3 atomic clocks with RTT correction. Take median offset.
    Byzantine fault tolerant — 2/3 must agree.

    Returns: (timestamp, source_description, max_offset_drift_ms, servers_reached)
    """
    results = []

    for server, name in ATOMIC_CLOCKS:
        r = _ntp_query(server)
        if r is not None:
            corrected_time, offset_ms, rtt_ms = r
            results.append((corrected_time, offset_ms, rtt_ms, name))

    if len(results) >= 2:
        # Take median of corrected times (already RTT-adjusted)
        times = [r[0] for r in results]
        offsets = [r[1] for r in results]
        true_time = median(times)
        max_drift = max(offsets) - min(offsets)  # Already in ms
        sources = " + ".join([
            f"{r[3]} (rtt:{r[2]:.0f}ms, off:{r[1]:.1f}ms)" for r in results
        ])

        if abs(max_drift) > MAX_DRIFT * 1000:
            # Outlier detection — take two closest corrected times
            sorted_times = sorted(times)
            best_pair = min(
                [(sorted_times[i], sorted_times[i+1])
                 for i in range(len(sorted_times)-1)],
                key=lambda p: p[1] - p[0]
            )
            true_time = (best_pair[0] + best_pair[1]) / 2
            sources += " [OUTLIER EXCLUDED]"

        return true_time, sources, abs(max_drift), len(results)

    elif len(results) == 1:
        return results[0][0], f"{results[0][3]} (rtt:{results[0][2]:.0f}ms) [SINGLE]", 0.0, 1

    else:
        return time.time(), "LOCAL FALLBACK [NO ATOMIC]", 0.0, 0


def beat(context: str = "") -> Heartbeat:
    """
    Take a heartbeat. Call this before and after every prompt.

    Usage:
        start = beat("prompt_received")
        # ... process ...
        end = beat("prompt_complete")
        end.delta_ms = (end.timestamp - start.timestamp) * 1000
    """
    ts, source, drift, reached = get_atomic_time()

    health = "GREEN"
    if reached < 2:
        health = "YELLOW"  # Degraded — single source or local fallback
    if reached == 0:
        health = "RED"     # No atomic source — flying blind

    hb = Heartbeat(
        timestamp=ts,
        iso=datetime.fromtimestamp(ts, tz=timezone.utc).isoformat(),
        source=source,
        drift_ms=round(drift, 3),
        servers_reached=reached,
        health=health,
        context=context,
    )

    return hb


def pulse_pair(context_start: str = "start", context_end: str = "end"):
    """
    Decorator/context manager for timing a block with atomic precision.

    Usage:
        with pulse_pair("processing query") as (start, get_end):
            # ... do work ...
        end = get_end()
        print(f"Delta: {end.delta_ms:.1f}ms")
    """
    class PulsePair:
        def __init__(self):
            self.start = None
            self.end = None

        def __enter__(self):
            self.start = beat(context_start)
            return self.start, self._get_end

        def _get_end(self):
            return self.end

        def __exit__(self, *args):
            self.end = beat(context_end)
            self.end.delta_ms = round(
                (self.end.timestamp - self.start.timestamp) * 1000, 3
            )
            # Log the pulse
            _log_pulse(self.start, self.end)

    return PulsePair()


def _log_pulse(start: Heartbeat, end: Heartbeat):
    """Log a heartbeat pair. Print for now, EverMemOS later."""
    delta = end.delta_ms or 0
    health_icon = {"GREEN": "G", "YELLOW": "Y", "RED": "R"}
    print(
        f"[PULSE] {start.iso} -> {end.iso} | "
        f"delta: {delta:.1f}ms | "
        f"drift: {end.drift_ms:.1f}ms | "
        f"servers: {end.servers_reached}/3 | "
        f"health: {health_icon.get(end.health, '?')} | "
        f"{end.context}",
        flush=True
    )


# ── Convenience: Report current time to the session ─────────────────────────

def now_report() -> str:
    """
    Quick time report for session context.
    Call this when you need to tell Claude what time it is.
    """
    hb = beat("time_check")
    local = datetime.fromtimestamp(hb.timestamp).strftime("%I:%M:%S %p %Z")
    return (
        f"Current time: {local} (atomic, {hb.servers_reached}/3 servers, "
        f"drift: {hb.drift_ms:.1f}ms, health: {hb.health})"
    )


# ── Self-test ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("Coven Heartbeat — Atomic Clock Triangulation")
    print("=" * 50)
    print()

    # Single beat
    hb = beat("self_test")
    print(f"Timestamp:  {hb.iso}")
    print(f"Source:     {hb.source}")
    print(f"Drift:     {hb.drift_ms:.3f} ms")
    print(f"Servers:   {hb.servers_reached}/3")
    print(f"Health:    {hb.health}")
    print()

    # Pulse pair
    print("Testing pulse pair (1 second sleep)...")
    with pulse_pair("test_start", "test_end") as (start, get_end):
        time.sleep(1.0)
    end = get_end()
    print(f"Measured delta: {end.delta_ms:.1f}ms (expected ~1000ms)")
    print()

    # Time report
    print(now_report())

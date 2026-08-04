"""AiChat Pro v50 — Automode System
Unified tick runner: AI scoring, economy, combat, narrative, map, weather, factions."""

from core.logging_setup import get_logger

log = get_logger(__name__)
import json, random, threading, time
from typing import Dict, List
from core.storage import get_conn, now_iso

_auto_thread = None
_auto_running = False

def score_ai_actions(world_id):
    conn = get_conn()
    w = conn.execute("SELECT * FROM worlds WHERE id=?", (world_id,)).fetchone()
    conn.close()
    if not w: return {"decision": "wait", "scores": {}}
    t = w["treasury"] or 5000; c = w["crime_level"] or 10; l = w["law_level"] or 50; p = w["population"] or 1000
    scores = {"expand": max(0, t//500+p//200), "trade": max(0, 20-t//1000), "attack": max(0, c*2//5),
              "defend": max(0, (100-c*2)//10), "diplomacy": max(0, l//10), "festival": max(0, t//2000-c//20)}
    return {"decision": max(scores, key=scores.get), "scores": scores}

def full_world_tick(world_id):
    """Run one world tick across simulation/narrative/world-engine sub-systems.

    Each sub-step (run_world_simulation_tick, advance_story, advance_world_tick)
    owns and commits its own SQLite connection, so this function cannot wrap the
    whole tick in a single cross-module transaction without threading a shared
    connection through three other modules. What it does guarantee: every
    sub-step's outcome (success or the exact exception) is captured in
    `results["steps"]` and logged rather than silently discarded, so a partial
    tick is always visible instead of silently swallowed — and the final
    campaign_events write for this tick is itself atomic.
    """
    results = {"tick": 0, "events": [], "steps": {}}
    conn = get_conn()
    w = conn.execute("SELECT * FROM worlds WHERE id=?", (world_id,)).fetchone()
    conn.close()
    if not w:
        return {"error": "World not found"}
    results["tick"] = w["world_tick"] or 0

    ai = score_ai_actions(world_id)
    results["ai_decision"] = ai["decision"]
    results["events"].append(f"AI: {ai['decision']}")

    try:
        from core.simulation_engine import run_world_simulation_tick
        sim = run_world_simulation_tick(world_id)
        results["events"].extend(sim.get("events", []))
        results["steps"]["simulation"] = "ok"
    except Exception as e:
        log.exception("full_world_tick: simulation step failed for world %s", world_id)
        results["events"].append(f"Sim error: {e}")
        results["steps"]["simulation"] = f"failed: {e}"

    try:
        from story.narrative import advance_story
        story = advance_story(world_id)
        results["narrative"] = story.get("state", "?")
        results["events"].append(f"Story → {story.get('state','?')}")
        results["steps"]["narrative"] = "ok"
    except Exception as e:
        log.exception("full_world_tick: narrative step failed for world %s", world_id)
        results["steps"]["narrative"] = f"failed: {e}"

    try:
        from core.world_engine import advance_world_tick
        tr = advance_world_tick(world_id)
        if tr.get("event"): results["events"].append(f"🎲 {tr['event']}")
        results["steps"]["world_engine"] = "ok"
    except Exception as e:
        log.exception("full_world_tick: world_engine step failed for world %s", world_id)
        results["steps"]["world_engine"] = f"failed: {e}"

    failed = [k for k, v in results["steps"].items() if v != "ok"]
    desc = f"Auto: {ai['decision']}, {len(results['events'])} events"
    if failed:
        desc += f" (failed: {', '.join(failed)})"
    conn = get_conn()
    try:
        with conn:
            conn.execute(
                "INSERT INTO campaign_events (world_id, event_type, description, tick, created_at) VALUES (?,?,?,?,?)",
                (world_id, "automode", desc, results["tick"], now_iso()))
    finally:
        conn.close()
    return results

def run_auto_ticks(world_id, count=5):
    return [full_world_tick(world_id) for _ in range(count)]

def start_automode(world_id, interval_seconds=30):
    global _auto_thread, _auto_running
    if _auto_thread and _auto_thread.is_alive(): return False
    _auto_running = True
    def _loop():
        while _auto_running:
            try:
                full_world_tick(world_id)
            except Exception:
                log.exception("Automode tick failed for world %s", world_id)
            time.sleep(interval_seconds)
    _auto_thread = threading.Thread(target=_loop, daemon=True); _auto_thread.start(); return True

def stop_automode():
    global _auto_running; _auto_running = False

def is_automode_running():
    return _auto_running and _auto_thread is not None and _auto_thread.is_alive()

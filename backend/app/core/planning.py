"""
AiChat Pro — Planning & Automation
AI planning engine, workflow engine, suggestion engine, task scheduler.
"""
from __future__ import annotations
import json
import random
from datetime import datetime
from typing import List, Dict, Optional
from core.storage import get_conn, now_iso


class PlanningEngine:
    def __init__(self):
        self.goals: List[Dict] = []

    def add_goal(self, goal: str, priority: int = 1):
        self.goals.append({"goal": goal, "priority": priority,
                           "created": now_iso()})

    def get_next(self) -> Optional[Dict]:
        if not self.goals:
            return None
        return sorted(self.goals, key=lambda g: g["priority"], reverse=True)[0]

    def remove_goal(self, goal: str):
        self.goals = [g for g in self.goals if g["goal"] != goal]


class WorkflowEngine:
    PRESET_STEPS = ["Backup system", "Clean memory", "Optimise performance",
                    "Sync data", "Generate report", "Run safety scan",
                    "Index knowledge", "Prune old messages"]

    def save_workflow(self, name: str, steps: List[str]):
        conn = get_conn()
        conn.execute(
            "INSERT OR REPLACE INTO workflows (name, steps_json, created_at) VALUES (?,?,?)",
            (name, json.dumps(steps), now_iso()))
        conn.commit()
        conn.close()

    def run_workflow(self, name: str) -> List[str]:
        conn = get_conn()
        row = conn.execute("SELECT steps_json FROM workflows WHERE name=?", (name,)).fetchone()
        conn.close()
        if not row:
            return [f"Workflow '{name}' not found"]
        steps = json.loads(row["steps_json"])
        return [f"Executed: {s}" for s in steps]

    def list_workflows(self) -> List[Dict]:
        conn = get_conn()
        rows = conn.execute("SELECT name, steps_json, created_at FROM workflows ORDER BY id DESC").fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def delete_workflow(self, name: str):
        conn = get_conn()
        conn.execute("DELETE FROM workflows WHERE name=?", (name,))
        conn.commit()
        conn.close()

    def random_workflow(self) -> Dict:
        steps = random.sample(self.PRESET_STEPS, min(4, len(self.PRESET_STEPS)))
        name = f"Auto_{datetime.now().strftime('%H%M%S')}"
        return {"name": name, "steps": steps}


class SuggestionEngine:
    def suggest(self, history: List[str]) -> List[str]:
        if not history:
            return ["Start a conversation", "Create a character", "Build a world"]
        last = history[-1][:50]
        return [
            f"Continue discussing: {last}",
            "Generate a report", "Create new scenario",
            "Start simulation", "Review memory",
            "Optimise performance"]


planning_engine = PlanningEngine()
workflow_engine = WorkflowEngine()
suggestion_engine = SuggestionEngine()

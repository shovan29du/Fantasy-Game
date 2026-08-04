"""
AiChat Pro — Safety Monitor
Real-time risk detection for system health and behavioral drift.
"""
from __future__ import annotations
from datetime import datetime
from typing import List, Dict

try:
    import psutil
except ImportError:
    psutil = None

try:
    import GPUtil
except ImportError:
    GPUtil = None


class SafetyMonitor:
    def __init__(self):
        self.risk_log: List[Dict] = []
        self.thresholds = {
            "cpu": 95, "ram": 90, "disk": 95,
            "trust_drop": 20, "personality_instability": 25
        }

    def system_snapshot(self) -> Dict:
        cpu = psutil.cpu_percent(interval=0.5) if psutil else 0
        ram = psutil.virtual_memory().percent if psutil else 0
        disk = psutil.disk_usage("/").percent if psutil else 0
        gpu = 0
        if GPUtil:
            gpus = GPUtil.getGPUs()
            if gpus:
                gpu = gpus[0].load * 100
        return {"cpu": round(cpu, 1), "ram": round(ram, 1),
                "disk": round(disk, 1), "gpu": round(gpu, 1)}

    def evaluate_system(self) -> List[str]:
        stats = self.system_snapshot()
        alerts = []
        if stats["cpu"] >= self.thresholds["cpu"]:
            alerts.append("Critical CPU load")
        if stats["ram"] >= self.thresholds["ram"]:
            alerts.append("High RAM usage")
        if stats["disk"] >= self.thresholds["disk"]:
            alerts.append("Disk nearly full")
        if alerts:
            self.risk_log.append({
                "time": datetime.now().isoformat(),
                "type": "system", "alerts": alerts})
        return alerts

    def evaluate_behavior(self, trust_delta: int = 0,
                          personality_shift: int = 0) -> List[str]:
        alerts = []
        if trust_delta <= -self.thresholds["trust_drop"]:
            alerts.append("Relationship instability detected")
        if personality_shift >= self.thresholds["personality_instability"]:
            alerts.append("Personality drift risk")
        if alerts:
            self.risk_log.append({
                "time": datetime.now().isoformat(),
                "type": "behavior", "alerts": alerts})
        return alerts

    def detect_gpu_profile(self) -> str:
        if not GPUtil:
            return "CPU-only"
        gpus = GPUtil.getGPUs()
        if not gpus:
            return "CPU-only"
        mem = gpus[0].memoryTotal
        if mem < 2048: return "Potato"
        if mem < 4096: return "Low"
        if mem < 8192: return "Medium"
        if mem < 12288: return "High"
        return "Ultra"

    def health_alerts(self) -> List[str]:
        return self.evaluate_system()

    def recent_risks(self, limit: int = 20) -> List[Dict]:
        return self.risk_log[-limit:]


safety_monitor = SafetyMonitor()

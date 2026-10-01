from __future__ import annotations

import json, os, shutil, subprocess
from pathlib import Path
import requests
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router=APIRouter(prefix="/services",tags=["local services"])
ROOT=Path(__file__).resolve().parent.parent
RECOMMENDED=[{"name":"qwen2.5:3b","role":"writing and notes"},{"name":"qwen2.5vl:3b","role":"frames, charts and formulas"}]

class ModelAction(BaseModel):
    name:str

def ollama_path():
    found=shutil.which("ollama.exe" if os.name=="nt" else "ollama")
    candidate=Path(os.getenv("LOCALAPPDATA",""))/"Programs/Ollama/ollama.exe"
    return found or (str(candidate) if candidate.exists() else None)

@router.get("/status")
def status():
    models=[]
    try:
        data=requests.get("http://127.0.0.1:11434/api/tags",timeout=2).json()
        models=[{"name":x.get("name"),"size":x.get("size",0),"modified":x.get("modified_at","")} for x in data.get("models",[])]
    except Exception: pass
    comfy=(ROOT/"engines/ComfyUI/main.py").exists()
    usage=shutil.disk_usage(ROOT)
    return {"ollama":bool(ollama_path()),"ollama_running":bool(models),"comfyui_installed":comfy,"ocr":bool(shutil.which("tesseract")),"models":models,"recommended":RECOMMENDED,"disk_free_gb":round(usage.free/1024**3,1),"disk_total_gb":round(usage.total/1024**3,1)}

@router.post("/models/pull")
def pull(body:ModelAction):
    exe=ollama_path()
    if not exe: raise HTTPException(503,"Ollama is not installed")
    if not any(body.name==x["name"] for x in RECOMMENDED): raise HTTPException(400,"Model is not in the approved local catalogue")
    try: subprocess.run([exe,"pull",body.name],check=True,timeout=7200)
    except Exception as exc: raise HTTPException(500,f"Model install failed: {exc}")
    return {"ok":True,"name":body.name}

@router.post("/models/remove")
def remove(body:ModelAction):
    exe=ollama_path()
    if not exe: raise HTTPException(503,"Ollama is not installed")
    subprocess.run([exe,"rm",body.name],check=True,timeout=120)
    return {"ok":True,"name":body.name}

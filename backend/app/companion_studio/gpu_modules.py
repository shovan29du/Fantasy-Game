from __future__ import annotations

import base64, json, os, shutil, subprocess, tempfile, time
from pathlib import Path
from typing import Any

import requests
from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse

router = APIRouter(prefix="/gpu", tags=["optional local GPU modules"])
ROOT = Path(__file__).resolve().parent
WORKFLOWS = ROOT / "workflows"
OUTPUTS = ROOT / "outputs" / "gpu"
OUTPUTS.mkdir(parents=True, exist_ok=True)

SERVICES = {
    "comfyui": os.getenv("COMFYUI_URL", "http://127.0.0.1:8188"),
    "liveportrait": os.getenv("LIVEPORTRAIT_URL", "http://127.0.0.1:8890"),
    "xtts": os.getenv("XTTS_URL", "http://127.0.0.1:8020"),
    "ollama": os.getenv("OLLAMA_URL", "http://127.0.0.1:11434"),
    "stable_diffusion": os.getenv("STABLE_DIFFUSION_URL", "http://127.0.0.1:7860"),
}

TASKS = {
    "text_to_image": {"label":"Text to image", "engine":"stable_diffusion", "vram":4, "consent":False},
    "chat_to_image": {"label":"Chat to image", "engine":"stable_diffusion", "vram":4, "consent":False},
    "text_to_video": {"label":"Text-to-video model packs", "engine":"comfyui", "vram":8, "consent":False},
    "controlled_video": {"label":"Pose / edge controlled video", "engine":"comfyui", "vram":8, "consent":True},
    "video_description": {"label":"Video description & captions", "engine":"ollama", "vram":4, "consent":False},
    "video_finetune": {"label":"One-shot / LoRA video tuning", "engine":"comfyui", "vram":12, "consent":True},
    "clip_ideation": {"label":"CLIP-guided visual ideation", "engine":"comfyui", "vram":4, "consent":False},
    "image_to_video": {"label":"Local image-to-video", "engine":"comfyui", "vram":8, "consent":False},
    "talking_presenter": {"label":"Talking product presenter", "engine":"liveportrait", "vram":8, "consent":True},
    "ugc_avatar": {"label":"AI UGC avatar", "engine":"comfyui", "vram":12, "consent":True},
    "lip_sync": {"label":"Multilingual lip-sync", "engine":"comfyui", "vram":8, "consent":True},
    "product_placement": {"label":"Generated product placement", "engine":"comfyui", "vram":12, "consent":False},
    "motion_transfer": {"label":"Motion transfer", "engine":"comfyui", "vram":12, "consent":True},
    "voice_clone": {"label":"Consent-based voice cloning", "engine":"xtts", "vram":4, "consent":True},
    "generative_broll": {"label":"Generative B-roll", "engine":"comfyui", "vram":10, "consent":False},
    "localize": {"label":"Automatic advert localisation", "engine":"ollama", "vram":4, "consent":False},
}

def alive(url: str, path: str = "/"):
    try: return requests.get(url + path, timeout=1.5).status_code < 500
    except Exception: return False

def gpu_info():
    tool = shutil.which("nvidia-smi")
    if not tool: return {"available":False,"name":"No NVIDIA GPU detected","vram_gb":0}
    try:
        raw=subprocess.check_output([tool,"--query-gpu=name,memory.total,driver_version","--format=csv,noheader,nounits"],text=True,timeout=4).strip().splitlines()[0]
        name,memory,driver=[x.strip() for x in raw.split(",",2)]
        return {"available":True,"name":name,"vram_gb":round(float(memory)/1024,1),"driver":driver}
    except Exception: return {"available":False,"name":"GPU detection failed","vram_gb":0}

@router.get("/modules")
def modules():
    gpu=gpu_info()
    status={
        "comfyui":alive(SERVICES["comfyui"],"/system_stats"),
        "liveportrait":alive(SERVICES["liveportrait"]),
        "xtts":alive(SERVICES["xtts"],"/docs"),
        "ollama":alive(SERVICES["ollama"],"/api/tags"),
        "stable_diffusion":alive(SERVICES["stable_diffusion"],"/sdapi/v1/sd-models"),
    }
    tasks=[]
    for key,item in TASKS.items():
        workflow=(WORKFLOWS/f"{key}.json").exists()
        tasks.append({"id":key,**item,"service_ready":status[item["engine"]],"workflow_ready":workflow if item["engine"]=="comfyui" else True,"hardware_ready":gpu["vram_gb"]>=item["vram"]})
    return {"gpu":gpu,"services":status,"tasks":tasks,"endpoints":SERVICES}

@router.get("/research-packs")
def research_packs():
    catalog=ROOT/"optional_engines"/"catalog.json"; installed=ROOT/"optional_research"/"installed.json"
    data=json.loads(catalog.read_text(encoding="utf-8")) if catalog.exists() else {"packs":[]}
    active=set(json.loads(installed.read_text(encoding="utf-8")).get("packs",[])) if installed.exists() else set()
    return {"packs":[{**pack,"imported":pack["id"] in active} for pack in data["packs"]]}

def save_upload(upload: UploadFile | None, folder: Path, name: str):
    if not upload: return None
    suffix=Path(upload.filename or "asset.bin").suffix; path=folder/f"{name}{suffix}"; path.write_bytes(upload.file.read()); return path

def replace_tokens(value: Any, tokens: dict[str,str]):
    if isinstance(value,dict): return {k:replace_tokens(v,tokens) for k,v in value.items()}
    if isinstance(value,list): return [replace_tokens(v,tokens) for v in value]
    if isinstance(value,str):
        for key,replacement in tokens.items(): value=value.replace("{{"+key+"}}",replacement)
    return value

def comfy_upload(path: Path | None):
    if not path: return ""
    with path.open("rb") as handle:
        response=requests.post(SERVICES["comfyui"]+"/upload/image",files={"image":(path.name,handle)},data={"overwrite":"true"},timeout=60)
    response.raise_for_status(); return response.json().get("name",path.name)

def run_comfy(task: str, prompt: str, image: Path | None, video: Path | None):
    workflow_path=WORKFLOWS/f"{task}.json"
    if not workflow_path.exists(): raise HTTPException(503,f"Add an API-format ComfyUI workflow at local_api/workflows/{task}.json. Use {{{{prompt}}}}, {{{{image}}}} and {{{{video}}}} placeholders.")
    workflow=json.loads(workflow_path.read_text(encoding="utf-8")); tokens={"prompt":prompt,"image":comfy_upload(image),"video":comfy_upload(video)}; workflow=replace_tokens(workflow,tokens)
    queued=requests.post(SERVICES["comfyui"]+"/prompt",json={"prompt":workflow},timeout=30); queued.raise_for_status(); prompt_id=queued.json()["prompt_id"]
    for _ in range(900):
        history=requests.get(SERVICES["comfyui"]+f"/history/{prompt_id}",timeout=20).json()
        if prompt_id in history:
            outputs=[]
            for node in history[prompt_id].get("outputs",{}).values():
                outputs += node.get("images",[]) + node.get("gifs",[]) + node.get("videos",[])
            if not outputs: raise HTTPException(500,"The ComfyUI job finished without a downloadable output")
            item=outputs[0]; params={"filename":item["filename"],"subfolder":item.get("subfolder",""),"type":item.get("type","output")}; data=requests.get(SERVICES["comfyui"]+"/view",params=params,timeout=120).content
            target=OUTPUTS/item["filename"]; target.write_bytes(data); return target
        time.sleep(1)
    raise HTTPException(504,"The local GPU job exceeded the 15-minute limit")

def generate_image(prompt: str, task: str):
    final_prompt=prompt
    if task=="chat_to_image" and alive(SERVICES["ollama"],"/api/tags"):
        instruction="Convert this conversation into one vivid, safe visual scene prompt. Preserve the characters, relationship, mood, setting and important objects. Do not include dialogue, captions or text in the image. Return only the image prompt:\n"+prompt
        try:
            response=requests.post(SERVICES["ollama"]+"/api/generate",json={"model":"qwen2.5:3b","prompt":instruction,"stream":False},timeout=180)
            response.raise_for_status(); final_prompt=response.json()["response"].strip()
        except requests.RequestException: pass
    payload={"prompt":final_prompt,"negative_prompt":"text, captions, watermark, logo, distorted anatomy, duplicate objects, low quality","width":768,"height":1024,"steps":28,"cfg_scale":7,"sampler_name":"DPM++ 2M Karras"}
    try:
        response=requests.post(SERVICES["stable_diffusion"]+"/sdapi/v1/txt2img",json=payload,timeout=600);response.raise_for_status()
        data=base64.b64decode(response.json()["images"][0].split(",")[-1]);target=OUTPUTS/f"{task}.png";target.write_bytes(data);return target,final_prompt
    except requests.RequestException:
        if alive(SERVICES["comfyui"],"/system_stats"): return run_comfy(task,final_prompt,None,None),final_prompt
        raise HTTPException(503,"Start Stable Diffusion WebUI/Forge with --api, or add a matching ComfyUI workflow")

@router.post("/run")
def run(module: str = Form(...), prompt: str = Form(""), target_language: str = Form("Spanish"), consent: bool = Form(False), image: UploadFile | None = File(None), audio: UploadFile | None = File(None), video: UploadFile | None = File(None)):
    task=TASKS.get(module)
    if not task: raise HTTPException(400,"Unknown GPU module")
    if task["consent"] and not consent: raise HTTPException(400,"Confirm that you own or have permission to use every depicted face, voice and motion reference")
    folder=Path(tempfile.mkdtemp(prefix="companion-gpu-"))
    try:
        image_path=save_upload(image,folder,"image"); audio_path=save_upload(audio,folder,"audio"); video_path=save_upload(video,folder,"video")
        if module in ("text_to_image","chat_to_image"):
            output,_final_prompt=generate_image(prompt,module);return FileResponse(output,filename=output.name)
        if task["engine"]=="comfyui": output=run_comfy(module,prompt,image_path,video_path); return FileResponse(output,filename=output.name)
        if module=="voice_clone":
            if not audio_path: raise HTTPException(400,"Add your consented voice reference")
            with audio_path.open("rb") as handle:
                result=requests.post(SERVICES["xtts"]+"/tts_to_audio/",files={"speaker_wav":handle},data={"text":prompt,"language":"en"},timeout=300)
            result.raise_for_status(); target=OUTPUTS/"cloned-voice.wav"; target.write_bytes(result.content); return FileResponse(target,filename=target.name)
        if module=="talking_presenter":
            if not image_path or not audio_path: raise HTTPException(400,"Add a consented presenter image and narration audio")
            with image_path.open("rb") as pic,audio_path.open("rb") as sound:
                result=requests.post(SERVICES["liveportrait"]+"/animate",files={"image":pic,"audio":sound},timeout=900)
            result.raise_for_status(); target=OUTPUTS/"talking-presenter.mp4"; target.write_bytes(result.content); return FileResponse(target,filename=target.name)
        if module=="video_description":
            if not video_path: raise HTTPException(400,"Add a reference video to describe")
            bundled=ROOT.parent/"node_modules"/"ffmpeg-static"/("ffmpeg.exe" if os.name=="nt" else "ffmpeg"); ffmpeg=shutil.which("ffmpeg") or (str(bundled) if bundled.exists() else None)
            if not ffmpeg: raise HTTPException(503,"FFmpeg is required")
            frame=folder/"representative-frame.jpg"; subprocess.run([ffmpeg,"-y","-ss","1","-i",str(video_path),"-frames:v","1",str(frame)],check=True,capture_output=True)
            request={"model":"qwen2.5vl:3b","prompt":prompt or "Describe this product video for an editor. Return a concise visual description, visible product details, actions, mood and suggested captions.","images":[base64.b64encode(frame.read_bytes()).decode()],"stream":False}
            response=requests.post(SERVICES["ollama"]+"/api/generate",json=request,timeout=300);response.raise_for_status();return {"description":response.json()["response"].strip()}
        if module=="localize":
            request={"model":"qwen2.5:3b","prompt":f"Translate this advert into {target_language}. Preserve product names, prices and claims exactly. Return only the translation:\n{prompt}","stream":False}
            response=requests.post(SERVICES["ollama"]+"/api/generate",json=request,timeout=180); response.raise_for_status(); return {"language":target_language,"translation":response.json()["response"].strip(),"next_step":"Generate narration with XTTS/Piper, then run the lip-sync module if needed."}
        raise HTTPException(501,"This module adapter is not configured")
    except requests.RequestException as exc: raise HTTPException(503,f"Local module service is unavailable: {exc}")
    finally: shutil.rmtree(folder,ignore_errors=True)

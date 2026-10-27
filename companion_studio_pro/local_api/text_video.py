"""Independent local adapter for the ModelScope text-to-video Diffusers model.

The optional model weights are CC-BY-NC-4.0 and are not bundled. This adapter
downloads them from Hugging Face only after the user explicitly starts a job.
"""
from __future__ import annotations

import gc, os, shutil, subprocess, tempfile
from pathlib import Path

from fastapi import APIRouter, Form, HTTPException
from fastapi.responses import FileResponse

router=APIRouter(prefix="/text-video",tags=["text to video"])
ROOT=Path(__file__).resolve().parent.parent
OUTPUTS=Path(__file__).resolve().parent/"outputs"/"text-video"
OUTPUTS.mkdir(parents=True,exist_ok=True)
MODEL_ID="damo-vilab/text-to-video-ms-1.7b"

def ffmpeg():
    bundled=ROOT/"node_modules/ffmpeg-static"/("ffmpeg.exe" if os.name=="nt" else "ffmpeg")
    return shutil.which("ffmpeg") or (str(bundled) if bundled.exists() else None)

@router.get("/status")
def status():
    try:
        import torch
        device="cuda" if torch.cuda.is_available() else "mps" if getattr(torch.backends,"mps",None) and torch.backends.mps.is_available() else "cpu"
        vram=round(torch.cuda.get_device_properties(0).total_memory/1024**3,1) if device=="cuda" else 0
        ready=True
    except Exception:device="unavailable";vram=0;ready=False
    return {"ready":ready,"device":device,"vram_gb":vram,"model":MODEL_ID,"license":"CC-BY-NC-4.0","commercial_use":False,"estimated_download_gb":15}

@router.post("/generate")
def generate(prompt:str=Form(...),negative_prompt:str=Form("blurry, distorted, watermark, text"),frames:int=Form(16),fps:int=Form(8),steps:int=Form(30),seed:int=Form(42),width:int=Form(384),height:int=Form(256),cpu_offload:bool=Form(True),attention_slicing:bool=Form(True),accept_noncommercial:bool=Form(False)):
    if not accept_noncommercial:raise HTTPException(400,"Confirm the model's CC-BY-NC-4.0 non-commercial licence first")
    if not prompt.strip():raise HTTPException(400,"Enter a prompt")
    frames=max(4,min(frames,64));fps=max(1,min(fps,30));steps=max(5,min(steps,80));width=max(128,min(width//8*8,768));height=max(128,min(height//8*8,768))
    try:
        import torch
        from diffusers import TextToVideoSDPipeline
        import imageio.v3 as iio
    except Exception as exc:raise HTTPException(503,f"Text-to-video dependencies are missing: {exc}")
    device="cuda" if torch.cuda.is_available() else "mps" if getattr(torch.backends,"mps",None) and torch.backends.mps.is_available() else "cpu"
    dtype=torch.float16 if device in ("cuda","mps") else torch.float32
    try:
        pipe=TextToVideoSDPipeline.from_pretrained(MODEL_ID,torch_dtype=dtype,variant="fp16" if dtype==torch.float16 else None)
        if device=="cuda" and cpu_offload:pipe.enable_model_cpu_offload()
        else:pipe=pipe.to(device)
        if attention_slicing:pipe.enable_attention_slicing()
        generator=torch.Generator(device="cpu").manual_seed(seed)
        result=pipe(prompt=prompt,negative_prompt=negative_prompt,num_frames=frames,num_inference_steps=steps,height=height,width=width,generator=generator)
        video=result.frames[0] if isinstance(result.frames,list) and result.frames and isinstance(result.frames[0],list) else result.frames
        temp=Path(tempfile.mkdtemp(prefix="modelscope-t2v-"));raw=temp/"raw.mp4";out=OUTPUTS/"generated-text-video.mp4"
        iio.imwrite(raw,video,fps=fps,codec="libx264")
        if ffmpeg():subprocess.run([ffmpeg(),"-y","-i",str(raw),"-pix_fmt","yuv420p","-movflags","+faststart",str(out)],check=True,capture_output=True)
        else:shutil.copy2(raw,out)
        shutil.rmtree(temp,ignore_errors=True)
        return FileResponse(out,media_type="video/mp4",filename="generated-text-video.mp4",headers={"X-Model-License":"CC-BY-NC-4.0","X-Seed":str(seed)})
    except Exception as exc:raise HTTPException(500,f"Local text-to-video generation failed: {exc}")
    finally:
        try:
            del pipe
            if torch.cuda.is_available():torch.cuda.empty_cache()
        except Exception:pass
        gc.collect()

from __future__ import annotations

import base64, io, json, os, re, shutil, subprocess, tempfile, urllib.parse, wave
from pathlib import Path
from typing import Any

import requests
from bs4 import BeautifulSoup
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from PIL import Image, ImageDraw, ImageFilter, ImageFont
from pydantic import BaseModel
from .gpu_modules import router as gpu_router
from .intelligence import router as intelligence_router
from .services import router as services_router
from .text_video import router as text_video_router

app = FastAPI(title="Companion Studio Local Engine", version="1.0")
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:5173", "http://127.0.0.1:5173"], allow_methods=["*"], allow_headers=["*"])
app.include_router(gpu_router)
app.include_router(intelligence_router)
app.include_router(services_router)
app.include_router(text_video_router)
ROOT = Path(__file__).resolve().parent
OUTPUTS = ROOT / "outputs"
OUTPUTS.mkdir(exist_ok=True)

def ffmpeg_path():
    bundled = ROOT.parent / "node_modules" / "ffmpeg-static" / ("ffmpeg.exe" if os.name == "nt" else "ffmpeg")
    return shutil.which("ffmpeg") or (str(bundled) if bundled.exists() else None)

class URLBody(BaseModel): url: str
class ScriptBody(BaseModel):
    name: str
    description: str = ""
    audience: str = "people who value quality and simplicity"
    tone: str = "warm, confident, conversational"
    model: str = "qwen2.5:3b"
class QueryBody(BaseModel): query: str
class GenerateBody(BaseModel): prompt: str; negative_prompt: str = "text, watermark, logo, distorted product"

def fetch(url: str, **kwargs):
    headers = {"User-Agent": "Mozilla/5.0 CompanionStudio/1.0", **kwargs.pop("headers", {})}
    return requests.get(url, headers=headers, timeout=20, **kwargs)

@app.get("/health")
def health():
    def live(url: str):
        try: return requests.get(url, timeout=1.2).ok
        except Exception: return False
    return {
        "ready": True,
        "ffmpeg": bool(ffmpeg_path()),
        "ollama": live("http://127.0.0.1:11434/api/tags"),
        "stable_diffusion": live("http://127.0.0.1:7860/sdapi/v1/sd-models"),
        "rembg": _has_module("rembg"),
        "whisper": _has_module("faster_whisper"),
        "tts": "windows-offline" if os.name == "nt" else ("piper" if shutil.which("piper") else "none"),
    }

def _has_module(name: str):
    try: __import__(name); return True
    except Exception: return False

@app.post("/extract")
def extract_product(body: URLBody):
    if not body.url.startswith(("http://", "https://")): raise HTTPException(400, "Enter a complete http(s) product URL")
    try:
        response = fetch(body.url); response.raise_for_status(); soup = BeautifulSoup(response.text, "html.parser")
    except Exception as exc: raise HTTPException(422, f"Could not read that page: {exc}")
    data: dict[str, Any] = {}
    for tag in soup.select('script[type="application/ld+json"]'):
        try:
            parsed = json.loads(tag.string or "null"); items = parsed if isinstance(parsed, list) else [parsed]
            for item in items:
                if isinstance(item, dict) and item.get("@type") in ("Product", ["Product"]): data = item; break
                if isinstance(item, dict) and "@graph" in item:
                    for node in item["@graph"]:
                        if isinstance(node, dict) and node.get("@type") == "Product": data = node; break
        except Exception: pass
        if data: break
    def meta(*keys):
        for key in keys:
            node = soup.find("meta", property=key) or soup.find("meta", attrs={"name": key})
            if node and node.get("content"): return node["content"].strip()
        return ""
    images = data.get("image", [])
    if isinstance(images, str): images = [images]
    if isinstance(images, dict): images = [images.get("url", "")]
    og = meta("og:image", "twitter:image"); images = [str(i) for i in images if i]
    if og and og not in images: images.insert(0, og)
    offers = data.get("offers", {}); offers = offers[0] if isinstance(offers, list) and offers else offers
    return {
        "name": data.get("name") or meta("og:title", "twitter:title") or (soup.title.string.strip() if soup.title and soup.title.string else "Untitled product"),
        "description": BeautifulSoup(str(data.get("description") or meta("og:description", "description")), "html.parser").get_text(" ", strip=True),
        "price": str(offers.get("price", "")) if isinstance(offers, dict) else "",
        "currency": offers.get("priceCurrency", "") if isinstance(offers, dict) else "",
        "brand": (data.get("brand", {}).get("name", "") if isinstance(data.get("brand"), dict) else str(data.get("brand", ""))),
        "images": images[:12], "source": body.url,
    }

@app.post("/scripts")
def scripts(body: ScriptBody):
    prompt = f'''Return ONLY valid JSON: an array of exactly 3 objects with keys title, hook, scenes, cta. scenes must be an array of exactly 4 short spoken lines. Write 15-second vertical product ad concepts. Product: {body.name}. Description: {body.description}. Audience: {body.audience}. Tone: {body.tone}. Avoid unsupported claims.'''
    try:
        result = requests.post("http://127.0.0.1:11434/api/generate", json={"model": body.model, "prompt": prompt, "stream": False, "format": "json"}, timeout=90)
        result.raise_for_status(); parsed = json.loads(result.json()["response"])
        if isinstance(parsed, dict): parsed = parsed.get("scripts", parsed.get("ads", []))
        if isinstance(parsed, list) and len(parsed) >= 3: return {"source": "ollama", "scripts": parsed[:3]}
    except Exception: pass
    name = body.name or "this product"; detail = body.description.split(".")[0][:110] or "made to make everyday life feel easier"
    fallback = [
        {"title":"Problem → relief","hook":f"Still looking for a simpler way?", "scenes":["Some everyday problems should not take all your energy.", f"Meet {name}.", detail + ".", "Make the next step the easy one."], "cta":"See what makes it different"},
        {"title":"Quiet product story","hook":f"A small upgrade can change the whole routine.", "scenes":["The best products fit naturally into your day.", f"That is the idea behind {name}.", detail + ".", "Thoughtful, useful, and ready when you are."], "cta":"Discover it today"},
        {"title":"Fast social proof","hook":f"Here is why {name} deserves a closer look.", "scenes":["Designed for real life, not just the product page.", detail + ".", "Simple to understand. Easy to remember.", "This could be the upgrade you were waiting for."], "cta":"Take a closer look"},
    ]
    return {"source": "built-in", "scripts": fallback}

@app.post("/stock")
def stock(body: QueryBody):
    params = {"action":"query", "generator":"search", "gsrsearch":body.query, "gsrnamespace":6, "gsrlimit":12, "prop":"imageinfo", "iiprop":"url|extmetadata", "iiurlwidth":1200, "format":"json", "origin":"*"}
    try:
        data = requests.get("https://commons.wikimedia.org/w/api.php", params=params, timeout=20).json()
        items=[]
        for page in data.get("query",{}).get("pages",{}).values():
            info=(page.get("imageinfo") or [{}])[0]; meta=info.get("extmetadata",{}); url=info.get("thumburl") or info.get("url")
            if url: items.append({"title":page.get("title","").replace("File:",""), "url":url, "page":info.get("descriptionurl", ""), "credit":BeautifulSoup(meta.get("Artist",{}).get("value","Wikimedia Commons"),"html.parser").get_text(" ",strip=True)})
        return {"items":items}
    except Exception as exc: raise HTTPException(502, f"Stock search failed: {exc}")

@app.post("/generate-image")
def generate_image(body: GenerateBody):
    try:
        result=requests.post("http://127.0.0.1:7860/sdapi/v1/txt2img",json={"prompt":body.prompt,"negative_prompt":body.negative_prompt,"width":768,"height":1024,"steps":24,"cfg_scale":7},timeout=180)
        result.raise_for_status(); return {"image":"data:image/png;base64,"+result.json()["images"][0]}
    except Exception: raise HTTPException(503, "Start a local AUTOMATIC1111/Forge Stable Diffusion server with --api first")

@app.post("/remove-background")
async def remove_background(file: UploadFile = File(...)):
    if not _has_module("rembg"): raise HTTPException(503, "Install optional package: pip install rembg onnxruntime")
    from rembg import remove
    raw=await file.read(); result=remove(raw); return {"image":"data:image/png;base64,"+base64.b64encode(result).decode()}

@app.post("/transcribe")
async def transcribe(file: UploadFile = File(...)):
    if not _has_module("faster_whisper"): raise HTTPException(503, "Install optional package: pip install faster-whisper")
    from faster_whisper import WhisperModel
    suffix=Path(file.filename or "media.mp4").suffix; path=Path(tempfile.mkstemp(suffix=suffix)[1])
    try:
        path.write_bytes(await file.read()); model=WhisperModel("small",device="cpu",compute_type="int8")
        segments,_=model.transcribe(str(path),vad_filter=True); items=[{"start":s.start,"end":s.end,"text":s.text.strip()} for s in segments]
        return {"text":" ".join(x["text"] for x in items),"segments":items}
    finally: path.unlink(missing_ok=True)

def font(size: int, bold=False):
    paths = [Path(os.environ.get("WINDIR","C:/Windows"))/"Fonts"/("arialbd.ttf" if bold else "arial.ttf"), Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")]
    for path in paths:
        if path.exists(): return ImageFont.truetype(str(path), size)
    return ImageFont.load_default()

def download_image(source: str) -> Image.Image:
    if source.startswith("data:image"):
        return Image.open(io.BytesIO(base64.b64decode(source.split(",",1)[1]))).convert("RGB")
    return Image.open(io.BytesIO(fetch(source).content)).convert("RGB")

def speak(text: str, output: Path):
    if shutil.which("piper"):
        subprocess.run(["piper","--output_file",str(output)],input=text.encode(),check=True)
    elif os.name == "nt":
        safe=text.replace("'","''"); out=str(output).replace("'","''")
        cmd=f"Add-Type -AssemblyName System.Speech; $s=New-Object System.Speech.Synthesis.SpeechSynthesizer; $s.SetOutputToWaveFile('{out}'); $s.Speak('{safe}'); $s.Dispose()"
        subprocess.run(["powershell","-NoProfile","-Command",cmd],check=True,capture_output=True)
    if not output.exists():
        # A valid silent track keeps rendering available on machines without a voice pack.
        seconds=max(2.0,len(text.split())/2.35); rate=24000
        with wave.open(str(output),"wb") as wav:
            wav.setnchannels(1); wav.setsampwidth(2); wav.setframerate(rate); wav.writeframes(b"\x00\x00"*int(rate*seconds))

def wav_duration(path: Path):
    with wave.open(str(path),"rb") as w: return w.getnframes()/w.getframerate()

@app.post("/render")
async def render(project: str = Form(...), images: list[UploadFile] = File(default=[]), music: UploadFile | None = File(default=None)):
    ffmpeg = ffmpeg_path()
    if not ffmpeg: raise HTTPException(503, "FFmpeg is required. Run npm install, then restart the local engine.")
    cfg=json.loads(project); scenes=cfg.get("scenes",[])
    if not scenes: raise HTTPException(400,"Add at least one scene")
    work=Path(tempfile.mkdtemp(prefix="companion-studio-")); uploaded=[]
    try:
        for index, item in enumerate(images):
            path=work/f"upload-{index}{Path(item.filename or '.jpg').suffix}"; path.write_bytes(await item.read()); uploaded.append(path)
        remote=cfg.get("images",[]); sources=[]
        for value in remote:
            try: sources.append(download_image(value))
            except Exception: pass
        for path in uploaded:
            try: sources.append(Image.open(path).convert("RGB"))
            except Exception: pass
        if not sources: sources=[Image.new("RGB",(1080,1920),(28,24,50))]
        narration=". ".join(str(s.get("text",s)) for s in scenes); voice=work/"voice.wav"; speak(narration,voice)
        durations=[max(.5,float(s.get("duration",3.2))) for s in scenes]
        frame_paths=[]
        for i,scene in enumerate(scenes):
            bg=sources[i%len(sources)].copy(); scale=max(1080/bg.width,1920/bg.height); bg=bg.resize((int(bg.width*scale),int(bg.height*scale)),Image.Resampling.LANCZOS); left=(bg.width-1080)//2; top=(bg.height-1920)//2; bg=bg.crop((left,top,left+1080,top+1920))
            blurred=bg.filter(ImageFilter.GaussianBlur(26)); blurred=Image.blend(blurred,Image.new("RGB",blurred.size,(12,10,25)),.35); product=bg.copy(); product.thumbnail((900,1040),Image.Resampling.LANCZOS); blurred.paste(product,((1080-product.width)//2,260))
            draw=ImageDraw.Draw(blurred,"RGBA"); draw.rounded_rectangle((70,1320,1010,1790),radius=42,fill=(10,10,22,205)); draw.text((95,1380),str(scene.get("label",f"SCENE {i+1}" )).upper(),font=font(28,True),fill=(176,161,255,255))
            text=str(scene.get("text",scene)); words=text.split(); lines=[]; line=""
            for word in words:
                trial=(line+" "+word).strip()
                if draw.textlength(trial,font=font(48,True))>850 and line: lines.append(line); line=word
                else: line=trial
            if line: lines.append(line)
            draw.multiline_text((95,1440),"\n".join(lines[:5]),font=font(48,True),fill="white",spacing=13)
            draw.text((95,1725),cfg.get("cta","Learn more"),font=font(30,True),fill=(255,205,94,255)); path=work/f"frame-{i:02}.jpg"; blurred.save(path,quality=94); frame_paths.append(path)
        concat=work/"frames.txt"; concat.write_text("".join(f"file '{p.as_posix()}'\nduration {durations[i]:.3f}\n" for i,p in enumerate(frame_paths))+f"file '{frame_paths[-1].as_posix()}'\n",encoding="utf-8")
        out=OUTPUTS/"product-ad.mp4"; cmd=[ffmpeg,"-y","-f","concat","-safe","0","-i",str(concat),"-i",str(voice)]
        if music:
            music_path=work/(music.filename or "music.mp3"); music_path.write_bytes(await music.read()); cmd += ["-stream_loop","-1","-i",str(music_path),"-filter_complex","[1:a]volume=1.0[v];[2:a]volume=0.16[m];[v][m]amix=inputs=2:duration=first[a]","-map","0:v","-map","[a]"]
        else: cmd += ["-map","0:v","-map","1:a"]
        cmd += ["-vf","fps=30,format=yuv420p","-c:v","libx264","-preset","medium","-crf","20","-c:a","aac","-b:a","192k","-shortest",str(out)]
        subprocess.run(cmd,check=True,capture_output=True); return FileResponse(out,media_type="video/mp4",filename="product-ad.mp4")
    except HTTPException: raise
    except Exception as exc: raise HTTPException(500,f"Render failed: {exc}")
    finally: shutil.rmtree(work,ignore_errors=True)

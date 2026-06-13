import os
import uuid
import shutil
import asyncio
from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Literal

from script_generator import generate_script
from tts_service import generate_audio
from video_fetcher import fetch_video_clips
from image_fetcher import fetch_style_images
from video_assembler import assemble_video

app = FastAPI(title="FacelessShorts API", version="2.0.0")

BASE_URL = os.environ.get("RENDER_BASE_URL", "http://localhost:8000")
MAX_JOBS = int(os.environ.get("MAX_CONCURRENT_JOBS", "1"))
active_jobs: list = []
jobs: dict = {}

VALID_STYLES = {"cinematic", "anime", "cartoon", "comic", "realistic"}
VALID_PLATFORMS = {"tiktok", "youtube", "instagram", "general"}


class ReelRequest(BaseModel):
    topic: str
    style: Literal["cinematic", "anime", "cartoon", "comic", "realistic"] = "cinematic"
    platform: Literal["tiktok", "youtube", "instagram", "general"] = "general"


@app.get("/")
def read_root():
    return {
        "status": "FacelessShorts API is running",
        "version": "2.0.0",
        "styles": list(VALID_STYLES),
        "platforms": list(VALID_PLATFORMS),
    }


@app.post("/generate")
async def generate_reel(request: ReelRequest, background_tasks: BackgroundTasks):
    if not request.topic or not request.topic.strip():
        raise HTTPException(status_code=400, detail="Topic cannot be empty")

    if len(active_jobs) >= MAX_JOBS:
        raise HTTPException(
            status_code=429,
            detail=f"Server busy — max {MAX_JOBS} concurrent video(s). Try again in 60 seconds."
        )

    job_id = str(uuid.uuid4())
    jobs[job_id] = {
        "status": "queued",
        "video_url": None,
        "error": None,
        "topic": request.topic.strip(),
        "style": request.style,
        "platform": request.platform,
    }
    active_jobs.append(job_id)
    background_tasks.add_task(
        run_pipeline,
        job_id,
        request.topic.strip(),
        request.style,
        request.platform,
    )
    return {
        "job_id": job_id,
        "status": "queued",
        "message": "Video generation started",
        "style": request.style,
        "platform": request.platform,
    }


@app.get("/status/{job_id}")
def get_status(job_id: str):
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    job = jobs[job_id]
    video_url = f"{BASE_URL}/video/{job_id}" if job.get("video_url") else None
    return {
        "job_id": job_id,
        "status": job["status"],
        "video_url": video_url,
        "style": job.get("style"),
        "platform": job.get("platform"),
        "error": job.get("error"),
    }


@app.get("/video/{job_id}")
def get_video(job_id: str):
    output_path = f"/tmp/{job_id}/output.mp4"
    if not os.path.exists(output_path):
        raise HTTPException(status_code=404, detail="Video not found or not ready yet")
    return FileResponse(
        output_path,
        media_type="video/mp4",
        filename=f"facelessshorts_{job_id[:8]}.mp4",
    )


async def run_pipeline(job_id: str, topic: str, style: str, platform: str):
    workdir = f"/tmp/{job_id}"
    os.makedirs(workdir, exist_ok=True)

    try:
        # Step 1: Generate script (platform-aware)
        jobs[job_id]["status"] = "generating_script"
        script = await asyncio.to_thread(generate_script, topic, platform, style)
        with open(f"{workdir}/script.txt", "w") as f:
            f.write(script)

        # Step 2: Text-to-speech
        jobs[job_id]["status"] = "generating_audio"
        audio_path = f"{workdir}/audio.mp3"
        await asyncio.to_thread(generate_audio, script, audio_path)

        # Step 3: Get visuals — Pexels for cinematic/realistic, Pollinations for anime/cartoon/comic
        jobs[job_id]["status"] = "fetching_visuals"
        clips_dir = f"{workdir}/clips"
        os.makedirs(clips_dir, exist_ok=True)

        if style in ("cinematic", "realistic"):
            await asyncio.to_thread(fetch_video_clips, topic, clips_dir)
        else:
            await asyncio.to_thread(fetch_style_images, topic, style, script, clips_dir)

        # Step 4: Assemble
        jobs[job_id]["status"] = "assembling"
        output_path = f"{workdir}/output.mp4"
        await asyncio.to_thread(assemble_video, audio_path, clips_dir, output_path, style)

        jobs[job_id]["status"] = "complete"
        jobs[job_id]["video_url"] = f"/video/{job_id}"

    except Exception as e:
        jobs[job_id]["status"] = "failed"
        jobs[job_id]["error"] = str(e)
        if os.path.exists(workdir):
            shutil.rmtree(workdir, ignore_errors=True)
    finally:
        if job_id in active_jobs:
            active_jobs.remove(job_id)

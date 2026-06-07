import os
import asyncio
import requests
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.staticfiles import StaticFiles
from g4f.client import Client
import edge_tts
from moviepy.editor import VideoFileClip, AudioFileClip

app = FastAPI()

# Create a folder to store the finished videos
os.makedirs("static", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

client = Client()

class ReelRequest(BaseModel):
    topic: str

def generate_free_script(topic: str) -> str:
    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": f"Write a short, engaging 15-second narration about: {topic}. Return ONLY the script text, no quotes, no commentary."}]
        )
        return response.choices[0].message.content
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Script generation failed: {str(e)}")

async def generate_free_voiceover(text: str) -> str:
    try:
        audio_path = "static/voice.mp3"
        communicate = edge_tts.Communicate(text, "en-US-ChristopherNeural")
        await communicate.save(audio_path)
        return audio_path
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Voiceover generation failed: {str(e)}")

def get_free_video(topic: str) -> str:
    try:
        # This is a temporary public key for testing. 
        # Later, we can put your own free key here!
        pexels_key = "5334c3042d8a947c9b13280f55547886" 
        url = f"https://api.pexels.com/videos/search?query={topic}&per_page=1&orientation=portrait"
        headers = {"Authorization": pexels_key}
        
        response = requests.get(url, headers=headers).json()
        video_url = response['videos'][0]['video_files'][0]['link']
        
        video_path = "static/background.mp4"
        video_data = requests.get(video_url).content
        with open(video_path, "wb") as f:
            f.write(video_data)
        return video_path
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Video download failed: {str(e)}")

@app.post("/generate")
async def generate_reel(request: ReelRequest):
    try:
        script = generate_free_script(request.topic)
        audio_path = await generate_free_voiceover(script)
        video_path = get_free_video(request.topic)
        
        video_clip = VideoFileClip(video_path)
        audio_clip = AudioFileClip(audio_path)
        
        final_clip = video_clip.subclip(0, audio_clip.duration).set_audio(audio_clip)
        
        output_path = "static/final_output.mp4"
        final_clip.resize(newsize=(1080, 1920)).write_videofile(
            output_path, 
            fps=30, 
            codec="libx264", 
            audio_codec="aac",
            logger=None
        )
        
        video_clip.close()
        audio_clip.close()
        
        return {"status": "success", "video_url": f"static/final_output.mp4"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

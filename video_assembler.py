import os
import glob
import subprocess
from moviepy.editor import (
    VideoFileClip,
    AudioFileClip,
    ImageClip,
    concatenate_videoclips,
)

TARGET_W = 1080
TARGET_H = 1920
IMAGE_STYLES = {"anime", "cartoon", "comic"}


def assemble_video(audio_path: str, clips_dir: str, output_path: str, style: str = "cinematic") -> None:
    audio = AudioFileClip(audio_path)
    audio_duration = audio.duration
    audio.close()

    if style in IMAGE_STYLES:
        _assemble_images_ffmpeg(audio_path, clips_dir, output_path, audio_duration)
    else:
        _assemble_video_ffmpeg(audio_path, clips_dir, output_path, audio_duration)


def _assemble_video_ffmpeg(audio_path: str, clips_dir: str, output_path: str, duration: float) -> None:
    clip_files = sorted(glob.glob(os.path.join(clips_dir, "clip_*.mp4")))
    if not clip_files:
        raise ValueError("No video clips found")

    # Write concat list
    concat_file = os.path.join(clips_dir, "concat.txt")
    with open(concat_file, "w") as f:
        total = 0.0
        while total < duration:
            for clip_path in clip_files:
                if total >= duration:
                    break
                f.write(f"file '{clip_path}'\n")
                # Get clip duration
                result = subprocess.run(
                    ["ffprobe", "-v", "error", "-show_entries", "format=duration",
                     "-of", "default=noprint_wrappers=1:nokey=1", clip_path],
                    capture_output=True, text=True
                )
                try:
                    clip_dur = float(result.stdout.strip())
                except:
                    clip_dur = 5.0
                total += clip_dur

    # Use ffmpeg directly — much lower memory than MoviePy
    cmd = [
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0", "-i", concat_file,
        "-i", audio_path,
        "-t", str(duration),
        "-vf", f"scale={TARGET_W}:{TARGET_H}:force_original_aspect_ratio=increase,crop={TARGET_W}:{TARGET_H}",
        "-c:v", "libx264", "-preset", "ultrafast", "-crf", "28",
        "-c:a", "aac", "-shortest",
        output_path
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise ValueError(f"FFmpeg error: {result.stderr[-500:]}")


def _assemble_images_ffmpeg(audio_path: str, clips_dir: str, output_path: str, duration: float) -> None:
    image_files = sorted(glob.glob(os.path.join(clips_dir, "frame_*.jpg")))
    if not image_files:
        raise ValueError("No image frames found")

    per_image = duration / len(image_files)

    concat_file = os.path.join(clips_dir, "concat.txt")
    with open(concat_file, "w") as f:
        for img_path in image_files:
            f.write(f"file '{img_path}'\n")
            f.write(f"duration {per_image}\n")

    cmd = [
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0", "-i", concat_file,
        "-i", audio_path,
        "-t", str(duration),
        "-vf", f"scale={TARGET_W}:{TARGET_H}:force_original_aspect_ratio=increase,crop={TARGET_W}:{TARGET_H}",
        "-c:v", "libx264", "-preset", "ultrafast", "-crf", "28",
        "-c:a", "aac", "-shortest",
        output_path
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise ValueError(f"FFmpeg error: {result.stderr[-500:]}")

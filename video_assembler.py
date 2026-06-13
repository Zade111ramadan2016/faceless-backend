import os
import glob
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

    if style in IMAGE_STYLES:
        final_bg = _assemble_from_images(clips_dir, audio_duration)
    else:
        final_bg = _assemble_from_video(clips_dir, audio_duration)

    final = final_bg.set_audio(audio).set_duration(audio_duration)

    final.write_videofile(
        output_path,
        codec="libx264",
        audio_codec="aac",
        fps=30,
        preset="ultrafast",
        threads=2,
        logger=None,
    )

    audio.close()
    final.close()


def _assemble_from_images(clips_dir: str, duration: float):
    image_files = sorted(glob.glob(os.path.join(clips_dir, "frame_*.jpg")))
    if not image_files:
        raise ValueError("No image frames found")

    per_image = duration / len(image_files)
    clips = []
    for path in image_files:
        clip = (
            ImageClip(path)
            .set_duration(per_image)
            .resize((TARGET_W, TARGET_H))
        )
        clips.append(clip)

    return concatenate_videoclips(clips, method="compose")


def _assemble_from_video(clips_dir: str, duration: float):
    clip_files = sorted(glob.glob(os.path.join(clips_dir, "clip_*.mp4")))
    if not clip_files:
        raise ValueError("No video clips found")

    processed = []
    for path in clip_files:
        try:
            clip = VideoFileClip(path, audio=False)
            clip = _resize_to_portrait(clip)
            processed.append(clip)
        except Exception:
            continue

    if not processed:
        raise ValueError("Failed to load any video clips")

    return _fit_clips_to_duration(processed, duration)


def _resize_to_portrait(clip):
    clip_w, clip_h = clip.size
    if (clip_w / clip_h) > (TARGET_W / TARGET_H):
        clip = clip.resize(height=TARGET_H)
        x_c = clip.w / 2
        clip = clip.crop(x1=x_c - TARGET_W / 2, x2=x_c + TARGET_W / 2)
    else:
        clip = clip.resize(width=TARGET_W)
        y_c = clip.h / 2
        clip = clip.crop(y1=y_c - TARGET_H / 2, y2=y_c + TARGET_H / 2)
    return clip.resize((TARGET_W, TARGET_H))


def _fit_clips_to_duration(clips: list, duration: float):
    result, total = [], 0.0
    while total < duration:
        for clip in clips:
            remaining = duration - total
            if remaining <= 0:
                break
            seg = clip.subclip(0, min(clip.duration, remaining))
            result.append(seg)
            total += seg.duration
    if not result:
        raise ValueError("Could not build video sequence")
    return concatenate_videoclips(result, method="compose")

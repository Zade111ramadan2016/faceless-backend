import os
import requests


PEXELS_API_KEY = os.environ["PEXELS_API_KEY"]
PEXELS_VIDEO_URL = "https://api.pexels.com/videos/search"


def fetch_video_clips(topic: str, clips_dir: str, max_clips: int = 4) -> None:
    headers = {"Authorization": PEXELS_API_KEY}
    params = {
        "query": topic,
        "per_page": max_clips,
        "orientation": "portrait",   # Vertical for reels/shorts
        "size": "medium",
    }

    response = requests.get(PEXELS_VIDEO_URL, headers=headers, params=params, timeout=15)
    response.raise_for_status()
    data = response.json()

    videos = data.get("videos", [])
    if not videos:
        # Fallback: search with a more generic term
        params["query"] = "nature background"
        response = requests.get(PEXELS_VIDEO_URL, headers=headers, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        videos = data.get("videos", [])

    if not videos:
        raise ValueError(f"No video clips found for topic: {topic}")

    for i, video in enumerate(videos[:max_clips]):
        # Pick the smallest HD file to keep download fast
        video_files = video.get("video_files", [])
        chosen = _pick_best_file(video_files)
        if not chosen:
            continue

        clip_path = os.path.join(clips_dir, f"clip_{i}.mp4")
        _download_file(chosen["link"], clip_path)


def _pick_best_file(video_files: list) -> dict | None:
    # Prefer HD portrait (1080x1920), fall back to any HD
    portrait_hd = [
        f for f in video_files
        if f.get("height", 0) >= 1080 and f.get("width", 0) <= f.get("height", 1)
    ]
    if portrait_hd:
        return min(portrait_hd, key=lambda f: f.get("file_size", float("inf")))

    hd_files = [f for f in video_files if f.get("quality") in ("hd", "sd")]
    if hd_files:
        return min(hd_files, key=lambda f: f.get("file_size", float("inf")))

    return video_files[0] if video_files else None


def _download_file(url: str, dest_path: str) -> None:
    with requests.get(url, stream=True, timeout=60) as r:
        r.raise_for_status()
        with open(dest_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)

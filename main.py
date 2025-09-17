import os
import random
import numpy as np
from moviepy.editor import *
from PIL import Image, ImageDraw, ImageFont
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials
from diffusers import StableDiffusionPipeline
import torch

# ------------------ CONFIG ------------------
VIDEOS_DIR = "videos"
IMAGES_DIR = "images"
MUSIC_DIR = "music"
os.makedirs(VIDEOS_DIR, exist_ok=True)
os.makedirs(IMAGES_DIR, exist_ok=True)
os.makedirs(MUSIC_DIR, exist_ok=True)

WIDTH, HEIGHT = 1080, 1920
VIDEO_DURATION = 15

# ------------------ LOAD QUOTES ------------------
with open("quotes.txt", "r", encoding="utf-8") as f:
    QUOTES = [q.strip() for q in f.readlines() if q.strip()]

# ------------------ STABLE DIFFUSION ------------------
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
pipe = StableDiffusionPipeline.from_pretrained(
    "runwayml/stable-diffusion-v1-5", torch_dtype=torch.float32
).to(DEVICE)

def generate_ai_image(quote, output_path):
    prompt = f"Ultra realistic cinematic illustration, Indian style, motivational theme: {quote}"
    try:
        result = pipe(prompt, height=512, width=512, num_inference_steps=20)
        img = result.images[0]
        img.save(output_path)
        return output_path
    except Exception as e:
        print("⚠️ AI Image generation failed, using fallback black screen:", e)
        img = Image.new("RGB", (WIDTH, HEIGHT), color=(0, 0, 0))
        draw = ImageDraw.Draw(img)
        font = ImageFont.load_default()
        draw.text((50, HEIGHT//2), quote[:80], fill="white", font=font)
        img.save(output_path)
        return output_path

# ------------------ PICK MUSIC ------------------
def get_music():
    tracks = [f for f in os.listdir(MUSIC_DIR) if f.endswith((".mp3", ".wav"))]
    return os.path.join(MUSIC_DIR, random.choice(tracks)) if tracks else None

# ------------------ CREATE VIDEO ------------------
def create_quote_video(quote, output_path):
    img_path = os.path.join(IMAGES_DIR, "ai_image.png")
    img_path = generate_ai_image(quote, img_path)
    clip = ImageClip(img_path).set_duration(VIDEO_DURATION).resize((WIDTH, HEIGHT))

    music_file = get_music()
    if music_file:
        audio = AudioFileClip(music_file).subclip(0, VIDEO_DURATION)
        clip = clip.set_audio(audio)

    clip.write_videofile(output_path, fps=24, codec="libx264", audio_codec="aac")

# ------------------ UPLOAD TO YOUTUBE ------------------
def upload_youtube(video_file, quote):
    creds = Credentials.from_authorized_user_file("token.json", ["https://www.googleapis.com/auth/youtube.upload"])
    youtube = build("youtube", "v3", credentials=creds)
    title = f"{quote[:60]} | Motivational Shorts"
    description = f"{quote}\n#motivation #shorts #inspiration #india"
    tags = ["motivation", "shorts", "inspiration", "success", "life"]
    request_body = {
        "snippet": {"title": title, "description": description, "tags": tags, "categoryId": "22"},
        "status": {"privacyStatus": "public"}
    }
    media = MediaFileUpload(video_file, chunksize=-1, resumable=True, mimetype="video/*")
    request = youtube.videos().insert(part="snippet,status", body=request_body, media_body=media)
    response = request.execute()
    print(f"✅ Uploaded: https://youtu.be/{response['id']}")

# ------------------ MAIN AUTOMATION ------------------
def main():
    # Check existing videos first
    ready_videos = [f for f in os.listdir(VIDEOS_DIR) if f.endswith(".mp4")]
    if ready_videos:
        video_file = os.path.join(VIDEOS_DIR, random.choice(ready_videos))
        print(f"📤 Uploading existing video: {video_file}")
        upload_youtube(video_file, "Ready-made video")
        os.remove(video_file)
        return

    # Generate new video
    quote = random.choice(QUOTES)
    print(f"🎬 Generating new video with quote: {quote}")
    output_path = os.path.join(VIDEOS_DIR, "quote_video.mp4")
    create_quote_video(quote, output_path)
    upload_youtube(output_path, quote)
    os.remove(output_path)

if __name__ == "__main__":
    main()
        

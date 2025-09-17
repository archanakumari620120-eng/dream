import os
import random
import json
from datetime import datetime
from moviepy.editor import ImageClip, AudioFileClip
from diffusers import StableDiffusionPipeline
import torch
from PIL import Image, ImageDraw
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials

# 📂 Directories
IMAGES_DIR = "images"
MUSIC_DIR = "music"
VIDEOS_DIR = "videos"

os.makedirs(IMAGES_DIR, exist_ok=True)
os.makedirs(MUSIC_DIR, exist_ok=True)
os.makedirs(VIDEOS_DIR, exist_ok=True)

# 🎯 Config
VIDEO_DURATION = 10
TOPIC = "Motivation & Life Quotes"

# 🤖 Load pipeline (CPU/GPU safe)
device = "cuda" if torch.cuda.is_available() else "cpu"
pipe = StableDiffusionPipeline.from_pretrained(
    "runwayml/stable-diffusion-v1-5",
    torch_dtype=torch.float32
).to(device)

# 📝 Quotes list
QUOTES = [
    "Difficulties in life don’t come to destroy you, but to help you realize your hidden potential.",
    "Success doesn’t come from what you do occasionally, it comes from what you do consistently.",
    "Your struggle today will be your strength tomorrow.",
    "Don’t wait for opportunity, create it.",
    "If you want to shine like the sun, first burn like the sun.",
    "Dream big. Start small. Act now.",
    "The harder you work for something, the greater you’ll feel when you achieve it.",
    "Push yourself, because no one else is going to do it for you.",
    "Don’t fear failure. Fear being in the same place next year as you are today.",
    "Discipline is choosing between what you want now and what you want most."
    # 👉 Aur bhi quotes add kar sakte ho
]

# 🖼️ Image generation
def generate_image(i, quote):
    try:
        prompt = f"Ultra realistic cinematic illustration, Indian style, motivational theme: {quote}"
        result = pipe(prompt, height=512, width=512, num_inference_steps=20)
        image = result.images[0]
        path = os.path.join(IMAGES_DIR, f"image_{i}.png")
        image.save(path)
        return path
    except Exception as e:
        print(f"⚠️ Image generation failed: {e}")
        fallback = Image.new("RGB", (512, 512), color=(0, 0, 0))
        d = ImageDraw.Draw(fallback)
        d.text((50, 250), quote[:40], fill=(255, 255, 255))
        path = os.path.join(IMAGES_DIR, f"image_fallback_{i}.png")
        fallback.save(path)
        return path

# 🎵 Music selection
def get_music():
    files = [f for f in os.listdir(MUSIC_DIR) if f.endswith(".mp3")]
    if files:
        return os.path.join(MUSIC_DIR, random.choice(files))
    return None

# 🎬 Video creation
def create_video(i, img, audio, quote):
    try:
        path = os.path.join(VIDEOS_DIR, f"video_{i}.mp4")
        clip = ImageClip(img, duration=VIDEO_DURATION)
        if audio and os.path.exists(audio):
            audio_clip = AudioFileClip(audio)
            clip = clip.set_audio(audio_clip)
        clip.write_videofile(path, fps=24, codec="libx264", audio_codec="aac")
        return path
    except Exception as e:
        print(f"❌ Video creation failed: {e}")
        return None

# 📤 Upload to YouTube
def upload_youtube(video_file, quote):
    creds = Credentials.from_authorized_user_file("token.json", ["https://www.googleapis.com/auth/youtube.upload"])
    youtube = build("youtube", "v3", credentials=creds)

    title = f"{quote[:60]} | Motivational Shorts"
    description = f"Motivational Quote: {quote}\n#motivation #shorts #inspiration #life"
    tags = ["motivation", "shorts", "inspiration", "success", "life"]

    request_body = {
        "snippet": {
            "title": title,
            "description": description,
            "tags": tags,
            "categoryId": "22"
        },
        "status": {
            "privacyStatus": "public"
        }
    }

    media = MediaFileUpload(video_file, chunksize=-1, resumable=True, mimetype="video/*")
    upload = youtube.videos().insert(part="snippet,status", body=request_body, media_body=media)
    response = upload.execute()
    print(f"✅ Uploaded: https://youtu.be/{response['id']}")

# 🚀 Main
def run_automation():
    quote = random.choice(QUOTES)
    print(f"\n🎬 Creating video with quote: {quote}")

    img = generate_image(0, quote)
    audio = get_music()
    video = create_video(0, img, audio, quote)

    if video:
        upload_youtube(video, quote)
        print("🎉 Automation complete!")
    else:
        print("❌ Automation failed!")

if __name__ == "__main__":
    run_automation()
        

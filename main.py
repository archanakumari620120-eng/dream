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
    "Great things never come from comfort zones.",
    "Dream it. Wish it. Do it.",
    "Success doesn’t just find you. You have to go out and get it.",
    "The harder you work for something, the greater you’ll feel when you achieve it.",
    "Dream bigger. Do bigger.",
    "Don’t stop when you’re tired. Stop when you’re done.",
    "Wake up with determination. Go to bed with satisfaction.",
    "Do something today that your future self will thank you for.",
    "Little things make big days.",
    "It’s going to be hard, but hard does not mean impossible.",
    "Don’t wait for opportunity. Create it.",
    "Sometimes we’re tested not to show our weaknesses, but to discover our strengths.",
    "The key to success is to focus on goals, not obstacles.",
    "Dream big. Start small. Act now.",
    "Discipline is choosing between what you want now and what you want most.",
    "Your struggle today will be your strength tomorrow.",
    "Fear kills more dreams than failure ever will.",
    "Work hard in silence. Let your success make the noise.",
    "Your limitation—it’s only your imagination.",
    "Sometimes later becomes never. Do it now.",
    "Don’t watch the clock; do what it does. Keep going.",
    "Hard work beats talent when talent doesn’t work hard.",
    "Do what you can with all you have, wherever you are.",
    "A little progress each day adds up to big results.",
    "Opportunities don’t happen. You create them.",
    "Failure is not the opposite of success; it’s part of success.",
    "Doubt kills more dreams than failure ever will.",
    "If you want to achieve greatness stop asking for permission.",
    "Success is walking from failure to failure with no loss of enthusiasm.",
    "The secret of getting ahead is getting started.",
    "Start where you are. Use what you have. Do what you can.",
    "Don’t be afraid to give up the good to go for the great.",
    "The way to get started is to quit talking and begin doing.",
    "Your time is limited, so don’t waste it living someone else’s life.",
    "Everything you’ve ever wanted is on the other side of fear.",
    "If you can dream it, you can do it.",
    "Believe in yourself and all that you are.",
    "Act as if what you do makes a difference. It does.",
    "Go the extra mile. It’s never crowded.",
    "Well done is better than well said.",
    "Stay positive, work hard, make it happen.",
    "It always seems impossible until it’s done.",
    "Consistency is the key to success.",
    "Small progress is still progress.",
    "Success is not final, failure is not fatal: It is the courage to continue that counts.",
    "Fall seven times and stand up eight.",
    "Winners are not afraid of losing. But losers are."
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
def pick_music():
    if not MUSIC_DIR.exists():
        return None
    mus = [p for p in MUSIC_DIR.iterdir() if p.suffix.lower() in ('.mp3','.wav','.m4a')]
    return str(random.choice(mus)) if mus else None

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
    music = pick_music()
    video = create_video(0, img, audio, quote)

    if video:
        upload_youtube(video, quote)
        print("🎉 Automation complete!")
    else:
        print("❌ Automation failed!")

if __name__ == "__main__":
    run_automation()
        

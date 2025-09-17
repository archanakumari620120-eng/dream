import os
import random
import logging
from datetime import datetime
from moviepy.editor import ImageClip, AudioFileClip
from pytube import YouTube
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials
from PIL import Image, ImageDraw, ImageFont

# 📂 Directories
IMAGES_DIR = "images"
VIDEOS_DIR = "videos"
LOG_FILE = "automation.log"
os.makedirs(IMAGES_DIR, exist_ok=True)
os.makedirs(VIDEOS_DIR, exist_ok=True)

# 🎯 Config
video_duration = 15
SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]

# 📝 Logger Setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, mode="a"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Random topics & quotes
TOPICS = ["Motivation", "Success", "Love", "Life", "Positivity", "Focus", "Discipline"]
QUOTES = [
    "Believe in yourself!",
    "Stay strong, work hard.",
    "Dream big, act bigger.",
    "Discipline beats motivation.",
    "Every day is a new chance.",
    "Hustle until you shine.",
    "Focus. Persist. Achieve."
]

# 🔑 Authenticate YouTube with token.json
def youtube_authenticate():
    try:
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
        logger.info("✅ YouTube authentication successful.")
        return build("youtube", "v3", credentials=creds)
    except Exception as e:
        logger.error(f"❌ YouTube authentication failed: {e}")
        raise

# 🖼️ Generate simple image with text
def generate_image(i, topic, quote):
    try:
        fallback = Image.new("RGB", (720, 1280), color=(0, 0, 0))
        d = ImageDraw.Draw(fallback)
        try:
            font = ImageFont.truetype("arial.ttf", 40)
        except:
            font = None
        d.text((50, 600), quote, fill=(255, 255, 255), font=font)
        path = os.path.join(IMAGES_DIR, f"image_{i}.png")
        fallback.save(path)
        logger.info(f"🖼️ Image generated: {path}")
        return path
    except Exception as e:
        logger.error(f"❌ Image generation failed: {e}")
        raise

# 🎵 Auto-download music
def download_music():
    try:
        url = "https://www.youtube.com/watch?v=jfKfPfyJRdk"  # Safe lofi
        yt = YouTube(url)
        stream = yt.streams.filter(only_audio=True).first()
        path = "temp_music.mp3"
        stream.download(filename=path)
        logger.info("🎵 Music downloaded successfully.")
        return path
    except Exception as e:
        logger.warning(f"⚠️ Music download failed, skipping: {e}")
        return None

# 🎬 Create video
def create_video(i, img, audio):
    try:
        path = os.path.join(VIDEOS_DIR, f"video_{i}.mp4")
        clip = ImageClip(img, duration=video_duration)
        if audio and os.path.exists(audio):
            audio_clip = AudioFileClip(audio).subclip(0, video_duration)
            clip = clip.set_audio(audio_clip)
        clip.write_videofile(path, fps=24, codec="libx264", audio_codec="aac", logger=None)
        logger.info(f"🎬 Video created: {path}")
        return path
    except Exception as e:
        logger.error(f"❌ Video creation failed: {e}")
        raise

# 📤 Upload to YouTube
def upload_video(youtube, video_path, title, description, tags):
    try:
        request = youtube.videos().insert(
            part="snippet,status",
            body={
                "snippet": {
                    "title": title,
                    "description": description,
                    "tags": tags,
                    "categoryId": "22"
                },
                "status": {"privacyStatus": "public"}
            },
            media_body=MediaFileUpload(video_path)
        )
        response = request.execute()
        logger.info(f"✅ Uploaded to YouTube: {response['id']}")
    except Exception as e:
        logger.error(f"❌ Upload failed: {e}")
        raise

# 🚀 Main automation
def run_automation(total_videos=1):
    logger.info("🚀 Starting automation...")
    youtube = youtube_authenticate()

    for i in range(total_videos):
        logger.info(f"🎯 Starting video {i+1}/{total_videos}")

        topic = random.choice(TOPICS)
        quote = random.choice(QUOTES)

        try:
            img = generate_image(i, topic, quote)
            audio = download_music()
            video = create_video(i, img, audio)

            title = f"{quote} | {topic} Shorts #{random.randint(100,999)}"
            description = f"{quote}\n\n#Shorts #{topic.lower()}"
            tags = [topic, "motivation", "quotes", "shorts"]

            upload_video(youtube, video, title, description, tags)

        except Exception as e:
            logger.error(f"❌ Error in video {i+1}: {e}")

    logger.info("🎉 Automation completed!")

if __name__ == "__main__":
    run_automation(total_videos=2)
    

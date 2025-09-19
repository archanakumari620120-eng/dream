import os
import random
import traceback
import requests
import glob
from time import sleep
from datetime import datetime

# Video processing
from moviepy.editor import ImageClip, AudioFileClip, vfx

# YouTube API
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials

# ---------------- CONFIG & DIRECTORIES ----------------
VIDEOS_DIR = "videos"
MUSIC_DIR = "music"
os.makedirs(VIDEOS_DIR, exist_ok=True)
os.makedirs(MUSIC_DIR, exist_ok=True)

# ---------------- TRENDING PROMPT GENERATOR ----------------
def generate_trending_prompt(quote):
    styles = [
        "ultra-realistic cinematic, trending on YouTube Shorts",
        "vibrant digital art, 3D render, highly detailed, viral style",
        "epic concept art, surreal and abstract, popular style",
        "cinematic lighting, modern illustration, eye-catching composition",
        "trending AI art, high quality, inspirational, vertical format"
    ]
    style = random.choice(styles)
    return f"Vertical 1080x1920 YouTube Short background inspired by quote: '{quote}', {style}"

# ---------------- HUGGING FACE IMAGE GENERATION ----------------
def generate_image_huggingface(prompt, model_id="stabilityai/stable-diffusion-xl-base-1.0"):
    try:
        print("🔹 Generating trending viral-style image...")
        api_token = os.getenv("HF_API_TOKEN")
        if not api_token:
            raise ValueError("❌ HF_API_TOKEN not found! Add it as secret.")

        api_url = f"https://api-inference.huggingface.co/models/{model_id}"
        headers = {"Authorization": f"Bearer {api_token}"}
        payload = {"inputs": prompt}

        response = requests.post(api_url, headers=headers, json=payload)
        if response.status_code == 503:
            print("⏳ Model loading, waiting 30 seconds...")
            sleep(30)
            response = requests.post(api_url, headers=headers, json=payload)

        if response.status_code != 200:
            raise Exception(f"Hugging Face API error. Status: {response.status_code}, Response: {response.text}")

        image_bytes = response.content
        img_path = os.path.join(VIDEOS_DIR, "frame.png")
        with open(img_path, "wb") as f:
            f.write(image_bytes)

        print(f"✅ Viral-style image generated at {img_path}")
        return img_path

    except Exception as e:
        print("❌ IMAGE GENERATION failed:")
        traceback.print_exc()
        raise

# ---------------- MUSIC SELECTION ----------------
def get_random_music():
    try:
        files = [f for f in os.listdir(MUSIC_DIR) if f.endswith((".mp3", ".wav"))]
        if not files:
            print("⚠️ No music found. Video will be silent.")
            return None
        chosen = os.path.join(MUSIC_DIR, random.choice(files))
        print(f"🎵 Selected music: {chosen}")
        return chosen
    except Exception as e:
        print("❌ MUSIC SELECTION failed:")
        traceback.print_exc()
        raise

# ---------------- VIDEO CREATION ----------------
def create_video(image_path, audio_path):
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = os.path.join(VIDEOS_DIR, f"short_{timestamp}.mp4")
        clip_duration = 10
        clip = ImageClip(image_path).set_duration(clip_duration)

        if audio_path and os.path.exists(audio_path):
            audio_clip = AudioFileClip(audio_path)
            if audio_clip.duration < clip_duration:
                audio_clip = audio_clip.fx(vfx.loop, duration=clip_duration)
            clip = clip.set_audio(audio_clip.subclip(0, clip_duration))

        clip.write_videofile(output_path, fps=24, codec="libx264", audio_codec="aac")
        print(f"✅ Video created successfully at {output_path}")

        # Cleanup old videos (keep last 10 only)
        all_videos = sorted(glob.glob(os.path.join(VIDEOS_DIR, "*.mp4")))
        if len(all_videos) > 10:
            for old_video in all_videos[:-10]:
                os.remove(old_video)
                print(f"🗑️ Deleted old video: {old_video}")

        return output_path

    except Exception as e:
        print("❌ VIDEO CREATION failed:")
        traceback.print_exc()
        raise

# ---------------- YOUTUBE UPLOAD ----------------
def upload_to_youtube(video_path, quote):
    try:
        print("🔹 Uploading video to YouTube...")
        creds = Credentials.from_authorized_user_file("token.json", ["https://www.googleapis.com/auth/youtube.upload"])
        youtube = build("youtube", "v3", credentials=creds)

        timestamp = datetime.now().strftime("%d %b %Y %H:%M")
        title = f"{quote} | AI Shorts {timestamp}"
        description = f"AI-generated motivational short video based on the quote: '{quote}'.\nUploaded at {timestamp}."
        hashtags = ["#AIShorts", "#Motivation", "#Inspiration", "#Quotes", "#Life"]
        tags = ["AI", "Shorts", "Motivation", "Quotes", "Life"]

        request = youtube.videos().insert(
            part="snippet,status",
            body={
                "snippet": {
                    "title": title,
                    "description": description + "\n" + " ".join(hashtags),
                    "tags": tags,
                    "categoryId": "22"
                },
                "status": {"privacyStatus": "private"}
            },
            media_body=video_path
        )

        response = request.execute()
        print(f"✅ Video uploaded successfully. Video ID: {response.get('id')}")
        return response.get("id")

    except Exception as e:
        print("❌ YOUTUBE UPLOAD failed:")
        traceback.print_exc()
        raise

# ---------------- MAIN PIPELINE ----------------
if __name__ == "__main__":
    try:
        quotes = [
            "Life is what happens when you're busy making other plans.",
            "Dream big, work hard, stay focused.",
            "Success is not final, failure is not fatal.",
            "Believe in yourself and all that you are.",
            "Every day is a second chance."
        ]
        quote = random.choice(quotes)
        print(f"📝 Selected quote: {quote}")

        # 1️⃣ Generate trending viral-style image
        prompt = generate_trending_prompt(quote)
        img_path = generate_image_huggingface(prompt)

        # 2️⃣ Select random music
        music_path = get_random_music()

        # 3️⃣ Create video
        video_path = create_video(img_path, music_path)

        # 4️⃣ Upload to YouTube
        upload_to_youtube(video_path, quote)

        print("🎉 Pipeline completed successfully!")

    except Exception as e:
        print("❌ Main pipeline failed:")
        traceback.print_exc()
        

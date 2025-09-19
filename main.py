import os
import base64
import random
import traceback
import requests
from time import sleep

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

# ---------------- HUGGING FACE IMAGE GENERATION ----------------
def generate_image_huggingface(prompt, model_id="stabilityai/stable-diffusion-xl-base-1.0"):
    api_token = os.getenv("HF_API_TOKEN")
    if not api_token:
        raise ValueError("❌ Hugging Face API Token नहीं मिला! कृपया 'HF_API_TOKEN' नाम का Secret सेट करें।")

    api_url = f"https://api-inference.huggingface.co/models/{model_id}"
    headers = {"Authorization": f"Bearer {api_token}"}

    payload = {
        "inputs": f"High-quality, vertical (1080x1920) YouTube Short background image for quote: '{prompt}'",
    }

    print(f"🔹 Sending request to Hugging Face model '{model_id}'...")
    response = requests.post(api_url, headers=headers, json=payload)

    if response.status_code == 503:
        print("⏳ Model loading, waiting 30 seconds...")
        sleep(30)
        response = requests.post(api_url, headers=headers, json=payload)

    if response.status_code != 200:
        error_message = f"❌ Hugging Face API error. Status: {response.status_code}, Response: {response.text}"
        print(error_message)
        raise Exception(error_message)

    image_bytes = response.content
    img_path = os.path.join(VIDEOS_DIR, "frame.png")
    with open(img_path, "wb") as f:
        f.write(image_bytes)

    print(f"✅ Image saved at {img_path}")
    return img_path

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
        print(f"❌ Error selecting music: {e}")
        raise

# ---------------- VIDEO CREATION ----------------
def create_video(image_path, audio_path, output_path="final_video.mp4"):
    try:
        print("🔹 Creating video...")
        clip_duration = 10
        clip = ImageClip(image_path).set_duration(clip_duration)

        if audio_path and os.path.exists(audio_path):
            audio_clip = AudioFileClip(audio_path)
            if audio_clip.duration < clip_duration:
                audio_clip = audio_clip.fx(vfx.loop, duration=clip_duration)
            clip = clip.set_audio(audio_clip.subclip(0, clip_duration))

        clip.write_videofile(output_path, fps=24, codec="libx264", audio_codec="aac")
        print(f"✅ Video created at {output_path}")
        return output_path
    except Exception as e:
        print(f"❌ Error creating video: {e}")
        traceback.print_exc()
        raise

# ---------------- YOUTUBE UPLOAD ----------------
def upload_to_youtube(video_path, title="AI Short Video", description="Auto-generated Short using AI"):
    try:
        print("🔹 Preparing YouTube upload...")
        creds = Credentials.from_authorized_user_file("token.json", ["https://www.googleapis.com/auth/youtube.upload"])
        youtube = build("youtube", "v3", credentials=creds)

        request = youtube.videos().insert(
            part="snippet,status",
            body={
                "snippet": {
                    "title": title,
                    "description": description,
                    "tags": ["AI", "Shorts", "Quotes", "Motivation"],
                    "categoryId": "22"
                },
                "status": {"privacyStatus": "private"}
            },
            media_body=video_path
        )

        response = request.execute()
        print(f"✅ Video uploaded. Video ID: {response.get('id')}")
        return response.get("id")
    except Exception as e:
        print(f"❌ Error uploading video: {e}")
        traceback.print_exc()
        raise

# ---------------- MAIN PIPELINE ----------------
if __name__ == "__main__":
    try:
        quote = "Life is what happens when you're busy making other plans."
        print(f"📝 Quote: {quote}")

        img_path = generate_image_huggingface(quote)
        music_path = get_random_music()
        video_path = create_video(img_path, music_path)
        upload_to_youtube(video_path, title=f"{quote} #shorts", description="AI Generated Motivational Short")

        print("🎉 Pipeline completed successfully!")
    except Exception as e:
        print(f"❌ Main pipeline error: {e}")
    

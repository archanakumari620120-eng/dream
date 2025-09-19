import os
import base64
import random
import traceback
import json
import requests
from time import sleep
from moviepy.editor import ImageClip, AudioFileClip, vfx

# YouTube API
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

# ---------------- CONFIG & DIRECTORIES ----------------
VIDEOS_DIR = "videos"
MUSIC_DIR = "music"
os.makedirs(VIDEOS_DIR, exist_ok=True)
os.makedirs(MUSIC_DIR, exist_ok=True)

# ---------------- DEBUG SECRET CHECK ----------------
hf_token = os.getenv("HF_API_TOKEN")
client_secret_json = os.getenv("CLIENT_SECRET_JSON")
token_json = os.getenv("TOKEN_JSON")

if not hf_token:
    raise ValueError("❌ HF_API_TOKEN missing! Check GitHub Secrets.")
if not client_secret_json:
    raise ValueError("❌ CLIENT_SECRET_JSON missing!")
if not token_json:
    raise ValueError("❌ TOKEN_JSON missing!")

print("✅ All secrets loaded successfully.")

# ---------------- HUGGING FACE IMAGE GENERATION ----------------
def generate_image_huggingface(prompt, model_id="stabilityai/stable-diffusion-xl-base-1.0"):
    api_url = f"https://api-inference.huggingface.co/models/{model_id}"
    headers = {"Authorization": f"Bearer {hf_token}"}

    payload = {"inputs": prompt}
    print(f"🔹 Hugging Face API request sent...")
    response = requests.post(api_url, headers=headers, json=payload)

    if response.status_code == 503:
        print("⏳ Model loading, waiting 30 seconds...")
        sleep(30)
        response = requests.post(api_url, headers=headers, json=payload)

    if response.status_code != 200:
        raise Exception(f"❌ HF API Error {response.status_code}: {response.text}")

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
            print("⚠️ No music found, video will be silent.")
            return None
        chosen = os.path.join(MUSIC_DIR, random.choice(files))
        print(f"🎵 Music selected: {chosen}")
        return chosen
    except Exception as e:
        print(f"❌ Music selection error: {e}")
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
        print(f"✅ Video ready: {output_path}")
        return output_path
    except Exception as e:
        print(f"❌ Video creation error: {e}")
        traceback.print_exc()
        raise

# ---------------- YOUTUBE UPLOAD ----------------
def upload_to_youtube(video_path, title="AI Short Video", description="Auto-generated Short using AI"):
    try:
        # Temporarily write JSON secrets to files
        with open("client_secret.json", "w") as f:
            f.write(client_secret_json)
        with open("token.json", "w") as f:
            f.write(token_json)

        creds = Credentials.from_service_account_file(
            "client_secret.json",
            scopes=["https://www.googleapis.com/auth/youtube.upload"]
        )
        youtube = build("youtube", "v3", credentials=creds)

        request = youtube.videos().insert(
            part="snippet,status",
            body={
                "snippet": {
                    "title": title,
                    "description": description,
                    "tags": ["AI", "Shorts", "Viral", "Trending"],
                    "categoryId": "22"
                },
                "status": {"privacyStatus": "private"}
            },
            media_body=video_path
        )
        response = request.execute()
        print(f"✅ YouTube upload successful! Video ID: {response.get('id')}")
        return response.get("id")
    except Exception as e:
        print(f"❌ YouTube upload error: {e}")
        traceback.print_exc()
        raise

# ---------------- MAIN PIPELINE ----------------
if __name__ == "__main__":
    try:
        # Example prompt: viral trending concept
        concepts = ["dog", "cat", "human", "woman", "man", "animal", "nature", "robot", "tech"]
        concept = random.choice(concepts)
        prompt = f"Vertical 1080x1920 YouTube Short background of a {concept}, ultra-realistic cinematic, trending on YouTube Shorts"

        print(f"📝 Prompt: {prompt}")

        # 1️⃣ Image generation
        img_path = generate_image_huggingface(prompt)

        # 2️⃣ Pick music
        music_path = get_random_music()

        # 3️⃣ Video creation
        video_path = create_video(img_path, music_path)

        # 4️⃣ YouTube upload
        title = f"{concept.capitalize()} Video #Shorts"
        description = f"AI-generated viral video of {concept}, trending on YouTube Shorts."
        upload_to_youtube(video_path, title=title, description=description)

        print("🎉 Pipeline complete!")
    except Exception as e:
        print(f"❌ Pipeline failed: {e}")
        traceback.print_exc()
    

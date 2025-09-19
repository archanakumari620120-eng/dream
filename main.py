import os
import json
import random
import traceback
import requests
from time import sleep
from moviepy.editor import ImageClip, AudioFileClip, vfx
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
import google.generativeai as genai

# ---------------- CONFIG ----------------
VIDEOS_DIR = "videos"
os.makedirs(VIDEOS_DIR, exist_ok=True)

# ---------------- SECRETS ----------------
HF_API_TOKEN = os.getenv("HF_API_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
TOKEN_JSON = os.getenv("TOKEN_JSON")

if not HF_API_TOKEN or not GEMINI_API_KEY or not TOKEN_JSON:
    raise ValueError("❌ Missing secrets! Check HF_API_TOKEN, GEMINI_API_KEY, TOKEN_JSON")

# Save token.json locally for YouTube upload
with open("token.json", "w") as f:
    f.write(TOKEN_JSON)

genai.configure(api_key=GEMINI_API_KEY)

# ---------------- GEMINI: CONCEPT + METADATA ----------------
def generate_concept_and_metadata():
    try:
        user_prompt = (
            "Generate a viral YouTube Shorts concept trending now. "
            "Output JSON with: prompt, title, description, tags, hashtags"
        )
        response = genai.chat(messages=[{"content": user_prompt}])
        content = response.last
        data = json.loads(content)
        return data
    except Exception as e:
        print("⚠️ Gemini output failed, using default concept:", e)
        return {
            "prompt": "Vertical 1080x1920 YouTube Short background of an animal, ultra-realistic cinematic, trending",
            "title": "AI Viral Short #1",
            "description": "Auto-generated AI short video",
            "tags": "AI,Shorts,Trending",
            "hashtags": "#AI #Shorts #Trending"
        }

# ---------------- HUGGING FACE IMAGE GENERATION ----------------
def generate_image_huggingface(prompt, model_id="stabilityai/stable-diffusion-xl-base-1.0"):
    api_url = f"https://api-inference.huggingface.co/models/{model_id}"
    headers = {"Authorization": f"Bearer {HF_API_TOKEN}"}
    payload = {"inputs": prompt}

    print("🔹 Hugging Face API request...")
    response = requests.post(api_url, headers=headers, json=payload)
    if response.status_code == 503:
        sleep(30)
        response = requests.post(api_url, headers=headers, json=payload)

    if response.status_code != 200:
        raise Exception(f"Hugging Face API Error: {response.status_code}, {response.text}")

    img_path = os.path.join(VIDEOS_DIR, "frame.png")
    with open(img_path, "wb") as f:
        f.write(response.content)

    print(f"✅ Image saved: {img_path}")
    return img_path

# ---------------- COPYRIGHT-FREE YOUTUBE MUSIC ----------------
def get_youtube_music():
    # Example: YouTube Audio Library direct download links or pre-downloaded tracks
    # For automation, maintain music/ folder with few mp3s downloaded from YouTube Audio Library
    MUSIC_DIR = "music"
    os.makedirs(MUSIC_DIR, exist_ok=True)
    files = [f for f in os.listdir(MUSIC_DIR) if f.endswith(".mp3")]
    if not files:
        print("⚠️ No music found. Video will have no audio.")
        return None
    chosen = os.path.join(MUSIC_DIR, random.choice(files))
    print(f"🎵 Music selected: {chosen}")
    return chosen

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
        print(f"❌ Error in VIDEO CREATION: {e}")
        traceback.print_exc()
        raise

# ---------------- YOUTUBE UPLOAD ----------------
def upload_to_youtube(video_path, title, description, tags="", hashtags=""):
    try:
        print("🔹 Uploading to YouTube...")
        creds = Credentials.from_authorized_user_file("token.json", ["https://www.googleapis.com/auth/youtube.upload"])
        youtube = build("youtube", "v3", credentials=creds)

        body = {
            "snippet": {
                "title": f"{title} {hashtags}",
                "description": description,
                "tags": tags.split(","),
                "categoryId": "22"
            },
            "status": {"privacyStatus": "public"}
        }

        media = googleapiclient.http.MediaFileUpload(video_path, chunksize=-1, resumable=True)
        request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)
        response = request.execute()
        print(f"✅ Uploaded! Video ID: {response.get('id')}")
        return response.get("id")
    except Exception as e:
        print(f"❌ YouTube upload error: {e}")
        traceback.print_exc()
        raise

# ---------------- MAIN PIPELINE ----------------
if __name__ == "__main__":
    try:
        # 1️⃣ Generate concept + metadata from Gemini
        concept = generate_concept_and_metadata()
        prompt = concept.get("prompt")
        title = concept.get("title")
        description = concept.get("description")
        tags = concept.get("tags")
        hashtags = concept.get("hashtags")

        print(f"📝 Concept: {concept}")

        # 2️⃣ Generate image
        img_path = generate_image_huggingface(prompt)

        # 3️⃣ Pick music
        music_path = get_youtube_music()

        # 4️⃣ Create video
        video_path = create_video(img_path, music_path)

        # 5️⃣ Upload to YouTube
        upload_to_youtube(video_path, title, description, tags, hashtags)

        print("🎉 Pipeline complete!")

    except Exception as e:
        print(f"❌ Pipeline failed: {e}")
        traceback.print_exc()
        

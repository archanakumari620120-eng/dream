import os
import random
import base64
import traceback
import requests
from time import sleep

# MoviePy for video
from moviepy.editor import ImageClip, AudioFileClip, vfx

# YouTube API
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials

# Gemini API
import google.generativeai as genai

# ---------------- CONFIG & DIRECTORIES ----------------
VIDEOS_DIR = "videos"
os.makedirs(VIDEOS_DIR, exist_ok=True)

# ---------------- CHECK SECRETS ----------------
HF_API_TOKEN = os.getenv("HF_API_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
TOKEN_JSON_PATH = "token.json"

if not (HF_API_TOKEN and GEMINI_API_KEY and os.path.exists(TOKEN_JSON_PATH)):
    raise ValueError("❌ Missing secrets! Check HF_API_TOKEN, GEMINI_API_KEY, TOKEN_JSON")

print("✅ All secrets loaded")

genai.configure(api_key=GEMINI_API_KEY)

# ---------------- GEMINI: Generate title, description, tags ----------------
def generate_metadata():
    prompt = (
        "Generate a viral YouTube Short concept with:\n"
        "- Title (catchy)\n"
        "- Description (50-100 words, engaging)\n"
        "- 5-10 tags\n"
        "- 3 hashtags\n"
        "Return as JSON object with keys: title, description, tags, hashtags."
    )
    try:
        response = genai.chat(messages=[{"content": prompt}])
        content = response.last.strip()
        import json
        data = json.loads(content)
        return data
    except Exception as e:
        print(f"❌ Gemini metadata error: {e}")
        raise

# ---------------- HUGGING FACE IMAGE GENERATION ----------------
def generate_image(prompt, model_id="stabilityai/stable-diffusion-xl-base-1.0"):
    headers = {"Authorization": f"Bearer {HF_API_TOKEN}"}
    payload = {"inputs": prompt}

    print("🔹 Hugging Face API request...")
    response = requests.post(f"https://api-inference.huggingface.co/models/{model_id}",
                             headers=headers, json=payload)
    if response.status_code != 200:
        raise Exception(f"Hugging Face API Error: {response.status_code}, {response.text}")
    
    img_path = os.path.join(VIDEOS_DIR, "frame.png")
    with open(img_path, "wb") as f:
        f.write(response.content)
    print(f"✅ Image saved: {img_path}")
    return img_path

# ---------------- VIDEO CREATION ----------------
def create_video(image_path, audio_path=None, output_path="final_video.mp4"):
    try:
        duration = 10
        clip = ImageClip(image_path).set_duration(duration)
        if audio_path:
            audio = AudioFileClip(audio_path)
            if audio.duration < duration:
                audio = audio.fx(vfx.loop, duration=duration)
            clip = clip.set_audio(audio.subclip(0, duration))
        clip.write_videofile(output_path, fps=24, codec="libx264", audio_codec="aac")
        print(f"✅ Video ready: {output_path}")
        return output_path
    except Exception as e:
        print(f"❌ Video creation error: {e}")
        traceback.print_exc()
        raise

# ---------------- YOUTUBE UPLOAD ----------------
def upload_to_youtube(video_path, title, description, tags):
    try:
        creds = Credentials.from_authorized_user_file(TOKEN_JSON_PATH, ["https://www.googleapis.com/auth/youtube.upload"])
        youtube = build("youtube", "v3", credentials=creds)
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
            media_body=video_path
        )
        response = request.execute()
        print(f"✅ Uploaded! Video ID: {response.get('id')}")
        return response.get('id')
    except Exception as e:
        print(f"❌ YouTube upload error: {e}")
        traceback.print_exc()
        raise

# ---------------- MAIN PIPELINE ----------------
if __name__ == "__main__":
    try:
        # 1️⃣ Generate metadata
        meta = generate_metadata()
        title = meta["title"]
        description = meta["description"]
        tags = meta["tags"]

        # 2️⃣ Generate image for concept
        concept_prompt = title + " viral trending YouTube Short image"
        img_path = generate_image(concept_prompt)

        # 3️⃣ Create video
        video_path = create_video(img_path)

        # 4️⃣ Upload to YouTube
        upload_to_youtube(video_path, title, description, tags)
        print("🎉 Pipeline complete!")

    except Exception as e:
        print(f"❌ Pipeline failed: {e}")
        traceback.print_exc()
        

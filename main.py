import os
import random
import traceback
import requests
from time import sleep

# Video processing
from moviepy.editor import ImageClip, AudioFileClip, vfx

# YouTube API
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials

# Gemini AI
import google.generativeai as genai

# ---------------- CONFIG & DIRECTORIES ----------------
VIDEOS_DIR = "videos"
os.makedirs(VIDEOS_DIR, exist_ok=True)

# ---------------- DEBUG SECRET CHECK ----------------
hf_token = os.getenv("HF_API_TOKEN")
gemini_key = os.getenv("GEMINI_API_KEY")
token_json = os.getenv("TOKEN_JSON")

if not hf_token:
    raise ValueError("❌ HF_API_TOKEN missing!")
if not gemini_key:
    raise ValueError("❌ GEMINI_API_KEY missing!")
if not token_json:
    raise ValueError("❌ TOKEN_JSON missing!")

print("✅ All secrets loaded")

# ---------------- GEMINI PROMPT & META GENERATION ----------------
def generate_concept_and_metadata():
    genai.configure(api_key=gemini_key)
    user_prompt = (
        "Generate a viral YouTube Shorts concept with a trending subject. "
        "Provide:\n1. image prompt for a vertical 1080x1920 video\n"
        "2. video title\n3. description\n4. tags (comma separated)\n5. hashtags (space separated)\n"
        "Output in JSON format with keys: prompt, title, description, tags, hashtags"
    )
    response = genai.chat.create(model="gemini-1.5", messages=[{"role":"user","content":user_prompt}])
    content = response.last
    try:
        import json
        data = json.loads(content)
        return data
    except:
        print("⚠️ Gemini output parsing failed, using default concept")
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
    headers = {"Authorization": f"Bearer {hf_token}"}
    payload = {"inputs": prompt}

    print(f"🔹 Hugging Face API request...")
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

# ---------------- MUSIC SELECTION ----------------
def get_youtube_music():
    # Using copyright-free YouTube audio tracks (hardcoded sample or fetch logic)
    # For now, skipping manual selection: return None
    print("⚠️ Using no music (YouTube copyright-free logic can be added)")
    return None

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
def upload_to_youtube(video_path, title, description, tags, hashtags):
    try:
        creds_path = os.path.join(os.getcwd(), "token.json")
        with open(creds_path, "w") as f:
            f.write(token_json)

        creds = Credentials.from_authorized_user_file(creds_path, ["https://www.googleapis.com/auth/youtube.upload"])
        youtube = build("youtube", "v3", credentials=creds)

        request = youtube.videos().insert(
            part="snippet,status",
            body={
                "snippet": {
                    "title": title,
                    "description": description,
                    "tags": tags.split(","),
                    "categoryId": "22"
                },
                "status": {"privacyStatus": "public"}
            },
            media_body=video_path
        )
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
        data = generate_concept_and_metadata()
        print(f"📝 Gemini generated concept: {data}")

        img_path = generate_image_huggingface(data["prompt"])
        music_path = get_youtube_music()
        video_path = create_video(img_path, music_path)

        upload_to_youtube(video_path,
                          title=data["title"],
                          description=data["description"],
                          tags=data["tags"],
                          hashtags=data["hashtags"])

        print("🎉 Pipeline complete!")

    except Exception as e:
        print(f"❌ Pipeline failed: {e}")
        traceback.print_exc()
        

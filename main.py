import os
import random
import traceback
import requests
import json
from time import sleep

# Video processing
from moviepy.editor import ImageClip, AudioFileClip, vfx

# YouTube API
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials

# Gemini AI
import google.generativeai as genai

# YouTube music download
import yt_dlp

# ---------------- CONFIG & DIRECTORIES ----------------
VIDEOS_DIR = "videos"
MUSIC_DIR = "music"
os.makedirs(VIDEOS_DIR, exist_ok=True)
os.makedirs(MUSIC_DIR, exist_ok=True)

# ---------------- SECRETS ----------------
gemini_key = os.getenv("GEMINI_API_KEY")
hf_token = os.getenv("HF_API_TOKEN")
token_json = os.getenv("TOKEN_JSON")

if not gemini_key or not hf_token or not token_json:
    raise ValueError("❌ Missing one of the required secrets!")

print("✅ All secrets loaded")

# ---------------- GEMINI: CONCEPT + METADATA ----------------
def generate_concept_and_metadata():
    genai.configure(api_key=gemini_key)
    user_prompt = (
        "Generate a viral YouTube Shorts concept with a trending subject. "
        "Provide:\n1. image prompt for a vertical 1080x1920 video\n"
        "2. video title\n3. description\n4. tags (comma separated)\n5. hashtags (space separated)\n"
        "Output in JSON format with keys: prompt, title, description, tags, hashtags"
    )

    response = genai.chat(messages=[{"role":"user","content":user_prompt}])
    content = response.last

    try:
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
    headers = {"Authorization": f"Bearer {hf_token}"}
    api_url = f"https://api-inference.huggingface.co/models/{model_id}"
    payload = {"inputs": prompt}

    print(f"🔹 Requesting Hugging Face image...")
    response = requests.post(api_url, headers=headers, json=payload)

    if response.status_code == 503:
        print("⏳ Model loading, waiting 30s...")
        sleep(30)
        response = requests.post(api_url, headers=headers, json=payload)

    if response.status_code != 200:
        error_message = f"❌ Hugging Face API Error: {response.status_code}, {response.text}"
        print(error_message)
        raise Exception(error_message)

    img_path = os.path.join(VIDEOS_DIR, "frame.png")
    with open(img_path, "wb") as f:
        f.write(response.content)

    print(f"✅ Image saved: {img_path}")
    return img_path

# ---------------- YOUTUBE COPYRIGHT-FREE MUSIC ----------------
def download_copyright_free_music(query="relaxing music copyright free"):
    try:
        print(f"🔹 Searching and downloading music from YouTube: {query}")
        ydl_opts = {
            'format': 'bestaudio/best',
            'noplaylist': True,
            'default_search': 'ytsearch',
            'outtmpl': os.path.join(MUSIC_DIR, '%(title)s.%(ext)s'),
            'quiet': True,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(query, download=True)
            if 'entries' in info:
                info = info['entries'][0]
            music_file = os.path.join(MUSIC_DIR, f"{info['title']}.mp3")
            print(f"✅ Music downloaded: {music_file}")
            return music_file
    except Exception as e:
        print(f"⚠️ Music download failed: {e}")
        return None

# ---------------- VIDEO CREATION ----------------
def create_video(image_path, audio_path=None, output_path="final_video.mp4"):
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
def upload_to_youtube(video_path, title, description, tags=[], privacy="public"):
    try:
        creds_data = json.loads(token_json)
        creds = Credentials.from_authorized_user_info(creds_data, ["https://www.googleapis.com/auth/youtube.upload"])
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
                "status": {"privacyStatus": privacy}
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
        concept = generate_concept_and_metadata()
        prompt = concept.get("prompt")
        title = concept.get("title")
        description = concept.get("description")
        tags = concept.get("tags", "").split(",")
        hashtags = concept.get("hashtags", "")

        # Generate image
        img_path = generate_image_huggingface(prompt)

        # Download YouTube copyright-free music
        music_path = download_copyright_free_music(query="copyright free trending music")

        # Create video
        video_path = create_video(img_path, music_path)

        # Upload to YouTube
        upload_to_youtube(video_path, title=f"{title} {hashtags}", description=description, tags=tags, privacy="public")

        print("🎉 Pipeline complete!")
    except Exception as e:
        print(f"❌ Pipeline failed: {e}")
        traceback.print_exc()
        

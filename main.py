import os
import json
import random
import traceback
import requests
from time import sleep
import yt_dlp

# Video processing
from moviepy.editor import ImageClip, AudioFileClip, vfx

# YouTube API
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials

# Gemini AI
import google.generativeai as genai

# ---------------- CONFIG & DIRECTORIES ----------------
VIDEOS_DIR = "videos"
MUSIC_DIR = "music"
os.makedirs(VIDEOS_DIR, exist_ok=True)
os.makedirs(MUSIC_DIR, exist_ok=True)

# ---------------- SECRETS CHECK ----------------
HF_TOKEN = os.getenv("HF_API_TOKEN")
GEMINI_KEY = os.getenv("GEMINI_API_KEY")
TOKEN_JSON = os.getenv("TOKEN_JSON")

if not HF_TOKEN or not GEMINI_KEY or not TOKEN_JSON:
    raise ValueError("❌ Missing secrets! Check HF_API_TOKEN, GEMINI_API_KEY, TOKEN_JSON")
else:
    print("✅ All secrets loaded")

# ---------------- GEMINI SETUP ----------------
genai.configure(api_key=GEMINI_KEY)

# ---------------- METADATA GENERATION ----------------
def generate_metadata():
    user_prompt = (
        "Generate a trending, viral YouTube Shorts video concept. "
        "Return JSON with keys: title, description, tags (list), hashtags (list). "
        "Make it unique, catchy, short, and viral on YouTube Shorts."
    )
    try:
        response = genai.chat(model="gemini-1.5-flash", messages=[{"content": user_prompt}])
        content = response.last or "{}"
        data = json.loads(content)
        return data
    except Exception as e:
        print(f"❌ Error generating metadata: {e}")
        return {"title": "Animal Video", "description": "AI Generated Short", "tags": ["AI","Shorts"], "hashtags":["#AI","#Shorts"]}

# ---------------- IMAGE GENERATION ----------------
def generate_image_huggingface(prompt, model_id="stabilityai/stable-diffusion-xl-base-1.0"):
    headers = {"Authorization": f"Bearer {HF_TOKEN}"}
    api_url = f"https://api-inference.huggingface.co/models/{model_id}"
    payload = {"inputs": prompt}

    print("🔹 Hugging Face API request...")
    response = requests.post(api_url, headers=headers, json=payload)
    if response.status_code == 503:
        print("⏳ Model loading, waiting 30s...")
        sleep(30)
        response = requests.post(api_url, headers=headers, json=payload)
    if response.status_code != 200:
        raise Exception(f"Hugging Face API Error: {response.status_code}, {response.text}")

    img_path = os.path.join(VIDEOS_DIR, "frame.png")
    with open(img_path, "wb") as f:
        f.write(response.content)
    print(f"✅ Image saved: {img_path}")
    return img_path

# ---------------- COPYRIGHT-FREE MUSIC DOWNLOAD ----------------
def download_copyright_free_music():
    """
    YouTube copyright-free playlist se random music download karo.
    """
    playlist_url = "https://www.youtube.com/playlist?list=PLzCxunOM5WFI6H2k8zJpE7E5Wdl66iRSu"  # example
    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": os.path.join(MUSIC_DIR, "%(title)s.%(ext)s"),
        "quiet": True,
        "noplaylist": False,
        "ignoreerrors": True,
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        }],
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([playlist_url])
        files = [os.path.join(MUSIC_DIR, f) for f in os.listdir(MUSIC_DIR) if f.endswith(".mp3")]
        if files:
            chosen = random.choice(files)
            print(f"🎵 Music selected: {chosen}")
            return chosen
        else:
            print("⚠️ No music downloaded, video will be silent.")
            return None
    except Exception as e:
        print(f"❌ Music download error: {e}")
        return None

# ---------------- VIDEO CREATION ----------------
def create_video(image_path, audio_path, output_path="final_video.mp4"):
    try:
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
        print(f"❌ Error creating video: {e}")
        traceback.print_exc()
        raise

# ---------------- YOUTUBE UPLOAD ----------------
def upload_to_youtube(video_path, title, description, tags, privacy="public"):
    try:
        with open("token.json", "w") as f:
            f.write(TOKEN_JSON)
        creds = Credentials.from_authorized_user_file("token.json", ["https://www.googleapis.com/auth/youtube.upload"])
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
        metadata = generate_metadata()
        prompt = f"Vertical 1080x1920 YouTube Short background of {metadata['title']}, ultra-realistic cinematic, trending on YouTube Shorts"
        print(f"📝 Prompt for image: {prompt}")

        img_path = generate_image_huggingface(prompt)
        music_path = download_copyright_free_music()
        video_path = create_video(img_path, music_path)
        upload_to_youtube(video_path, title=metadata['title'], description=metadata['description'], tags=metadata['tags'], privacy="public")

        print("🎉 Pipeline complete!")
    except Exception as e:
        print(f"❌ Pipeline failed: {e}")
        traceback.print_exc()
        

import os
import random
import json
import requests
from datetime import datetime
from moviepy.editor import ImageClip, AudioFileClip
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

# ========= CONFIG =========
VIDEOS_DIR = "videos"
MUSIC_FILE = "music.mp3"   # कोई copyright-free mp3 डाल दो repo में
DURATION = 30              # video length (seconds)
WIDTH, HEIGHT = 1080, 1920 # Shorts format
# ==========================

# Create folders
os.makedirs(VIDEOS_DIR, exist_ok=True)

# 🔑 Load env variables (Secrets)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# YouTube OAuth secrets are handled by GitHub Secrets (TOKEN_JSON + CLIENT_SECRET_JSON)

# ✅ Generate Image from Gemini
def generate_image(prompt):
    url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateImage"
    headers = {"Content-Type": "application/json"}
    params = {"key": GEMINI_API_KEY}
    payload = {
        "prompt": {
            "text": prompt
        }
    }
    r = requests.post(url, headers=headers, params=params, json=payload)
    if r.status_code != 200:
        raise Exception(f"Gemini API Error: {r.text}")
    data = r.json()
    image_b64 = data["candidates"][0]["image"]["base64"]
    img_path = os.path.join(VIDEOS_DIR, "frame.png")
    with open(img_path, "wb") as f:
        f.write(requests.utils.unquote_to_bytes(image_b64))
    return img_path

# ✅ Create Video from Image
def create_video(image_path, output_path):
    img_clip = ImageClip(image_path).set_duration(DURATION).resize((WIDTH, HEIGHT))
    if os.path.exists(MUSIC_FILE):
        audio = AudioFileClip(MUSIC_FILE).subclip(0, DURATION)
        video = img_clip.set_audio(audio)
    else:
        video = img_clip
    video.write_videofile(output_path, fps=30)

# ✅ Upload to YouTube
def upload_to_youtube(video_path, title, description, tags):
    creds = Credentials.from_authorized_user_info(
        json.loads(os.getenv("TOKEN_JSON")),
        ["https://www.googleapis.com/auth/youtube.upload"]
    )
    youtube = build("youtube", "v3", credentials=creds)

    body = {
        "snippet": {
            "title": title,
            "description": description,
            "tags": tags,
            "categoryId": "22"  # People & Blogs
        },
        "status": {
            "privacyStatus": "public",
            "selfDeclaredMadeForKids": False,
        }
    }

    request = youtube.videos().insert(
        part="snippet,status",
        body=body,
        media_body=video_path
    )
    response = request.execute()
    print("✅ Uploaded:", response["id"])

# ✅ Main Flow
def main():
    # 1. Get random prompt
    with open("quotes.txt", "r", encoding="utf-8") as f:
        prompts = [line.strip() for line in f if line.strip()]
    prompt = random.choice(prompts)

    # 2. Generate image
    img_path = generate_image(prompt)

    # 3. Create video
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    video_path = os.path.join(VIDEOS_DIR, f"video_{timestamp}.mp4")
    create_video(img_path, video_path)

    # 4. Upload video
    title = f"{prompt} #shorts"
    description = f"AI Generated Shorts - {prompt}"
    tags = ["AI", "shorts", "motivation", "quotes"]
    upload_to_youtube(video_path, title, description, tags)

if __name__ == "__main__":
    main()
    

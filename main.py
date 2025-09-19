import os
import random
import json
import base64
from datetime import datetime
from moviepy.editor import ImageClip, AudioFileClip
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
import google.generativeai as genai

# ========= CONFIG =========
VIDEOS_DIR = "videos"
MUSIC_FILE = "music.mp3"   # copyright-free mp3
DURATION = 30              # video length (seconds)
WIDTH, HEIGHT = 1080, 1920 # Shorts format
# ==========================

os.makedirs(VIDEOS_DIR, exist_ok=True)

# 🔑 Load env variables (Secrets)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# ✅ Generate Image from Gemini
def generate_image(prompt):
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel("imagen-3-flash")

        # API Call (no sample_count / candidate_count needed)
        response = model.generate_content(prompt)

        # Base64 निकालना
        image_b64 = response.candidates[0].content.parts[0].inline_data.data

        # Save image
        img_path = os.path.join(VIDEOS_DIR, "frame.png")
        with open(img_path, "wb") as f:
            f.write(base64.b64decode(image_b64))

        print("✅ Image generated successfully.")
        return img_path

    except Exception as e:
        print(f"❌ Error generating image: {e}")
        raise

# ✅ Create Video
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
    # 1. Prompt / Quote चुनो
    with open("quotes.txt", "r", encoding="utf-8") as f:
        prompts = [line.strip() for line in f if line.strip()]
    prompt = random.choice(prompts)

    # 2. Gemini से Image Generate
    img_path = generate_image(prompt)

    # 3. Video बनाओ
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    video_path = os.path.join(VIDEOS_DIR, f"video_{timestamp}.mp4")
    create_video(img_path, video_path)

    # 4. Upload to YouTube
    title = f"{prompt} #shorts"
    description = f"AI Generated Shorts - {prompt}"
    tags = ["AI", "shorts", "motivation", "quotes"]
    upload_to_youtube(video_path, title, description, tags)

if __name__ == "__main__":
    main()
        

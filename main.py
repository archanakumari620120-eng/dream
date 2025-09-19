# ---------------- DEBUG SECRET CHECK ----------------
hf_token = os.getenv("HF_API_TOKEN")
if not hf_token:
    raise ValueError("❌ HF_API_TOKEN missing! Check GitHub Secrets.")
else:
    print("✅ HF_API_TOKEN successfully loaded (length:", len(hf_token), ")")
    
import os
import random
import requests
import traceback
from time import sleep
from datetime import datetime

# Video processing
from moviepy.editor import ImageClip, AudioFileClip, vfx

# YouTube API
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials

# ---------------- CONFIG ----------------
VIDEOS_DIR = "videos"
MUSIC_DIR = "music"
os.makedirs(VIDEOS_DIR, exist_ok=True)
os.makedirs(MUSIC_DIR, exist_ok=True)

# ---------------- PROMPT GENERATOR ----------------
def generate_trending_prompt():
    subjects = ["cat", "dog", "man", "woman", "human", "animal", "city", "nature", "abstract art"]
    styles = [
        "ultra-realistic cinematic, trending on YouTube Shorts",
        "vibrant digital art, 3D render, highly detailed, viral style",
        "epic concept art, surreal and abstract, popular style",
        "cinematic lighting, modern illustration, eye-catching composition",
        "trending AI art, high quality, inspirational, vertical format"
    ]
    subject = random.choice(subjects)
    style = random.choice(styles)
    return f"Vertical 1080x1920 YouTube Short background of a {subject}, {style}"

# ---------------- IMAGE GENERATION (Hugging Face) ----------------
def generate_image_huggingface(prompt, model_id="stabilityai/stable-diffusion-xl-base-1.0"):
    try:
        api_token = os.getenv("HF_API_TOKEN")
        if not api_token:
            raise ValueError("❌ HF_API_TOKEN secret missing!")

        api_url = f"https://api-inference.huggingface.co/models/{model_id}"
        headers = {"Authorization": f"Bearer {api_token}"}
        payload = {"inputs": prompt}

        print(f"🖼️ Generating image from Hugging Face: {prompt}")
        response = requests.post(api_url, headers=headers, json=payload)

        if response.status_code == 503:
            print("⏳ Model loading... waiting 30s")
            sleep(30)
            response = requests.post(api_url, headers=headers, json=payload)

        if response.status_code != 200:
            raise Exception(f"Hugging Face API error {response.status_code}: {response.text}")

        img_path = os.path.join(VIDEOS_DIR, "frame.png")
        with open(img_path, "wb") as f:
            f.write(response.content)

        print(f"✅ Image saved at {img_path}")
        return img_path

    except Exception as e:
        print(f"❌ Error in image generation: {e}")
        traceback.print_exc()
        raise

# ---------------- MUSIC ----------------
def get_random_music():
    try:
        files = [f for f in os.listdir(MUSIC_DIR) if f.endswith((".mp3", ".wav"))]
        if not files:
            print("⚠️ No music found. Video will be silent.")
            return None
        chosen = os.path.join(MUSIC_DIR, random.choice(files))
        print(f"🎵 Music chosen: {chosen}")
        return chosen
    except Exception as e:
        print(f"❌ Error selecting music: {e}")
        traceback.print_exc()
        raise

# ---------------- VIDEO CREATION ----------------
def create_video(image_path, audio_path, output_path="final_video.mp4"):
    try:
        print("🎬 Creating video...")
        clip_duration = 10  # default length 10s
        clip = ImageClip(image_path).set_duration(clip_duration)

        if audio_path and os.path.exists(audio_path):
            audio_clip = AudioFileClip(audio_path)
            if audio_clip.duration < clip_duration:
                audio_clip = audio_clip.fx(vfx.loop, duration=clip_duration)
            clip = clip.set_audio(audio_clip.subclip(0, clip_duration))

        clip.write_videofile(output_path, fps=24, codec="libx264", audio_codec="aac")
        print(f"✅ Video saved: {output_path}")
        return output_path

    except Exception as e:
        print(f"❌ Error in video creation: {e}")
        traceback.print_exc()
        raise

# ---------------- YOUTUBE UPLOAD ----------------
def upload_to_youtube(video_path, title, description, tags):
    try:
        print("📤 Uploading to YouTube...")
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
                "status": {"privacyStatus": "public"}
            },
            media_body=video_path
        )

        response = request.execute()
        print(f"✅ Uploaded successfully. Video ID: {response.get('id')}")
        return response.get("id")

    except Exception as e:
        print(f"❌ Error in YouTube upload: {e}")
        traceback.print_exc()
        raise

# ---------------- MAIN PIPELINE ----------------
if __name__ == "__main__":
    try:
        # 1️⃣ Prompt
        prompt = generate_trending_prompt()
        print(f"📝 Prompt: {prompt}")

        # 2️⃣ Image
        img_path = generate_image_huggingface(prompt)

        # 3️⃣ Music
        music_path = get_random_music()

        # 4️⃣ Video
        video_path = create_video(img_path, music_path)

        # 5️⃣ YouTube Upload (Dynamic metadata)
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        title = f"{prompt} | Viral AI Shorts {now}"
        description = f"🔥 Auto-generated AI Shorts\nPrompt: {prompt}\n#AI #Shorts #Trending #Viral"
        tags = ["AI", "Shorts", "Trending", "Viral", "Motivation", "Art"]

        upload_to_youtube(video_path, title, description, tags)

        print("🎉 Full pipeline finished successfully!")

    except Exception as e:
        print(f"❌ Pipeline failed: {e}")
        traceback.print_exc()
            

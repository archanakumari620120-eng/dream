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

# ---------------- DIRECTORIES ----------------
VIDEOS_DIR = "videos"
MUSIC_DIR = "music"
os.makedirs(VIDEOS_DIR, exist_ok=True)
os.makedirs(MUSIC_DIR, exist_ok=True)

# ---------------- DEBUG SECRET CHECK ----------------
hf_token = os.getenv("HF_API_TOKEN")
if not hf_token:
    raise ValueError("❌ HF_API_TOKEN missing! Check GitHub Secrets.")
else:
    print("✅ HF_API_TOKEN successfully loaded (length:", len(hf_token), ")")

# ---------------- HUGGING FACE IMAGE GENERATION ----------------
def generate_image_huggingface(prompt, model_id="stabilityai/stable-diffusion-xl-base-1.0"):
    api_token = os.getenv("HF_API_TOKEN")
    if not api_token:
        raise ValueError("❌ HF_API_TOKEN secret missing!")

    api_url = f"https://api-inference.huggingface.co/models/{model_id}"
    headers = {"Authorization": f"Bearer {api_token}"}
    payload = {"inputs": prompt}

    print(f"🔹 Hugging Face API को रिक्वेस्ट भेज रहा है...")
    response = requests.post(api_url, headers=headers, json=payload)

    if response.status_code == 503:
        print("⏳ मॉडल लोड हो रहा है, 30 सेकंड इंतज़ार...")
        sleep(30)
        response = requests.post(api_url, headers=headers, json=payload)

    if response.status_code != 200:
        error_message = f"❌ Hugging Face API Error: {response.status_code}, {response.text}"
        print(error_message)
        raise Exception(error_message)

    image_bytes = response.content
    img_path = os.path.join(VIDEOS_DIR, "frame.png")
    with open(img_path, "wb") as f:
        f.write(image_bytes)

    print(f"✅ इमेज सेव हो गई: {img_path}")
    return img_path

# ---------------- MUSIC SELECTION ----------------
def get_random_music():
    try:
        files = [f for f in os.listdir(MUSIC_DIR) if f.endswith((".mp3", ".wav"))]
        if not files:
            print("⚠️ कोई म्यूज़िक नहीं मिला। वीडियो बिना ऑडियो बनेगा।")
            return None
        chosen = os.path.join(MUSIC_DIR, random.choice(files))
        print(f"🎵 म्यूज़िक चुना गया: {chosen}")
        return chosen
    except Exception as e:
        print(f"❌ म्यूज़िक चुनने में एरर: {e}")
        raise

# ---------------- VIDEO CREATION ----------------
def create_video(image_path, audio_path, output_path="final_video.mp4"):
    try:
        print("🔹 वीडियो बना रहा है...")
        clip_duration = 10
        clip = ImageClip(image_path).set_duration(clip_duration)

        if audio_path and os.path.exists(audio_path):
            audio_clip = AudioFileClip(audio_path)
            if audio_clip.duration < clip_duration:
                audio_clip = audio_clip.fx(vfx.loop, duration=clip_duration)
            clip = clip.set_audio(audio_clip.subclip(0, clip_duration))

        clip.write_videofile(output_path, fps=24, codec="libx264", audio_codec="aac")
        print(f"✅ वीडियो बन गया: {output_path}")
        return output_path
    except Exception as e:
        print(f"❌ Error in VIDEO CREATION: {e}")
        traceback.print_exc()
        raise

# ---------------- YOUTUBE UPLOAD ----------------
def upload_to_youtube(video_path, title="AI Short Video", description="Auto-generated Short using AI"):
    try:
        print("🔹 YouTube पर अपलोड शुरू...")
        creds = Credentials.from_authorized_user_file("token.json", ["https://www.googleapis.com/auth/youtube.upload"])
        youtube = build("youtube", "v3", credentials=creds)

        request = youtube.videos().insert(
            part="snippet,status",
            body={
                "snippet": {
                    "title": title,
                    "description": description,
                    "tags": ["AI", "Shorts", "Viral", "Trending", "Motivation"],
                    "categoryId": "22"
                },
                "status": {"privacyStatus": "private"}
            },
            media_body=video_path
        )

        response = request.execute()
        print(f"✅ अपलोड सफल! Video ID: {response.get('id')}")
        return response.get("id")
    except Exception as e:
        print(f"❌ YouTube upload error: {e}")
        traceback.print_exc()
        raise

# ---------------- MAIN PIPELINE ----------------
if __name__ == "__main__":
    try:
        # Trending viral concepts example
        concepts = ["dog", "cat", "human", "woman", "man", "animal", "nature"]
        concept = random.choice(concepts)
        prompt = f"Vertical 1080x1920 YouTube Short background of a {concept}, ultra-realistic cinematic, trending on YouTube Shorts"
        description = f"AI generated viral YouTube Short featuring {concept}, trending content for viewers."

        print(f"📝 Prompt: {prompt}")

        # 1️⃣ Generate image
        img_path = generate_image_huggingface(prompt)

        # 2️⃣ Pick music
        music_path = get_random_music()

        # 3️⃣ Create video
        video_path = create_video(img_path, music_path)

        # 4️⃣ Upload to YouTube
        upload_to_youtube(video_path, title=f"{concept.capitalize()} Video #Shorts", description=description)

        print("🎉 Pipeline complete!")

    except Exception as e:
        print(f"❌ Pipeline failed: {e}")
        traceback.print_exc()

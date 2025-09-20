import os
import random
import traceback
import requests
from time import sleep
from moviepy.editor import ImageClip, AudioFileClip, vfx
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials

# ---------------- DIRECTORIES ----------------
VIDEOS_DIR = "videos"
MUSIC_DIR = "music"
os.makedirs(VIDEOS_DIR, exist_ok=True)
os.makedirs(MUSIC_DIR, exist_ok=True)

# ---------------- DEBUG SECRET ----------------
hf_token = os.getenv("HF_API_TOKEN")
if not hf_token:
    raise ValueError("❌ HF_API_TOKEN missing! Check GitHub Secrets.")
else:
    print("✅ HF_API_TOKEN loaded (length:", len(hf_token), ")")

# ---------------- IMAGE GENERATION ----------------
def generate_image_huggingface(prompt, model_id="stabilityai/stable-diffusion-xl-base-1.0"):
    headers = {"Authorization": f"Bearer {hf_token}"}
    payload = {"inputs": prompt}

    print(f"🔹 Hugging Face API request...")
    response = requests.post(f"https://api-inference.huggingface.co/models/{model_id}", headers=headers, json=payload)

    if response.status_code == 503:
        print("⏳ Model loading, wait 30s...")
        sleep(30)
        response = requests.post(f"https://api-inference.huggingface.co/models/{model_id}", headers=headers, json=payload)

    if response.status_code != 200:
        raise Exception(f"❌ HF API Error {response.status_code}: {response.text}")

    img_path = os.path.join(VIDEOS_DIR, "frame.png")
    with open(img_path, "wb") as f:
        f.write(response.content)
    print(f"✅ Image saved: {img_path}")
    return img_path

# ---------------- MUSIC SELECTION ----------------
def get_random_music():
    files = [f for f in os.listdir(MUSIC_DIR) if f.endswith((".mp3", ".wav"))]
    if not files:
        print("⚠️ No music found, video will have no audio.")
        return None
    chosen = os.path.join(MUSIC_DIR, random.choice(files))
    print(f"🎵 Selected music: {chosen}")
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
        print(f"❌ VIDEO CREATION ERROR: {e}")
        traceback.print_exc()
        raise

# ---------------- YOUTUBE UPLOAD ----------------
def upload_to_youtube(video_path, title="AI Short Video", description="Auto-generated Short using AI"):
    try:
        print("🔹 Uploading to YouTube...")
        creds = Credentials.from_authorized_user_file("token.json", ["https://www.googleapis.com/auth/youtube.upload"])
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
        print(f"✅ Uploaded! Video ID: {response.get('id')}")
        return response.get("id")
    except Exception as e:
        print(f"❌ YOUTUBE UPLOAD ERROR: {e}")
        traceback.print_exc()
        raise

# ---------------- MAIN PIPELINE ----------------
if __name__ == "__main__":
    try:
        concepts = ["dog", "cat", "human", "woman", "man", "animal", "bird", "horse"]
        concept = random.choice(concepts)
        prompt = f"Vertical 1080x1920 YouTube Short background of a {concept}, ultra-realistic cinematic, trending on YouTube Shorts"
        print(f"📝 Prompt: {prompt}")

        img_path = generate_image_huggingface(prompt)
        music_path = get_random_music()
        video_path = create_video(img_path, music_path)
        upload_to_youtube(video_path, title=f"{concept.capitalize()} Video #Shorts", description=f"AI Generated Viral {concept.capitalize()} Short")
        print("🎉 Pipeline complete!")

    except Exception as e:
        print(f"❌ Pipeline failed: {e}")
        traceback.print_exc()
        

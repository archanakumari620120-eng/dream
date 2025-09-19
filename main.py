import os
import random
import traceback
import requests
from time import sleep
from moviepy.editor import ImageClip, AudioFileClip, vfx
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials

# ---------------- CONFIG & DIRECTORIES ----------------
VIDEOS_DIR = "videos"
MUSIC_DIR = "music"
os.makedirs(VIDEOS_DIR, exist_ok=True)
os.makedirs(MUSIC_DIR, exist_ok=True)

# ---------------- DEBUG SECRET CHECK ----------------
hf_token = os.getenv("HF_API_TOKEN")
if not hf_token:
    raise ValueError("❌ HF_API_TOKEN missing! Set GitHub Secret 'HF_API_TOKEN'.")
else:
    print("✅ HF_API_TOKEN successfully loaded (length:", len(hf_token), ")")

# ---------------- HUGGING FACE IMAGE GENERATION ----------------
def generate_image_huggingface(prompt, model_id="stabilityai/stable-diffusion-xl-base-1.0"):
    api_token = os.getenv("HF_API_TOKEN")
    api_url = f"https://api-inference.huggingface.co/models/{model_id}"
    headers = {"Authorization": f"Bearer {api_token}"}
    payload = {"inputs": prompt}

    print("🔹 Sending request to Hugging Face API...")
    response = requests.post(api_url, headers=headers, json=payload)

    if response.status_code == 503:
        print("⏳ Model loading, waiting 30 sec...")
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

# ---------------- MUSIC SELECTION ----------------
def get_random_music():
    files = [f for f in os.listdir(MUSIC_DIR) if f.endswith((".mp3", ".wav"))]
    if not files:
        print("⚠️ No music found. Video will be silent.")
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
        print(f"❌ Error in VIDEO CREATION: {e}")
        traceback.print_exc()
        raise

# ---------------- YOUTUBE UPLOAD ----------------
def upload_to_youtube(video_path, title, description):
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
                    "tags": ["AI", "Shorts", "Viral", "Motivation"],
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
        print(f"❌ Error in YOUTUBE UPLOAD: {e}")
        traceback.print_exc()
        raise

# ---------------- MAIN PIPELINE ----------------
if __name__ == "__main__":
    try:
        # Example viral prompt
        concept = random.choice(["dog", "cat", "man", "woman", "animal", "nature"])
        prompt = f"Vertical 1080x1920 YouTube Short background of a {concept}, ultra-realistic cinematic, trending on YouTube Shorts"
        description = f"AI Generated Viral {concept.capitalize()} Video #Shorts"

        print(f"📝 Prompt: {prompt}")

        img_path = generate_image_huggingface(prompt)
        music_path = get_random_music()
        video_path = create_video(img_path, music_path)
        upload_to_youtube(video_path, title=f"{concept.capitalize()} Video #Shorts", description=description)

        print("🎉 Pipeline complete!")
    except Exception as e:
        print(f"❌ Pipeline failed: {e}")
        traceback.print_exc()
        

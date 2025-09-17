import os
import random
import time
import json
from moviepy.editor import ImageClip, AudioFileClip
from diffusers import StableDiffusionPipeline
from PIL import Image, ImageDraw
import torch
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# 📂 Directories
IMAGES_DIR = "images"
MUSIC_DIR = "music"
VIDEOS_DIR = "videos"

os.makedirs(IMAGES_DIR, exist_ok=True)
os.makedirs(MUSIC_DIR, exist_ok=True)
os.makedirs(VIDEOS_DIR, exist_ok=True)

# 🎯 Config
video_duration = 10
topic = "Motivational Quotes"

# 🔑 GitHub Secrets (JSON as string)
CLIENT_SECRET_JSON = os.getenv("CLIENT_SECRET_JSON")
TOKEN_JSON = os.getenv("TOKEN_JSON")

# 🤖 AI pipeline
device = "cuda" if torch.cuda.is_available() else "cpu"
pipe = StableDiffusionPipeline.from_pretrained(
    "runwayml/stable-diffusion-v1-5",
    torch_dtype=torch.float32  # ✅ CPU safe
).to(device)

# 🖼️ Generate AI or fallback image
def generate_image(i):
    try:
        prompt = f"Viral YouTube Short image about {topic}"
        result = pipe(prompt, height=512, width=512, num_inference_steps=20)

        if result and hasattr(result, "images") and len(result.images) > 0:
            image = result.images[0]
        else:
            raise ValueError("Pipeline returned no image")

        path = os.path.join(IMAGES_DIR, f"image_{i}.png")
        image.save(path)
        return path

    except Exception as e:
        print(f"⚠️ Image generation failed for {i}, fallback used: {e}")
        fallback = Image.new("RGB", (512, 512), color=(0, 0, 0))
        d = ImageDraw.Draw(fallback)
        d.text((50, 250), f"Video {i} - {topic}", fill=(255, 255, 255))
        path = os.path.join(IMAGES_DIR, f"image_fallback_{i}.png")
        fallback.save(path)
        return path

# 🎵 Pick random music
def get_music():
    try:
        files = [f for f in os.listdir(MUSIC_DIR) if f.endswith(".mp3")]
        if files:
            return os.path.join(MUSIC_DIR, random.choice(files))
    except Exception as e:
        print(f"⚠️ Music selection failed: {e}")
    return None

# 🎬 Create video
def create_video(i, img, audio):
    try:
        path = os.path.join(VIDEOS_DIR, f"video_{i}.mp4")
        clip = ImageClip(img, duration=video_duration)

        if audio and os.path.exists(audio):
            audio_clip = AudioFileClip(audio)
            clip = clip.set_audio(audio_clip)
        else:
            print(f"⚠️ No audio for video {i}, silent video.")

        clip.write_videofile(path, fps=24, codec="libx264", audio_codec="aac")
        return path
    except Exception as e:
        print(f"❌ Video creation failed {i}: {e}")
        return None

# 📤 YouTube upload
def upload_to_youtube(video_path, title, description, tags=None, category="22", privacy="public"):
    try:
        token_data = json.loads(TOKEN_JSON)
        creds = Credentials.from_authorized_user_info(token_data, ["https://www.googleapis.com/auth/youtube.upload"])
        youtube = build("youtube", "v3", credentials=creds)

        body = {
            "snippet": {
                "title": title,
                "description": description,
                "tags": tags or ["automation", "shorts", "ai"],
                "categoryId": category,
            },
            "status": {
                "privacyStatus": privacy,
                "selfDeclaredMadeForKids": False,
            },
        }

        media = MediaFileUpload(video_path, chunksize=-1, resumable=True, mimetype="video/*")
        request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)
        response = request.execute()

        print(f"📤 Uploaded: https://youtu.be/{response['id']}")
        return True
    except Exception as e:
        print(f"❌ Upload failed: {e}")
        return False

# 🚀 Automation flow
def run_automation(total_videos=1):
    start = time.time()
    success, fail, uploaded, upload_fail = 0, 0, 0, 0

    for i in range(total_videos):
        print(f"\n🎬 Starting video {i}")
        img = generate_image(i)
        audio = get_music()
        video = create_video(i, img, audio)

        if video:
            print(f"✅ Video {i} created: {video}")
            success += 1

            if upload_to_youtube(video, f"My Auto Video {i}", "Auto generated AI Shorts"):
                print(f"📤 Video {i} uploaded ✅")
                uploaded += 1
            else:
                print(f"❌ Upload failed {i}")
                upload_fail += 1
        else:
            fail += 1

    duration = round(time.time() - start, 2)
    print("\n" + "="*40)
    print("📊 SUMMARY")
    print(f"   🎬 Generated: {success} success / {fail} failed")
    print(f"   📤 Uploaded: {uploaded} success / {upload_fail} failed")
    print(f"   ⏱️ Time Taken: {duration} sec")
    print("="*40 + "\n")

if __name__ == "__main__":
    run_automation(total_videos=2)
        

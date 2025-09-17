    import os
import random
import tempfile
import json
from moviepy.editor import ImageClip, AudioFileClip
from diffusers import StableDiffusionPipeline
import torch
from PIL import Image, ImageDraw
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials

# Config
VIDEO_DURATION = 10
QUOTES_FILE = "quotes.txt"

# Directories
IMAGES_DIR = "images"
os.makedirs(IMAGES_DIR, exist_ok=True)

# Stable Diffusion
device = "cuda" if torch.cuda.is_available() else "cpu"
pipe = StableDiffusionPipeline.from_pretrained(
    "runwayml/stable-diffusion-v1-5", torch_dtype=torch.float32
).to(device)

# Load quotes
with open(QUOTES_FILE, "r", encoding="utf-8") as f:
    QUOTES = [line.strip() for line in f if line.strip()]

# Get copyright-free music
def get_youtube_music():
    silent_path = "music/silence.mp3"
    return silent_path if os.path.exists(silent_path) else None

# Generate AI image with fallback
def generate_image(quote):
    try:
        prompt = f"Ultra realistic cinematic illustration, Indian style, motivational theme: {quote}"
        result = pipe(prompt, height=512, width=512, num_inference_steps=20)
        img_path = os.path.join(IMAGES_DIR, "image_tmp.png")
        result.images[0].save(img_path)
        return img_path
    except Exception:
        img = Image.new("RGB", (512, 512), (0, 0, 0))
        draw = ImageDraw.Draw(img)
        draw.text((20, 250), quote[:40], fill=(255, 255, 255))
        fallback_path = os.path.join(IMAGES_DIR, "image_tmp.png")
        img.save(fallback_path)
        return fallback_path

# Create temporary video
def create_video(image_path, audio_path):
    clip = ImageClip(image_path, duration=VIDEO_DURATION)
    if audio_path and os.path.exists(audio_path):
        clip = clip.set_audio(AudioFileClip(audio_path))
    tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
    clip.write_videofile(tmp_file.name, fps=24, codec="libx264", audio_codec="aac")
    clip.close()
    return tmp_file.name

# Upload video to YouTube using secrets
def upload_youtube(video_path, quote):
    token_json_str = os.environ.get("TOKEN_JSON")
    client_secret_str = os.environ.get("CLIENT_SECRET_JSON")
    if not token_json_str or not client_secret_str:
        raise ValueError("TOKEN_JSON or CLIENT_SECRET_JSON not set in secrets")
    
    creds_dict = json.loads(token_json_str)
    creds = Credentials.from_authorized_user_info(creds_dict, ["https://www.googleapis.com/auth/youtube.upload"])
    
    youtube = build("youtube", "v3", credentials=creds)

    title = f"{quote[:60]} | Motivational Shorts"
    description = f"Motivational Quote: {quote}\n#motivation #shorts #inspiration #life"
    tags = ["motivation", "shorts", "inspiration", "success", "life"]
    body = {
        "snippet": {"title": title, "description": description, "tags": tags, "categoryId": "22"},
        "status": {"privacyStatus": "public"}
    }

    media = MediaFileUpload(video_path, chunksize=-1, resumable=True, mimetype="video/*")
    req = youtube.videos().insert(part="snippet,status", body=body, media_body=media)
    res = req.execute()
    print(f"✅ Uploaded: https://youtu.be/{res['id']}")

# Main automation
def run():
    quote = random.choice(QUOTES)
    print(f"🎬 Creating video for quote: {quote}")
    img_path = generate_image(quote)
    audio_path = get_youtube_music()
    video_path = create_video(img_path, audio_path)
    upload_youtube(video_path, quote)
    os.remove(video_path)
    print("🎉 Done, temporary video deleted")

if __name__ == "__main__":
    run()

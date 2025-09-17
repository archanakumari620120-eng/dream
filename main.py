import os
import random
import subprocess
from datetime import datetime
from moviepy.editor import *
from PIL import Image, ImageDraw, ImageFont
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials

# ------------------ CONFIG ------------------
VIDEOS_DIR = "videos"
IMAGES_DIR = "images"
MUSIC_DIR = "music"
os.makedirs(VIDEOS_DIR, exist_ok=True)
os.makedirs(IMAGES_DIR, exist_ok=True)
os.makedirs(MUSIC_DIR, exist_ok=True)

WIDTH, HEIGHT = 1080, 1920
VIDEO_DURATION = 15

# ------------------ LOAD QUOTES ------------------
with open("quotes.txt", "r", encoding="utf-8") as f:
    QUOTES = [q.strip() for q in f.readlines() if q.strip()]

# ------------------ HELPER: CREATE TEXT CLIP ------------------
def create_text_clip(text, size=(WIDTH, HEIGHT), fontsize=70, color="white", bg_color="black"):
    img = Image.new("RGB", size, color=bg_color)
    draw = ImageDraw.Draw(img)

    try:
        font = ImageFont.truetype("DejaVuSans-Bold.ttf", fontsize)
    except:
        font = ImageFont.load_default()

    # Word wrapping
    lines, line = [], ""
    for word in text.split():
        if draw.textlength(line + " " + word, font=font) <= size[0] - 100:
            line += " " + word
        else:
            lines.append(line.strip())
            line = word
    lines.append(line.strip())

    # Vertical centering
    total_h = sum([draw.textbbox((0,0), l, font=font)[3] for l in lines])
    y = (size[1] - total_h) // 2

    for l in lines:
        w = draw.textlength(l, font=font)
        x = (size[0] - w) // 2
        draw.text((x, y), l, font=font, fill=color)
        y += fontsize + 10

    frame = np.array(img)
    return ImageClip(frame).set_duration(VIDEO_DURATION)

# ------------------ HELPER: DOWNLOAD MUSIC ------------------
def get_music():
    local_music = [f for f in os.listdir(MUSIC_DIR) if f.endswith((".mp3", ".wav"))]
    if local_music:
        return os.path.join(MUSIC_DIR, random.choice(local_music))

    print("🎵 Downloading free copyright-free track...")
    url = "https://www.youtube.com/watch?v=jfKfPfyJRdk"  # example free track
    output_path = os.path.join(MUSIC_DIR, "bg.mp3")
    try:
        subprocess.run(
            ["yt-dlp", "-f", "bestaudio", "--extract-audio", "--audio-format", "mp3",
             "-o", output_path, url],
            check=True
        )
        return output_path
    except Exception as e:
        print("⚠️ Music download failed:", e)
        return None

# ------------------ CREATE VIDEO ------------------
def create_quote_video(quote, output_path, use_ai_image=False):
    if use_ai_image:
        # Manual AI image generation placeholder
        img_path = os.path.join(IMAGES_DIR, "ai_image.png")
        if not os.path.exists(img_path):
            # Implement your AI image generation logic here
            # Currently creating a black image placeholder
            img = Image.new("RGB", (WIDTH, HEIGHT), color=(0,0,0))
            img.save(img_path)
        clip = ImageClip(img_path).set_duration(VIDEO_DURATION)
    else:
        clip = create_text_clip(quote)

    music_file = get_music()
    if music_file:
        audio = AudioFileClip(music_file).subclip(0, VIDEO_DURATION)
        clip = clip.set_audio(audio)

    clip.write_videofile(output_path, fps=24, codec="libx264", audio_codec="aac")

# ------------------ UPLOAD TO YOUTUBE ------------------
def upload_youtube(video_file, quote):
    creds = Credentials.from_authorized_user_file("token.json", ["https://www.googleapis.com/auth/youtube.upload"])
    youtube = build("youtube", "v3", credentials=creds)

    title = f"{quote[:60]} | Motivational Shorts"
    description = f"{quote}\n#motivation #shorts #inspiration #india"
    tags = ["motivation", "shorts", "inspiration", "success", "life"]

    request_body = {
        "snippet": {
            "title": title,
            "description": description,
            "tags": tags,
            "categoryId": "22"
        },
        "status": {"privacyStatus": "public"}
    }

    media = MediaFileUpload(video_file, chunksize=-1, resumable=True, mimetype="video/*")
    request = youtube.videos().insert(part="snippet,status", body=request_body, media_body=media)
    response = request.execute()
    print(f"✅ Uploaded: https://youtu.be/{response['id']}")

# ------------------ MAIN AUTOMATION ------------------
def main():
    # 1️⃣ Ready video check
    ready_videos = [f for f in os.listdir(VIDEOS_DIR) if f.endswith(".mp4")]
    if ready_videos:
        video_file = os.path.join(VIDEOS_DIR, random.choice(ready_videos))
        print(f"📤 Uploading existing video: {video_file}")
        upload_youtube(video_file, "Ready-made video")
        os.remove(video_file)
        return

    # 2️⃣ Generate new video
    quote = random.choice(QUOTES)
    print(f"🎬 Generating new video with quote: {quote}")
    output_path = os.path.join(VIDEOS_DIR, "quote_video.mp4")

    # Toggle use_ai_image=True to generate AI image video, else False for black screen + text
    create_quote_video(quote, output_path, use_ai_image=False)
    upload_youtube(output_path, quote)
    os.remove(output_path)

if __name__ == "__main__":
    main()
    

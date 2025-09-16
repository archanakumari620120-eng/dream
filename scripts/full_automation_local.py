import os
import random
from datetime import datetime
from moviepy.editor import ImageClip, AudioFileClip
from diffusers import StableDiffusionPipeline
import torch
from PIL import Image, ImageDraw

# 📂 Directories
IMAGES_DIR = "images"
MUSIC_DIR = "music"
VIDEOS_DIR = "videos"

os.makedirs(IMAGES_DIR, exist_ok=True)
os.makedirs(MUSIC_DIR, exist_ok=True)
os.makedirs(VIDEOS_DIR, exist_ok=True)

# 🎯 Video config
video_duration = 10
topic = "Motivational Quotes"

# 🤖 AI pipeline setup
device = "cuda" if torch.cuda.is_available() else "cpu"
pipe = StableDiffusionPipeline.from_pretrained(
    "runwayml/stable-diffusion-v1-5",
    torch_dtype=torch.float32  # ✅ float16 hata diya (CPU ke liye safe)
).to(device)


# 🖼️ Image generation with fallback
def generate_image(i):
    try:
        prompt = f"Viral YouTube Short image about {topic}"
        result = pipe(prompt, height=512, width=512, num_inference_steps=20)

        if result and hasattr(result, "images") and len(result.images) > 0:
            image = result.images[0]
        else:
            raise ValueError("Diffusion pipeline returned no image")

        path = os.path.join(IMAGES_DIR, f"image_{i}.png")
        image.save(path)
        return path

    except Exception as e:
        print(f"⚠️ Image generation failed for video {i}, fallback: {e}")
        fallback = Image.new("RGB", (512, 512), color=(0, 0, 0))
        d = ImageDraw.Draw(fallback)
        d.text((50, 250), f"Video {i} - {topic}", fill=(255, 255, 255))
        path = os.path.join(IMAGES_DIR, f"image_fallback_{i}.png")
        fallback.save(path)
        return path


# 🎵 Select random music
def get_music():
    try:
        files = [f for f in os.listdir(MUSIC_DIR) if f.endswith(".mp3")]
        if files:
            return os.path.join(MUSIC_DIR, random.choice(files))
    except Exception as e:
        print(f"⚠️ Music selection failed: {e}")
    return None


# 🎬 Video creation with safe checks
def create_video(i, img, audio):
    try:
        path = os.path.join(VIDEOS_DIR, f"video_{i}.mp4")
        clip = ImageClip(img, duration=video_duration)

        if audio and os.path.exists(audio):
            audio_clip = AudioFileClip(audio)
            clip = clip.set_audio(audio_clip)
        else:
            print(f"⚠️ No audio for video {i}, video will be silent.")

        clip.write_videofile(path, fps=24, codec="libx264", audio_codec="aac")
        return path

    except Exception as e:
        print(f"❌ Video creation failed for video {i}: {e}")
        return None


# 🚀 Main automation
def run_automation(total_videos=1):
    for i in range(total_videos):
        print(f"\n🎬 Starting video {i}")
        img = generate_image(i)
        audio = get_music()
        video = create_video(i, img, audio)

        if video:
            print(f"✅ Video {i} created at {video}")
        else:
            print(f"❌ Video {i} failed")


if __name__ == "__main__":
    run_automation(total_videos=2)
    print("\n🎉 Automation completed!")
        

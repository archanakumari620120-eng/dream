import os, json, time
from moviepy.editor import ImageClip, AudioFileClip
from gtts import gTTS
from PIL import Image, ImageDraw, ImageFont
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from concurrent.futures import ThreadPoolExecutor
from diffusers import StableDiffusionPipeline
import torch

BASE_DIR = os.getcwd()
IMAGES_DIR = os.path.join(BASE_DIR, "assets/images")
VOICES_DIR = os.path.join(BASE_DIR, "assets/voices")
VIDEOS_DIR = os.path.join(BASE_DIR, "assets/videos")
TOKEN_FILE = os.path.join(BASE_DIR, "token.json")

os.makedirs(IMAGES_DIR, exist_ok=True)
os.makedirs(VOICES_DIR, exist_ok=True)
os.makedirs(VIDEOS_DIR, exist_ok=True)

config = json.load(open(os.path.join(BASE_DIR,"config.json")))
topic = config["topic"]
video_count = config["video_count"]
video_duration = config["video_duration"]
auto_upload = config.get("auto_upload", True)

# VRAM-safe Stable Diffusion
pipe = StableDiffusionPipeline.from_pretrained("runwayml/stable-diffusion-v1-5", torch_dtype=torch.float16)
pipe.to("cuda" if torch.cuda.is_available() else "cpu")
pipe.enable_attention_slicing()  # reduces VRAM usage

def generate_script(i): return f"Hello viewers! This is YouTube Short #{i} about {topic}."

def generate_image(i):
    prompt = f"Viral YouTube Short image about {topic}"
    image = pipe(prompt, height=512, width=512).images[0]
    if image is None:
        raise ValueError("Image generation failed")
    path = os.path.join(IMAGES_DIR, f"image_{i}.png")
    image.save(path)
    return path

def generate_voice(i, script):
    path = os.path.join(VOICES_DIR, f"voice_{i}.mp3")
    gTTS(script).save(path)
    return path

def create_video(i, img, audio):
    path = os.path.join(VIDEOS_DIR, f"video_{i}.mp4")
    clip = ImageClip(img, duration=video_duration).set_audio(AudioFileClip(audio))
    clip.write_videofile(path, fps=24, codec='libx264', audio_codec='aac')
    return path

def generate_single_video(i):
    try:
        script = generate_script(i)
        img = generate_image(i)
        audio = generate_voice(i, script)
        create_video(i, img, audio)
        print(f"✅ Video #{i} created")
    except Exception as e:
        print(f"❌ Video generation failed #{i}: {e}")

def run_automation():
    start = time.time()
    with ThreadPoolExecutor(max_workers=video_count) as ex:
        for i in range(video_count):
            ex.submit(generate_single_video, i)

    if auto_upload:
        try:
            creds = Credentials.from_authorized_user_file(TOKEN_FILE, ["https://www.googleapis.com/auth/youtube.upload"])
            yt = build("youtube", "v3", credentials=creds)
            for i, vf in enumerate(sorted(os.listdir(VIDEOS_DIR))):
                try:
                    yt.videos().insert(
                        part="snippet,status",
                        body={
                            "snippet": {"title": f"{topic} Short {i}", "description": f"Check out {topic}!", "tags": ["AI","Tech","Shorts"]},
                            "status": {"privacyStatus": "public"}
                        },
                        media_body=os.path.join(VIDEOS_DIR,vf)
                    ).execute()
                    print(f"✅ Uploaded {vf}")
                except Exception as e:
                    print(f"❌ Upload failed {vf}: {e}")
        except Exception as e:
            print(f"❌ YouTube upload setup failed: {e}")

    print(f"🎉 Automation completed in {time.time()-start:.2f}s")

if __name__ == "__main__":
    run_automation()

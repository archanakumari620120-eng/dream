import os, json, time
from moviepy.editor import ImageClip, AudioFileClip
import pyttsx3
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from concurrent.futures import ThreadPoolExecutor
from PIL import Image, ImageDraw, ImageFont

config = json.load(open("config.json"))
topic = config["topic"]
video_count = config["video_count"]
video_duration = config["video_duration"]
auto_upload = config.get("auto_upload", True)

os.makedirs("assets/images", exist_ok=True)
os.makedirs("assets/voices", exist_ok=True)
os.makedirs("assets/videos", exist_ok=True)

def generate_script(index):
    return f"Hello viewers! This is YouTube Short #{index} about {topic}. Enjoy and subscribe!"

def generate_image(index):
    file_path = f"assets/images/image_{index}.png"
    img = Image.new("RGB", (720,1280), color=(73,109,137))
    d = ImageDraw.Draw(img)
    font = ImageFont.load_default()
    d.text((50,600), f"{topic} #{index}", fill=(255,255,0), font=font)
    img.save(file_path)
    return file_path

def generate_voice(index, script):
    file_path = f"assets/voices/voice_{index}.mp3"
    engine = pyttsx3.init()
    engine.save_to_file(script, file_path)
    engine.runAndWait()
    return file_path

def create_video(index, image_file, audio_file):
    video_file = f"assets/videos/video_{index}.mp4"
    clip = ImageClip(image_file, duration=video_duration)
    audio = AudioFileClip(audio_file)
    final = clip.set_audio(audio)
    final.write_videofile(video_file, fps=24)
    return video_file

def generate_single_video(index):
    script = generate_script(index)
    img_file = generate_image(index)
    voice_file = generate_voice(index, script)
    video_file = create_video(index, img_file, voice_file)
    print(f"✅ Video #{index} created: {video_file}")

def run_automation():
    start = time.time()
    from concurrent.futures import ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=video_count) as executor:
        for i in range(video_count):
            executor.submit(generate_single_video, i)

    if auto_upload:
        creds = Credentials.from_authorized_user_file("token.json", ["https://www.googleapis.com/auth/youtube.upload"])
        youtube = build("youtube", "v3", credentials=creds)

        for i, vf in enumerate(sorted(os.listdir("assets/videos"))):
            request = youtube.videos().insert(
                part="snippet,status",
                body={
                    "snippet": {"title": f"{topic} Short {i}", "description": f"Check out {topic}!", "tags": ["AI","Tech","Shorts"]},
                    "status": {"privacyStatus": "public"}
                },
                media_body=f"assets/videos/{vf}"
            )
            response = request.execute()
            print(f"Uploaded video: {vf}")

    end = time.time()
    print(f"🎉 Automation completed in {end-start:.2f} seconds")

if __name__ == "__main__":
    run_automation()

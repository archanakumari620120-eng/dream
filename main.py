import os
import random
import traceback
import requests
from time import sleep
from moviepy.editor import VideoFileClip, AudioFileClip, vfx

# YouTube API
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials

# ---------------- DIRECTORIES ----------------
VIDEOS_DIR = "videos"
MUSIC_DIR = "music"
os.makedirs(VIDEOS_DIR, exist_ok=True)
os.makedirs(MUSIC_DIR, exist_ok=True)

# ---------------- SECRETS ----------------
hf_token = os.getenv("HF_API_TOKEN")
if not hf_token:
    raise ValueError("❌ HF_API_TOKEN missing! Check GitHub Secrets.")
else:
    print(f"✅ HF_API_TOKEN loaded (length: {len(hf_token)})")

# ---------------- VIDEO GENERATION (NEW) ----------------
def generate_video_huggingface(prompt, model_id="cerspense/zeroscope_v2_576w"):
    """Generates a video from a prompt using a Hugging Face model."""
    api_url = f"https://api-inference.huggingface.co/models/{model_id}"
    headers = {"Authorization": f"Bearer {hf_token}"}
    payload = {"inputs": prompt}

    print(f"🔹 Requesting video from Hugging Face API...")
    response = requests.post(api_url, headers=headers, json=payload)

    if response.status_code == 503:
        print("⏳ Model is loading, please wait 60 seconds...")
        sleep(60) # Video models can take longer to load
        response = requests.post(api_url, headers=headers, json=payload)

    if response.status_code != 200:
        raise Exception(f"❌ Hugging Face API Error {response.status_code}: {response.text}")

    video_path = os.path.join(VIDEOS_DIR, "generated_video.mp4")
    with open(video_path, "wb") as f:
        f.write(response.content)
    print(f"✅ Video generated and saved: {video_path}")
    return video_path

# ---------------- MUSIC SELECTION ----------------
def get_random_music():
    """Selects a random music file from the music directory."""
    files = [f for f in os.listdir(MUSIC_DIR) if f.endswith((".mp3", ".wav"))]
    if not files:
        print("⚠️ No music found, video will have no audio.")
        return None
    chosen = os.path.join(MUSIC_DIR, random.choice(files))
    print(f"🎵 Selected music: {chosen}")
    return chosen

# ---------------- COMBINE VIDEO & AUDIO (NEW) ----------------
def combine_video_and_audio(video_path, audio_path, output_path="final_video.mp4"):
    """Adds an audio track to an existing video file."""
    try:
        print("🔹 Combining video and audio...")
        video_clip = VideoFileClip(video_path)
        
        if not audio_path or not os.path.exists(audio_path):
            print("⚠️ Audio file not found. Skipping audio combination.")
            video_clip.write_videofile(output_path, codec="libx264", audio_codec="aac")
            return output_path

        audio_clip = AudioFileClip(audio_path)
        
        # If audio is shorter than video, loop it
        if audio_clip.duration < video_clip.duration:
            audio_clip = audio_clip.fx(vfx.loop, duration=video_clip.duration)
        
        # Set the audio of the video clip
        final_clip = video_clip.set_audio(audio_clip.subclip(0, video_clip.duration))
        
        final_clip.write_videofile(output_path, codec="libx264", audio_codec="aac")
        print(f"✅ Final video with audio is ready: {output_path}")
        return output_path
        
    except Exception as e:
        print(f"❌ VIDEO-AUDIO COMBINATION ERROR: {e}")
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
                    "tags": ["AI", "Shorts", "Viral", "Trending", "TextToVideo"],
                    "categoryId": "28" # Science & Technology
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
        concepts = ["a dog riding a skateboard", "a cat DJing at a party", "an astronaut walking on Mars", "a futuristic city with flying cars", "a dragon flying over a castle"]
        concept = random.choice(concepts)
        prompt = f"A cinematic, ultra-realistic video of {concept}, vertical 9:16 aspect ratio, trending on YouTube Shorts"
        print(f"📝 Prompt: {prompt}")

        # 1. Generate the base video from text
        generated_video_path = generate_video_huggingface(prompt)
        
        # 2. Get random music
        music_path = get_random_music()
        
        # 3. Combine the generated video with music
        final_video_path = combine_video_and_audio(generated_video_path, music_path)
        
        # 4. Upload the final video to YouTube
        upload_to_youtube(final_video_path, title=f"{concept.capitalize()} #Shorts", description=f"AI Generated Viral Short: {concept.capitalize()}")
        
        print("🎉 Pipeline complete!")

    except Exception as e:
        print(f"❌ Pipeline failed: {e}")
        traceback.print_exc()
            

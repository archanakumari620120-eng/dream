import os
import random
import traceback
import requests
import json
import re
from time import sleep

# Video processing
from moviepy.editor import ImageClip, AudioFileClip, vfx

# YouTube API
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials

# Gemini API
import google.generativeai as genai

# ---------------- CONFIG & DIRECTORIES ----------------
VIDEOS_DIR = "videos"
MUSIC_DIR = "music"
os.makedirs(VIDEOS_DIR, exist_ok=True)
os.makedirs(MUSIC_DIR, exist_ok=True)

# ---------------- SECRETS ----------------
# Make sure to set these in your GitHub repository's Secrets
HF_API_TOKEN = os.getenv("HF_API_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
TOKEN_JSON = os.getenv("TOKEN_JSON")

if not all([HF_API_TOKEN, GEMINI_API_KEY, TOKEN_JSON]):
    raise ValueError("❌ Missing one or more secrets! Check HF_API_TOKEN, GEMINI_API_KEY, TOKEN_JSON")
print("✅ All secrets loaded successfully.")

# ---------------- GEMINI: Concept, Title, Description, Tags ----------------
def generate_concept_and_metadata():
    """Generates video metadata using the Gemini API."""
    try:
        print("🔹 Generating metadata with Gemini...")
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel('gemini-1.5-flash')

        categories = ["Animal", "Nature", "Space", "Motivation", "Funny", "Abstract Art", "Fantasy", "Sci-Fi"]
        category = random.choice(categories)

        user_prompt = f"""
        You are a YouTube Shorts content expert. Generate a viral content idea.
        Your output MUST be a single, clean JSON object, without any markdown formatting like ```json.
        Category: {category}
        JSON format:
        {{
            "concept": "A very short, creative, and visually compelling concept for an AI image. This will be used as a prompt.",
            "title": "A catchy, viral YouTube Shorts title (under 70 characters).",
            "description": "A short description with 3-4 relevant hashtags at the end.",
            "tags": ["tag1", "tag2", "tag3", "tag4", "tag5"]
        }}
        """
        
        response = model.generate_content(user_prompt)
        
        # Clean the response to extract only the JSON part
        cleaned_text = re.search(r'\{.*\}', response.text, re.DOTALL)
        if not cleaned_text:
            raise ValueError("❌ Gemini did not return a valid JSON object.")
            
        metadata = json.loads(cleaned_text.group(0))
        print("✅ Gemini metadata generated successfully.")
        return metadata

    except Exception as e:
        print(f"❌ Gemini metadata error: {e}")
        traceback.print_exc()
        raise

# ---------------- HUGGING FACE IMAGE GENERATION ----------------
def generate_image_huggingface(prompt, model_id="stabilityai/stable-diffusion-xl-base-1.0"):
    """Generates an image using Hugging Face Inference API."""
    api_url = f"[https://api-inference.huggingface.co/models/](https://api-inference.huggingface.co/models/){model_id}"
    headers = {"Authorization": f"Bearer {HF_API_TOKEN}"}
    # Add enhancements to the prompt for better image quality
    payload = {"inputs": f"Vertical (1080x1920), {prompt}, cinematic, high detail, trending on artstation, ultra-realistic"}

    print(f"🖼️ Requesting image from Hugging Face for prompt: '{prompt}'")
    response = requests.post(api_url, headers=headers, json=payload)

    if response.status_code == 503:
        print("⏳ Model is loading, waiting for 30 seconds...")
        sleep(30)
        response = requests.post(api_url, headers=headers, json=payload)

    if response.status_code != 200:
        raise Exception(f"Hugging Face API error {response.status_code}: {response.text}")

    img_path = os.path.join(VIDEOS_DIR, "frame.png")
    with open(img_path, "wb") as f:
        f.write(response.content)
    print(f"✅ Image saved successfully: {img_path}")
    return img_path

# ---------------- MUSIC SELECTION ----------------
def get_random_music():
    """Selects a random music file from the music directory."""
    try:
        files = [f for f in os.listdir(MUSIC_DIR) if f.endswith((".mp3", ".wav"))]
        if not files:
            print("⚠️ No music found in the music folder. The video will be silent.")
            return None
        chosen = os.path.join(MUSIC_DIR, random.choice(files))
        print(f"🎵 Music selected: {chosen}")
        return chosen
    except Exception as e:
        print(f"❌ Error selecting music: {e}")
        raise

# ---------------- VIDEO CREATION ----------------
def create_video(image_path, audio_path, output_path="final_video.mp4"):
    """Creates a video from an image and an audio file."""
    try:
        print("🎬 Creating video...")
        clip_duration = 10
        clip = ImageClip(image_path).set_duration(clip_duration)

        if audio_path and os.path.exists(audio_path):
            audio_clip = AudioFileClip(audio_path)
            if audio_clip.duration < clip_duration:
                audio_clip = audio_clip.fx(vfx.loop, duration=clip_duration)
            clip = clip.set_audio(audio_clip.subclip(0, clip_duration))

        clip.write_videofile(output_path, fps=24, codec="libx264", audio_codec="aac")
        print(f"✅ Video created successfully: {output_path}")
        return output_path
    except Exception as e:
        print(f"❌ Error creating video: {e}")
        traceback.print_exc()
        raise

# ---------------- YOUTUBE UPLOAD ----------------
def upload_to_youtube(video_path, title, description, tags, privacy="public"):
    """Uploads the video to YouTube."""
    try:
        print("📤 Uploading to YouTube...")
        with open("token.json", "w") as f:
            f.write(TOKEN_JSON)

        creds = Credentials.from_authorized_user_file("token.json", ["[https://www.googleapis.com/auth/youtube.upload](https://www.googleapis.com/auth/youtube.upload)"])
        youtube = build("youtube", "v3", credentials=creds)

        request_body = {
            "snippet": {
                "title": title,
                "description": description,
                "tags": tags,
                "categoryId": "22" # People & Blogs
            },
            "status": {
                "privacyStatus": privacy,
                "selfDeclaredMadeForKids": False
            }
        }

        request = youtube.videos().insert(
            part="snippet,status",
            body=request_body,
            media_body=video_path
        )

        response = request.execute()
        print(f"✅ Video uploaded successfully! Video ID: {response.get('id')}")
        return response.get("id")
    except Exception as e:
        print(f"❌ Error uploading to YouTube: {e}")
        traceback.print_exc()
        raise

# ---------------- MAIN PIPELINE ----------------
if __name__ == "__main__":
    try:
        # 1. Generate Metadata with Gemini
        metadata = generate_concept_and_metadata()
        
        # 2. Generate Image with Hugging Face using Gemini's concept
        img_path = generate_image_huggingface(metadata["concept"])
        
        # 3. Select Music
        music_path = get_random_music()
        
        # 4. Create Video
        video_path = create_video(img_path, music_path)
        
        # 5. Upload to YouTube using Gemini's metadata
        upload_to_youtube(
            video_path, 
            metadata["title"], 
            metadata["description"], 
            metadata["tags"]
        )
        
        print("\n🎉 Pipeline completed successfully! 🎉")

    except Exception as e:
        print(f"\n❌ Pipeline failed: {e}")
        traceback.print_exc()


import os
import google.generativeai as genai
from moviepy.editor import ImageClip, AudioFileClip, CompositeVideoClip
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
import yt_dlp
import traceback

# 📂 Directories
VIDEOS_DIR = "videos"
MUSIC_DIR = "music"

# ---------------- IMAGE GENERATION ----------------
def generate_image(prompt):
    try:
        print("🔹 Configuring Gemini API...")
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

        print("🔹 Using model gemini-2.0-flash-image")
        model = genai.GenerativeModel("gemini-2.0-flash-image")

        image_prompt = (
            f"Generate a single, high-quality, vertical (1080x1920) image suitable for a YouTube Short background. "
            f"The image should visually represent this quote: '{prompt}'"
        )

        print("🔹 Sending request to generate image...")
        response = model.generate_content(
            [image_prompt],
            request_options={"binary_output": True}
        )

        print("🔹 Response received. Keys:", dir(response))
        print("🔹 Candidates:", response._result.response.candidates)

        img_path = os.path.join(VIDEOS_DIR, "frame.png")
        image_data = response._result.response.candidates[0].content.parts[0].inline_data.data
        with open(img_path, "wb") as f:
            f.write(image_data)

        print(f"✅ Image generated successfully at {img_path}")
        return img_path

    except Exception as e:
        print(f"❌ Error generating image: {e}")
        traceback.print_exc()
        if 'response' in locals():
            try:
                print("Full API Response:", response._result.response)
            except Exception as inner_e:
                print("Could not print full response:", inner_e)
        raise

# ---------------- VIDEO CREATION ----------------
def create_video(image_path, audio_path, output_path="final_video.mp4"):
    try:
        print("🔹 Creating video...")
        clip = ImageClip(image_path).set_duration(10)  # 10 seconds default
        if audio_path and os.path.exists(audio_path):
            audio_clip = AudioFileClip(audio_path)
            clip = clip.set_audio(audio_clip).set_duration(audio_clip.duration)
        clip.write_videofile(output_path, fps=24)
        print(f"✅ Video created successfully at {output_path}")
        return output_path
    except Exception as e:
        print(f"❌ Error creating video: {e}")
        traceback.print_exc()
        raise

# ---------------- MUSIC DOWNLOAD ----------------
def get_random_music():
    try:
        print("🔹 Searching local music folder...")
        files = [f for f in os.listdir(MUSIC_DIR) if f.endswith((".mp3", ".wav"))]
        if not files:
            raise Exception("No music files found in music folder.")
        import random
        chosen = os.path.join(MUSIC_DIR, random.choice(files))
        print(f"🎵 Using music: {chosen}")
        return chosen
    except Exception as e:
        print(f"❌ Error selecting music: {e}")
        raise

# ---------------- YOUTUBE UPLOAD ----------------
def upload_to_youtube(video_path, title="Test Video", description="Uploaded via script"):
    try:
        print("🔹 Preparing YouTube upload...")
        creds = Credentials.from_authorized_user_file("token.json", ["https://www.googleapis.com/auth/youtube.upload"])
        youtube = build("youtube", "v3", credentials=creds)

        request = youtube.videos().insert(
            part="snippet,status",
            body={
                "snippet": {
                    "title": title,
                    "description": description,
                    "tags": ["AI", "Shorts"],
                    "categoryId": "22"
                },
                "status": {
                    "privacyStatus": "private"
                }
            },
            media_body=video_path
        )

        response = request.execute()
        print(f"✅ Video uploaded successfully. Video ID: {response.get('id')}")
        return response.get("id")
    except Exception as e:
        print(f"❌ Error uploading video: {e}")
        traceback.print_exc()
        raise

# ---------------- MAIN PIPELINE ----------------
if __name__ == "__main__":
    try:
        quote = "Life is what happens when you're busy making other plans."
        img_path = generate_image(quote)
        music_path = get_random_music()
        video_path = create_video(img_path, music_path)
        upload_to_youtube(video_path, title=quote, description="Auto-generated Short using AI")
    except Exception as e:
        print("❌ Pipeline failed:", e)
        

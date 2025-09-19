import os
import base64
import traceback
import random
import google.generativeai as genai
from moviepy.editor import ImageClip, AudioFileClip
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials

# ---------------- DIRECTORIES ----------------
VIDEOS_DIR = "videos"
MUSIC_DIR = "music"
os.makedirs(VIDEOS_DIR, exist_ok=True)

# ---------------- IMAGE GENERATION ----------------
def generate_image(prompt):
    try:
        print("🔹 Configuring Gemini API...")
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

        model = genai.GenerativeModel('gemini-1.5-flash-latest')

        image_prompt = (
            f"Generate a single, high-quality, vertical (1080x1920) image suitable for a YouTube Short background. "
            f"The image should visually represent this quote: '{prompt}'"
        )

        print("🔹 Sending request to generate image...")
        response = model.generate_content([image_prompt])

        # ✅ Extract base64 image
        image_b64 = response._result.response.candidates[0].content[0].image.image_base64
        image_data = base64.b64decode(image_b64)

        img_path = os.path.join(VIDEOS_DIR, "frame.png")
        with open(img_path, "wb") as f:
            f.write(image_data)

        print(f"✅ Image generated successfully at {img_path}")
        return img_path

    except Exception as e:
        print(f"❌ Error generating image: {e}")
        traceback.print_exc()
        if 'response' in locals():
            print("Full API Response:", response)
        raise

# ---------------- MUSIC SELECTION ----------------
def get_random_music():
    try:
        files = [f for f in os.listdir(MUSIC_DIR) if f.endswith((".mp3", ".wav"))]
        if not files:
            raise Exception("No music files found in music folder.")
        chosen = os.path.join(MUSIC_DIR, random.choice(files))
        print(f"🎵 Selected music: {chosen}")
        return chosen
    except Exception as e:
        print(f"❌ Error selecting music: {e}")
        raise

# ---------------- VIDEO CREATION ----------------
def create_video(image_path, audio_path, output_path="final_video.mp4"):
    try:
        print("🔹 Creating video...")
        clip = ImageClip(image_path).set_duration(10)  # default 10 sec
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

# ---------------- YOUTUBE UPLOAD ----------------
def upload_to_youtube(video_path, title="AI Short Video", description="Auto-generated Short using AI"):
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
        print(f"📝 Quote: {quote}")

        # 1️⃣ Image generation
        img_path = generate_image(quote)

        # 2️⃣ Music selection
        music_path = get_random_music()

        # 3️⃣ Video creation
        video_path = create_video(img_path, music_path)

        # 4️⃣ YouTube upload
        upload_to_youtube(video_path, title=quote, description="Auto-generated Short using AI")

        print("🎉 Pipeline completed successfully!")

    except Exception as e:
        print("❌ Pipeline failed:", e)
        

import os, json, random, traceback
from moviepy.editor import ImageClip, AudioFileClip, concatenate_videoclips
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials

# ----------------- VIDEO GENERATION -----------------
def safe_index(sequence, idx):
    """Prevent out of range index"""
    if idx < 0: return 0
    if idx >= len(sequence): return len(sequence) - 1
    return idx

def generate_video(images_folder, music_folder, output_file="final.mp4"):
    try:
        images = [os.path.join(images_folder, f) for f in os.listdir(images_folder) if f.lower().endswith((".jpg",".png"))]
        musics = [os.path.join(music_folder, f) for f in os.listdir(music_folder) if f.lower().endswith((".mp3",".wav"))]

        if not images:
            raise Exception("No images found in folder")
        if not musics:
            raise Exception("No music found in folder")

        # Safe random pick with index clipping
        img_idx = safe_index(images, random.randint(0, len(images)))
        image = images[img_idx]

        music_file = random.choice(musics)

        # Create video clip
        img_clip = ImageClip(image).set_duration(15).resize((1080,1920))

        # Avoid NoneType in Audio
        if os.path.exists(music_file):
            audio_clip = AudioFileClip(music_file).volumex(0.8)
            video = img_clip.set_audio(audio_clip)
        else:
            video = img_clip

        video.write_videofile(output_file, fps=30, codec="libx264", audio_codec="aac")
        print("✅ Video generated:", output_file)
        return output_file

    except Exception as e:
        print("❌ Video generation failed:")
        traceback.print_exc()
        return None

# ----------------- YOUTUBE UPLOAD -----------------
def upload_to_youtube(video_file, title, description, tags):
    try:
        token_data = json.loads(os.environ["TOKEN_JSON"])
        creds = Credentials.from_authorized_user_info(token_data)
        youtube = build("youtube", "v3", credentials=creds)

        request = youtube.videos().insert(
            part="snippet,status",
            body={
                "snippet": {
                    "title": title,
                    "description": description,
                    "tags": tags,
                    "categoryId": "22"
                },
                "status": {"privacyStatus": "public"}
            },
            media_body=MediaFileUpload(video_file)
        )
        response = request.execute()
        print(f"✅ Uploaded: https://youtube.com/watch?v={response['id']}")

    except Exception as e:
        print("❌ Upload failed with error:")
        traceback.print_exc()

# ----------------- MAIN -----------------
if __name__ == "__main__":
    video = generate_video("images", "music")
    if video:
        upload_to_youtube(video,
            title="AI Generated Short",
            description="Automated upload test",
            tags=["AI","shorts","automation"]
        )
    print("🎉 Automation completed")
                          

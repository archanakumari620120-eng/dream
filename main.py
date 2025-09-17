import os
import random
import datetime
import glob
import shutil
import requests
from moviepy.editor import TextClip, CompositeVideoClip, AudioFileClip, ColorClip
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials
import json

# ==============================
# Load Config
# ==============================
with open("config.json", "r") as f:
    config = json.load(f)

YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"

# ==============================
# QUOTES LIST (200+ Indian style motivational)
# ==============================
QUOTES = [
    "Sapne wahi sach hote hain jinhe jag kar dekha jata hai.",
    "Mehnat itni khamoshi se karo ki success shor macha de.",
    "Samay se bada koi sikshak nahi.",
    "Jo kismat me nahi, woh mehnat se milega.",
    "Har raat ke baad ek nayi subah zaroor aati hai.",
    "Jo apne maa-baap ko khush karta hai, uska har kaam safal hota hai.",
    "Jitni badi soch, utni badi jeet.",
    "Zindagi ek hi baar milti hai, ise khud ke liye jeeyo.",
    "Aaj ki mehnat kal ki kamyabi hai.",
    "Gir kar uthna hi asli jeet hai.",
    "Jo apne lakshya par dhyan deta hai, wahi vijay paata hai.",
    "Mushkilein insaan ko majboot banati hain.",
    "Aasan raste kahin nahi le jaate.",
    "Kamyabi ka maza tab aata hai jab sab tumhe girta dekhna chahte hain.",
    "Zindagi jeetne ka tareeka hai, kabhi peeche mudh kar na dekhna.",
    "Shikayat se behtar hai shukriya ada karna.",
    "Samay par ki gayi mehnat hamesha rang laati hai.",
    "Jo sapne dekhte hain, wahi unhe sach bhi karte hain.",
    "Duniya unhe yaad karti hai jo kuch alag karte hain.",
    "Mehnat ki roti sabse meethi hoti hai.",
    "Apna time aayega, bas lage raho.",
    "Jitne bade sapne, utni badi mehnat.",
    "Nakaamiyabi ke bina safalta adhuri hai.",
    "Zindagi me haar kar bhi seekhna chahiye.",
    "Jahan soch unchi, wahan manzil aasaan.",
    "Insaan apni soch se bada banta hai.",
    "Kamyabi unhi ko milti hai jo rukte nahi.",
    "Jitni kathinai, utni badi kahani.",
    "Har subah naya moka lekar aati hai.",
    "Khud par bharosa sabse badi taakat hai.",
    "Seekhna band, toh jeevan band.",
    "Jahan mehnat hoti hai, wahan asambhav kuch nahi.",
    "Zindagi ek khel hai, ise dil se khelo.",
    "Jeetne ke liye haarna bhi zaroori hai.",
    "Himmatwala hi asli jeetata hai.",
    "Bade sapne chhoti soch se nahi aate.",
    "Samay ka sahi istemal hi safalta hai.",
    "Jo khud me sudhar lata hai, wahi duniya badalta hai.",
    "Asli khushi mehnat ke pasine me hai.",
    "Har ek din ek naya chance hai.",
    "Mushkil ghadiyan hi insaan ko banati hain.",
    "Asli dost wahi hai jo musibat me kaam aaye.",
    "Apni pehchaan khud banao.",
    "Duniya sirf result dekhti hai, mehnat nahi.",
    "Maa-baap ki duaon se badi koi taakat nahi.",
    "Asli jeet wahi hai jo sabke liye faydemand ho.",
    "Zindagi me kabhi haar mat maano.",
    "Kamyabi ke raste me patience sabse badi cheez hai.",
    "Chhoti soch bade sapne ko daba deti hai.",
    "Gyaan se bada dhan aur koi nahi.",
    "Jo apne lakshya ko paana chahta hai, uske liye ruke bina chalna hi raasta hai.",
    "Zindagi ko aasaan nahi, khud ko majboot banao.",
    "Jo apna waqt barbad karta hai, wahi zindagi barbad karta hai.",
    "Jo log tumhe neecha dikhana chahte hain, unhe apni success se jawab do.",
    "Jeet ki asli khushi tab hai jab sab tumhe haarte dekhna chahte hain.",
    "Jitni mehnat, utna fal.",
    "Zindagi ek kitaab hai, har din ek naya panna.",
    "Insaan apni aadat se pehchana jata hai.",
    "Aasan raste kabhi manzil tak nahi le jaate.",
    "Nakaamiyabi se ghabrane wala kabhi safal nahi hota.",
    "Har safalta ke peeche ek kahani hoti hai.",
    "Jo apne sapno ke liye lada hai, wahi asli vijeta hai.",
    "Har din ek nayi umeed lekar aata hai.",
    "Aaj ka waqt sabse bada dhan hai.",
    "Mehnat se bada koi puja nahi.",
    "Jahan iraade mazboot hote hain, wahan raste khud ban jaate hain.",
    "Jo khud pe bharosa rakhta hai, use koi hara nahi sakta.",
    "Jitni kathinai, utni badi safalta.",
    "Har musibat ek nayi seekh lekar aati hai.",
    "Jahan dum hai, wahan manzil hai.",
    "Jo khud ko sudhar leta hai, wahi asli insaan hai.",
    "Samay ka moolya samajhne wala kabhi haar nahi khata.",
    "Zindagi unhi ki hai jo kabhi rukte nahi.",
    "Har ek nayi soch ek nayi duniya banati hai.",
    "Jeetne ke liye pehle khud se jeetna padta hai.",
    "Jo log apne iraadon pe tikte hain, wahi jeette hain.",
    "Jeevan me hamesha seekhne wala hi jeetata hai.",
    "Zindagi ek safar hai, manzil nahi.",
    "Mehnat aur imaandari hamesha rang laati hai.",
    "Jahan chah, wahan raah.",
    "Asli shakti insaan ke andar hoti hai.",
    "Har ek din apne sapne ke kareeb le jaata hai.",
    "Jo apne iraade ko majboot banata hai, wahi safal hota hai.",
    "Nakaamiyabi sirf ek pause hai, ant nahi.",
    "Insaan apni soch se banta hai.",
    "Samay sabse bada upchar hai.",
    "Jo sapne chhod dete hain, wo kabhi jeet nahi sakte.",
    "Mehnat se banaya hua sapna sabse khoobsurat hota hai.",
    "Zindagi ka asli maza sangharsh me hai.",
    "Har dukh ek nayi seekh de jaata hai.",
    "Jo apna iraada nahi todta, use duniya jhuka leti hai.",
    "Kamyabi ka asli raaz hai patience.",
    "Mushkil raste hi sundar manzil tak le jaate hain.",
    "Jo apni galtiyon se seekhta hai, wahi bada banta hai.",
    "Zindagi ko aasaan mat samajho, ise behtareen banao.",
    "Apni mehnat par garv karo.",
    "Jo kal tha usse seekho, jo aaj hai use jeeyo.",
    "Insaan apni koshish se sab kuch paa sakta hai.",
    "Jahan iraade sahi hote hain, wahan manzil milti hai.",
    "Maa-baap ki izzat sabse badi ibadat hai.",
    "Har ek sapna sacrifice maangta hai.",
    "Asli khushi apno ko khush rakhne me hai.",
    "Zindagi ek safar hai, ise khushi se jeeyo.",
    "Jitna bada sapna, utni badi mehnat.",
    "Mushkilein hamesha seekh deti hain.",
    "Jo apne iraade me mazboot hote hain, wahi vijay paate hain.",
    "Kamyabi ki asli pehchaan haar ke baad hoti hai.",
    "Jo apna kaam imaandari se karta hai, usse koi hara nahi sakta.",
    "Zindagi ka har pal ek nayi seekh hai.",
    "Aasan raaste kabhi bada insaan nahi banate.",
    "Samay aur gyaan sabse bade dhan hain.",
    "Jo apne sapno ke liye ladta hai, wahi asli jeetata hai.",
    "Har ek insaan ke andar ek nayi taakat hoti hai.",
    "Zindagi ko khud apne rang do.",
    "Jo apna iraada majboot banata hai, use koi hara nahi sakta.",
    "Har mushkil ka hal hota hai, bas hausla hona chahiye.",
    "Kamyabi unhi ko milti hai jo kabhi rukte nahi.",
    "Jo khud par vishwas karta hai, use kabhi haar ka dar nahi hota.",
    "Zindagi me kabhi give up mat karo.",
    "Apni galtiyon se seekhna sabse badi taakat hai.",
    "Jahan hausla hoga, wahan raasta hoga.",
    "Jo apne sapno ke liye jagte hain, wahi unhe paate hain.",
    "Har ek din apne iraade ko mazboot karo.",
    "Jo apna samay bekaar karta hai, wahi zindagi haar jaata hai.",
    "Zindagi jeene ka maza tab hai jab tum apne iraade ko sach karo.",
    "Har ek insaan me kuch alag karne ki shamta hoti hai.",
    "Jo apne iraade se nahi hat'ta, wahi vijay paata hai.",
    "Jitni badi kathinai, utni badi jeet.",
    "Zindagi ko aasaan nahi, sundar banao.",
    "Samay ka moolya samajhne wala hamesha aage badhta hai.",
    "Jo apne iraade par tikta hai, wahi safal hota hai.",
    "Mushkil waqt hamesha seekh deta hai.",
    "Jo apne sapno pe vishwas rakhta hai, wahi vijay paata hai.",
    "Har ek din apne sapno ke kareeb hota hai.",
    "Zindagi unhi ki hai jo kabhi rukte nahi.",
    "Samay aur mehnat hamesha rang laate hain.",
    "Jo apne iraade ko majboot banata hai, wahi safal hota hai.",
    "Har ek musibat ek nayi taqat lekar aati hai.",
    "Zindagi me kabhi rukna nahi chahiye.",
    "Mushkilein hi insaan ko mazboot banati hain.",
    "Jo apne iraade me majboot hote hain, wahi vijay paate hain.",
    "Zindagi ko sundar banane ka tareeka hai apni soch ko sundar banana.",
    "Samay ka sahi istemal hi safalta hai.",
    "Har ek din ek nayi umeed lekar aata hai.",
    "Jo apne sapno ke liye mehnat karta hai, wahi safal hota hai.",
    "Zindagi ka asli maza sangharsh me hai.",
    "Jahan iraade mazboot hote hain, wahan manzil aasaan hoti hai.",
    "Har ek musibat ek moka hai.",
    "Jo apna iraada majboot banata hai, wahi vijay paata hai.",
    "Zindagi ko apni soch se sundar banao.",
    "Samay aur gyaan sabse bade dhan hain.",
    "Har ek din ek nayi seekh hoti hai.",
    "Jo apne iraade ko kabhi nahi todta, wahi safal hota hai.",
    "Zindagi me kabhi give up mat karo.",
    "Mushkil waqt hamesha nayi raah dikhata hai.",
    "Jo apne sapno ke liye jagta hai, wahi unhe paata hai.",
    "Zindagi ko khud apne rang do.",
    "Har ek din ek nayi umeed hoti hai.",
    "Jo apne iraade ko mazboot rakhta hai, wahi vijay paata hai.",
    "Samay sabse bada dhan hai.",
    "Har ek musibat ek nayi taqat lekar aati hai.",
    "Jo apne sapno ko sach karna chahta hai, wahi safal hota hai.",
    "Zindagi ko sundar banane ka raaz hai apni soch.",
    "Har ek din apne iraade ko majboot karo.",
    "Jo apne iraade se nahi hat'ta, wahi vijay paata hai.",
    "Zindagi me kabhi rukna nahi chahiye.",
    "Mushkilein hi insaan ko majboot banati hain.",
    "Jo apne iraade ko majboot banata hai, wahi safal hota hai.",
    "Har ek musibat ek moka hai.",
    "Zindagi ko apni soch se sundar banao.",
    "Samay aur gyaan sabse bade dhan hain.",
    "Har ek din ek nayi seekh hoti hai.",
    "Jo apne iraade ko kabhi nahi todta, wahi safal hota hai.",
    "Zindagi me kabhi give up mat karo.",
    "Mushkil waqt hamesha nayi raah dikhata hai.",
    "Jo apne sapno ke liye jagta hai, wahi unhe paata hai.",
    "Zindagi ko khud apne rang do.",
    "Har ek din ek nayi umeed hoti hai.",
    "Jo apne iraade ko mazboot rakhta hai, wahi vijay paata hai."
]

# ==============================
# Get YouTube service
# ==============================
def get_youtube_service():
    creds = Credentials.from_authorized_user_file("token.json", ["https://www.googleapis.com/auth/youtube.upload"])
    return build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION, credentials=creds)

# ==============================
# Download copyright-free music
# ==============================
def get_music():
    music_path = "music/background.mp3"
    if not os.path.exists(music_path):
        url = "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3"  # free no-copyright sample
        r = requests.get(url)
        with open(music_path, "wb") as f:
            f.write(r.content)
    return music_path

# ==============================
# Create Quote Video (black screen + text)
# ==============================
def create_quote_video(quote, output_path):
    duration = 15
    W, H = 1080, 1920

    # Black background
    bg = ColorClip(size=(W, H), color=(0, 0, 0), duration=duration)

    # Text
    txt_clip = TextClip(
        quote,
        fontsize=70,
        color="white",
        size=(W-100, None),
        method="caption",
        align="center",
        font="Arial-Bold"
    ).set_duration(duration).set_position(("center", "center"))

    # Music
    music_path = get_music()
    audio = AudioFileClip(music_path).subclip(0, duration)

    video = CompositeVideoClip([bg, txt_clip])
    video = video.set_audio(audio)
    video.write_videofile(output_path, fps=30, codec="libx264", audio_codec="aac")
    video.close()

# ==============================
# Upload to YouTube
# ==============================
def upload_video(youtube, file_path, title, description, tags):
    request_body = {
        "snippet": {
            "title": title,
            "description": description,
            "tags": tags,
            "categoryId": "22"
        },
        "status": {
            "privacyStatus": "public",
            "selfDeclaredMadeForKids": False
        }
    }

    media = MediaFileUpload(file_path, chunksize=-1, resumable=True)
    request = youtube.videos().insert(
        part="snippet,status",
        body=request_body,
        media_body=media
    )
    response = request.execute()
    print(f"✅ Uploaded: {response['id']}")

# ==============================
# Main Function
# ==============================
def main():
    youtube = get_youtube_service()

    # Step 1: Check if videos/ folder has ready video
    os.makedirs("videos", exist_ok=True)
    existing_videos = glob.glob("videos/*.mp4")

    if existing_videos:
        file_path = existing_videos[0]
        title = f"Motivational Shorts | {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}"
        description = "Fresh motivational shorts video. Stay inspired! 🇮🇳"
        tags = ["motivation", "shorts", "inspiration", "india", "success"]

        upload_video(youtube, file_path, title, description, tags)
        os.remove(file_path)  # cleanup
        return

    # Step 2: If no ready video, create new quote video
    quote = random.choice(QUOTES)
    output_path = "temp_quote.mp4"
    create_quote_video(quote, output_path)

    title = f"{quote[:60]}... | Motivational Shorts"
    description = f"{quote}\n\nDaily inspirational shorts. 🇮🇳"
    tags = ["motivation", "shorts", "inspiration", "india", "success"]

    upload_video(youtube, output_path, title, description, tags)

    os.remove(output_path)

if __name__ == "__main__":
    main()
    

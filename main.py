import google.generativeai as genai
import base64
import os

def generate_image(prompt):
    try:
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        
        # ✅ सही image generation model
        model = genai.GenerativeModel("gemini-2.0-flash-image")  
        
        image_prompt = (
            f"Generate a single, high-quality, vertical (1080x1920) image suitable for a YouTube Short background. "
            f"The image should visually represent this quote: '{prompt}'"
        )

        # ✅ Image generation call
        response = model.generate_content(
            [image_prompt],
            request_options={"binary_output": True}  # Direct image binary मिलेगा
        )

        # ✅ Save image
        img_path = os.path.join(VIDEOS_DIR, "frame.png")
        with open(img_path, "wb") as f:
            f.write(response._result.response.candidates[0].content.parts[0].inline_data.data)

        print("✅ Image generated successfully.")
        return img_path

    except Exception as e:
        print(f"❌ Error generating image: {e}")
        if 'response' in locals():
            print("Full API Response:", response)
        raise
        

from google import genai
from google.genai import types

with open('photo_2026-02-07_20-54-20.jpg', 'rb') as f:
    image_bytes = f.read()

# Pass API key as keyword argument
client = genai.Client(api_key="AIzaSyDXe6k8vnuaP_L10VpXVROh2fyVCPSWMiU")
response = client.models.generate_content(
    model='gemini-3-flash-preview',
    contents=[
        types.Part.from_bytes(
            data=image_bytes,
            mime_type='image/jpeg',
        ),
        'Caption this image.'
    ]
)

print(response.text)
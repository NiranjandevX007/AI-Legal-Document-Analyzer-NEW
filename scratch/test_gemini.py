import os
import google.generativeai as genai

print("GEMINI_API_KEY in env:", os.environ.get("GEMINI_API_KEY"))

genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-2.5-flash")

try:
    print("Testing generate_content...")
    response = model.generate_content("Hello! Say 'Gemini is working' if you can read this.")
    print("Response:", response.text.strip())
except Exception as e:
    print("Failed to run Gemini:", e)

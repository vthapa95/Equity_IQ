import os
from dotenv import load_dotenv
from google import genai

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

with open("model_list.txt", "w") as f:
    f.write(f"API Key: {api_key[:8]}...\n\n")
    
    f.write("=== AVAILABLE MODELS ===\n")
    try:
        for model in client.models.list():
            f.write(f"{model.name}\n")
    except Exception as e:
        f.write(f"Error: {e}\n")
    
    f.write("\n=== TESTING GENERATION ===\n")
    test_models = [
        "gemini-2.0-flash",
        "gemini-2.0-flash-lite",
        "gemini-1.5-flash",
        "gemini-1.5-pro",
        "gemini-pro",
    ]
    for m in test_models:
        try:
            response = client.models.generate_content(model=m, contents="Say hi")
            f.write(f"SUCCESS {m}: {response.text.strip()[:50]}\n")
            break
        except Exception as e:
            f.write(f"FAILED  {m}: {str(e)[:200]}\n")

print("Done! Check model_list.txt")

from getpass import getpass
from google import genai

api_key = getpass("Enter your Gemini API key: ")

client = genai.Client(api_key=api_key)

try:
    response = client.models.generate_content(
    model="gemini-3.7-flash",
    contents="Say hello in one sentence."
)

except Exception as e:
    print("Error:", type(e).__name__, str(e))

finally:
    client.close()
"""Manual Gemini connectivity check; run directly, never during pytest collection."""

from getpass import getpass


def main() -> None:
    from google import genai

    api_key = getpass("Enter your Gemini API key: ")
    client = genai.Client(api_key=api_key)
    try:
        response = client.models.generate_content(
            model="gemini-3.7-flash",
            contents="Say hello in one sentence.",
        )
        print(response.text)
    except Exception as exc:
        print("Error:", type(exc).__name__, str(exc))
    finally:
        client.close()


if __name__ == "__main__":
    main()

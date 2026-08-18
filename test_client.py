"""
Quick manual test - hits your gateway exactly like a normal OpenAI client would.

Usage:
    python test_client.py "openai/gpt-4o-mini"
    python test_client.py "anthropic/claude-sonnet-4-6"
    python test_client.py "groq/llama-3.3-70b-versatile"
"""
import sys
import httpx

GATEWAY_URL = "http://localhost:8000/v1/chat/completions"
GATEWAY_KEY = "test-key-123"


def main():
    model = sys.argv[1] if len(sys.argv) > 1 else "openai/gpt-4o-mini"

    with httpx.Client(timeout=60.0) as client:
        with client.stream(
            "POST",
            GATEWAY_URL,
            headers={"Authorization": f"Bearer {GATEWAY_KEY}"},
            json={
                "model": model,
                "messages": [{"role": "user", "content": "Say hello in 5 words."}],
            },
        ) as resp:
            print(f"Status: {resp.status_code}")
            for line in resp.iter_lines():
                if line:
                    print(line)


if __name__ == "__main__":
    main()

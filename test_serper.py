"""Test Serper.dev API directly."""
import os
import requests
from dotenv import load_dotenv

load_dotenv()

serper_key = os.getenv("SERPER_API_KEY")
print(f"API Key loaded: {'Yes' if serper_key else 'No'}")
print(f"API Key length: {len(serper_key) if serper_key else 0}")

if serper_key:
    # Test simple query
    headers = {
        'X-API-KEY': serper_key,
        'Content-Type': 'application/json'
    }

    payload = {
        "q": "한국 아르바이트 플랫폼",
        "num": 5,
        "hl": "ko",
        "gl": "kr"
    }

    print("\nTesting Serper.dev API...")
    print(f"Query: {payload['q']}")

    try:
        response = requests.post(
            'https://google.serper.dev/search',
            headers=headers,
            json=payload,
            timeout=10
        )

        print(f"\nHTTP Status: {response.status_code}")

        if response.status_code != 200:
            print(f"Error response: {response.text}")
        else:
            results = response.json()
            print(f"Response keys: {list(results.keys())}")

            if 'error' in results:
                print(f"ERROR: {results['error']}")
            elif 'organic' in results:
                print(f"\nFound {len(results['organic'])} results:")
                for i, result in enumerate(results['organic'][:3], 1):
                    print(f"\n{i}. {result.get('title', 'No title')}")
                    print(f"   URL: {result.get('link', 'No URL')}")
                    print(f"   Snippet: {result.get('snippet', 'No snippet')[:100]}...")
            else:
                print(f"\nNo organic results. Full response:")
                print(results)

    except Exception as e:
        print(f"\nException: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
else:
    print("\nNo API key found!")

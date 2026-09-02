import requests

api_key = input("Paste your RapidAPI key: ").strip()

url = "https://exercisedb.p.rapidapi.com/exercises/name/squat"
headers = {
    "X-RapidAPI-Key": api_key,
    "X-RapidAPI-Host": "exercisedb.p.rapidapi.com",
}

print(f"\nKey length: {len(api_key)} characters")
print(f"Key (first 8 chars): {api_key[:8]}...")
print(f"URL: {url}")
print("\nSending request...\n")

response = requests.get(url, headers=headers, params={"limit": 10}, timeout=10)

print(f"Status code: {response.status_code}")
print(f"Response headers: {dict(response.headers)}")
print(f"\nRaw response body (first 500 chars):")
print(response.text[:500])

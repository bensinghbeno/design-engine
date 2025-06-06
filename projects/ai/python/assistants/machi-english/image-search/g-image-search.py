import requests
import sys
import tempfile
from PIL import Image

GOOGLE_API_KEY = "AIzaSyCHkMwQIwPo5ARcwxVl2-8xYPOT5k5rhgM"
GOOGLE_CSE_ID = "f353698d81ef5475f"

def google_image_search(query):
    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "key": GOOGLE_API_KEY,
        "cx": GOOGLE_CSE_ID,
        "q": query,
        "searchType": "image",
        "num": 1,
    }

    try:
        print(f"Searching for: {query}")
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        image_url = data["items"][0]["link"]
        print(f"Found image: {image_url}")
        return image_url
    except Exception as e:
        print(f"Error: {e}")
        return None

def download_and_show_image(image_url):
    try:
        response = requests.get(image_url, stream=True)
        response.raise_for_status()
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as f:
            f.write(response.content)
            img = Image.open(f.name)
            img.show()
    except Exception as e:
        print(f"Image load error: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python google_image_search.py 'search term'")
        sys.exit(1)

    query = " ".join(sys.argv[1:])
    image_url = google_image_search(query)
    if image_url:
        download_and_show_image(image_url)


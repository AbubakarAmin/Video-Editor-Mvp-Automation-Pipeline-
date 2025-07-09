import os
import uuid
import json
import requests
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

from dotenv import load_dotenv, set_key

# Load .env
ENV_PATH = ".env"
load_dotenv(dotenv_path=ENV_PATH)

AUTH_URL = "https://freesound.org/apiv2/oauth2/authorize/"
TOKEN_URL = "https://freesound.org/apiv2/oauth2/access_token/"
API_BASE_URL = "https://freesound.org/apiv2/"
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
REDIRECT_URI = "http://freesound.org/home/app_permissions/permission_granted/"

def launch_oauth_flow():
    auth_link = f"{AUTH_URL}?client_id={CLIENT_ID}&response_type=code"
    print(f"\n🔑 Opening the following URL in your browser:\n{auth_link}\n")
    import webbrowser
    webbrowser.open(auth_link)
    return input("Paste the code shown on the Freesound page here: ").strip()

def exchange_code_for_tokens(code):
    data = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "grant_type": "authorization_code",
        "code": code
    }
    response = requests.post(TOKEN_URL, data=data)
    response.raise_for_status()
    tokens = response.json()
    expires_at = int(time.time()) + tokens["expires_in"]
    set_key(ENV_PATH, "ACCESS_TOKEN", tokens["access_token"])
    set_key(ENV_PATH, "REFRESH_TOKEN", tokens["refresh_token"])
    set_key(ENV_PATH, "EXPIRES_AT", str(expires_at))
    return tokens["access_token"]

def refresh_access_token():
    data = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "grant_type": "refresh_token",
        "refresh_token": os.getenv("REFRESH_TOKEN")
    }
    response = requests.post(TOKEN_URL, data=data)
    response.raise_for_status()
    tokens = response.json()
    expires_at = int(time.time()) + tokens["expires_in"]
    set_key(ENV_PATH, "ACCESS_TOKEN", tokens["access_token"])
    set_key(ENV_PATH, "REFRESH_TOKEN", tokens["refresh_token"])
    set_key(ENV_PATH, "EXPIRES_AT", str(expires_at))
    return tokens["access_token"]

def get_valid_token():
    token = os.getenv("ACCESS_TOKEN")
    refresh_token = os.getenv("REFRESH_TOKEN")
    expires_at_str = os.getenv("EXPIRES_AT", "0")

    try:
        expires_at = int(expires_at_str)
    except ValueError:
        expires_at = 0

    if not token or not refresh_token or not expires_at:
        print("🔁 Access token missing or expired. Authenticating...")
        code = launch_oauth_flow()
        token = exchange_code_for_tokens(code)
    if  time.time() > expires_at:
        token=refresh_access_token()

    return token


# 🔑 Single audio download function (same core logic, made robust)
def download_top_sfx_for_tag(tag, output_dir, token):
    try:
        os.makedirs(output_dir, exist_ok=True)

        search_url = f"{API_BASE_URL}search/text/"
        params = {"query": tag, "sort": "downloads_desc", "fields": "id,name,download"}
        headers = {"Authorization": f"Bearer {token}"}

        # Step 1: Search sound by tag
        response = requests.get(search_url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        results = response.json().get("results")
        if not results:
            print(f"No results found for tag: {tag}")
            return None

        # Step 2: Get download URL of top result
        sound_id = results[0]["id"]
        sound_info_url = f"{API_BASE_URL}sounds/{sound_id}/"
        sound_response = requests.get(sound_info_url, headers=headers, timeout=10)
        sound_response.raise_for_status()
        download_url = sound_response.json()["download"]

        # Step 3: Download audio file
        file_ext = ".mp3"
        file_name = f"{uuid.uuid4()}{file_ext}"
        file_path = os.path.join(output_dir, file_name)

        audio_data = requests.get(download_url, headers=headers, timeout=20)
        audio_data.raise_for_status()
        with open(file_path, "wb") as f:
            f.write(audio_data.content)

        return file_path

    except Exception as e:
        print(f"[ERROR] Failed to download SFX for tag '{tag}': {e}")
        return None


# 🚀 Multithreaded bulk SFX download
def process_sfx_json_and_download(json_video, output_dir="Assets/Downloaded_SF", max_workers=5):
    token = get_valid_token()
    os.makedirs(output_dir, exist_ok=True)

    print("Downloading audio (SFX)...")
    updated = []

    def download_worker(item):
        tag = item.search_tag_for_sfx_from_freesound
        if not tag:
            return None
        audio_path = download_top_sfx_for_tag(tag, output_dir, token)
        if audio_path:
            item.search_tag_for_sfx_from_freesound = audio_path
            return item
        return None

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [
            executor.submit(download_worker, item)
            for item in json_video if item.search_tag_for_sfx_from_freesound
        ]

        for future in as_completed(futures):
            result = future.result()
            if result:
                updated.append(result)

    return updated

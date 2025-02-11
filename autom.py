import os
import json
import random
import requests
import openai
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from moviepy.editor import *
from gtts import gTTS
from bs4 import BeautifulSoup
from elevenlabs import generate, save
import tweepy
import time

# --------------------- USER SETUP MENU ---------------------
def setup_user():
    config_path = "config.json"
    
    if os.path.exists(config_path):
        with open(config_path, "r") as file:
            return json.load(file)
    
    user_data = {
        "openai_api_key": input("Enter OpenAI API Key (or press Enter to skip): ") or None,
        "youtube_api_key": input("Enter YouTube API Key (or press Enter to skip): ") or None,
        "channel_id": input("Enter YouTube Channel ID (or press Enter to skip): ") or None,
        "affiliate_keyword": input("Enter Affiliate Product Keyword (or press Enter to skip): ") or "technology",
        "elevenlabs_api_key": input("Enter ElevenLabs API Key (or press Enter to use default AI voice): ") or None,
        "twitter_api_key": input("Enter Twitter API Key (or press Enter to skip): ") or None,
        "twitter_api_secret": input("Enter Twitter API Secret (or press Enter to skip): ") or None,
        "twitter_access_token": input("Enter Twitter Access Token (or press Enter to skip): ") or None,
        "twitter_access_secret": input("Enter Twitter Access Secret (or press Enter to skip): ") or None,
        "tiktok_username": input("Enter TikTok Username (or press Enter to skip): ") or None,
        "tiktok_password": input("Enter TikTok Password (or press Enter to skip): ") or None
    }
    
    with open(config_path, "w") as file:
        json.dump(user_data, file)
    
    return user_data

# --------------------- STEP 1: FIND TRENDING TOPICS ---------------------
def get_trending_topics():
    print("Finding trending topics...")
    headers = {"User-Agent": "Mozilla/5.0"}
    url = "https://trends.google.com/trends/trendingsearches/daily/rss"
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, "xml")
        trends = [item.title.text for item in soup.find_all("item")]
        return random.choice(trends)
    else:
        return "Latest AI Technology Trends"

# --------------------- STEP 2: GENERATE VIDEO SCRIPT ---------------------
def generate_script(trend, openai_api_key):
    if not openai_api_key:
        print("Skipping script generation (OpenAI API Key missing).")
        return f"An overview of {trend}. Stay updated!"
    
    print(f"Generating video script for: {trend}...")
    openai.api_key = openai_api_key
    
    prompt = f"Write an engaging YouTube video script about {trend}." \
             "Make it informative, engaging, and encourage viewer interaction. Include a call to action for comments and subscriptions."
    
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}]
    )
    
    return response["choices"][0]["message"]["content"]

# --------------------- STEP 3: GENERATE AI VOICEOVER ---------------------
def generate_voiceover(script, api_key, output_audio="voice.mp3"):
    print("Generating AI voiceover...")
    if api_key:
        audio = generate(text=script, voice="Rachel", api_key=api_key)
        save(audio, output_audio)
    else:
        tts = gTTS(text=script, lang="en")
        tts.save(output_audio)

# --------------------- STEP 4: FIND RELEVANT IMAGES ---------------------
def get_stock_images(keyword, save_folder="images"):
    print(f"Downloading stock images for: {keyword}...")
    os.makedirs(save_folder, exist_ok=True)
    
    image_urls = [
        f"https://source.unsplash.com/1280x720/?{keyword}",
        f"https://source.unsplash.com/1280x720/?technology",
        f"https://source.unsplash.com/1280x720/?news"
    ]
    
    for i, url in enumerate(image_urls):
        img_data = requests.get(url).content
        with open(f"{save_folder}/image_{i}.jpg", "wb") as img_file:
            img_file.write(img_data)

# --------------------- STEP 5: CREATE VIDEO ---------------------
def create_video(image_folder="images", audio_file="voice.mp3", output_video="video.mp4"):
    print("Creating video...")
    images = [os.path.join(image_folder, img) for img in os.listdir(image_folder)]
    clips = [ImageClip(img, duration=5) for img in images]
    
    audio = AudioFileClip(audio_file)
    video = concatenate_videoclips(clips, method="compose").set_audio(audio)
    
    video.write_videofile(output_video, fps=24)

# --------------------- STEP 6: UPLOAD VIDEO TO YOUTUBE ---------------------
def upload_to_youtube(video_file, title, description, tags, youtube_api_key, channel_id):
    if not youtube_api_key or not channel_id:
        print("Skipping YouTube upload (API Key or Channel ID missing).")
        return
    
    print("Uploading video to YouTube...")
    youtube = build("youtube", "v3", developerKey=youtube_api_key)
    
    request = youtube.videos().insert(
        part="snippet,status",
        body={
            "snippet": {
                "title": title,
                "description": description,
                "tags": tags,
                "channelId": channel_id
            },
            "status": {"privacyStatus": "public"}
        },
        media_body=MediaFileUpload(video_file, chunksize=-1, resumable=True)
    )
    response = request.execute()
    print("Upload Complete: ", response)

# --------------------- STEP 7: AUTO-SHARE ON SOCIAL MEDIA ---------------------
def share_on_twitter(message, config):
    if not config.get("twitter_api_key"):
        print("Skipping Twitter post (API Key missing).")
        return
    
    print("Sharing video on Twitter...")
    auth = tweepy.OAuth1UserHandler(config["twitter_api_key"], config["twitter_api_secret"], config["twitter_access_token"], config["twitter_access_secret"])
    api = tweepy.API(auth)
    api.update_status(message)

def share_on_tiktok(video_file, config):
    if not config.get("tiktok_username"):
        print("Skipping TikTok upload (credentials missing).")
        return
    print("Uploading video to TikTok...")
    # Implement TikTok API integration here

# --------------------- RUN THE AUTOMATION ---------------------
if __name__ == "__main__":
    user_config = setup_user()
    trending_topic = get_trending_topics()
    video_script = generate_script(trending_topic, user_config.get("openai_api_key"))
    generate_voiceover(video_script, user_config.get("elevenlabs_api_key"))
    get_stock_images(trending_topic)
    create_video()
    upload_to_youtube("video.mp4", f"{trending_topic} Explained!", f"Latest news about {trending_topic}.", [trending_topic, "news", "trending"], user_config.get("youtube_api_key"), user_config.get("channel_id"))
    share_on_twitter(f"New video: {trending_topic}! Watch here: [YouTube Link]", user_config)
    share_on_tiktok("video.mp4", user_config)

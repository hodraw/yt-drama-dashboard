import os
import json
import datetime
from googleapiclient.discovery import build

API_KEY = os.environ.get("YOUTUBE_API_KEY")

if not API_KEY:
    raise ValueError("找不到 YOUTUBE_API_KEY，請確認 GitHub Secrets 設定。")

# 頻道清單配置 (名稱與 Channel ID)
CHANNELS = [
    {"name": "劇翻天 Drama Go", "id": "UCIXjvnAhFma9fn8dJk6dMKg"},
    {"name": "盛世短剧", "id": "UC_GcrznCXn6b-i1Y7DOn54A"},
    {"name": "六翼至尊剧场", "id": "UCEoo7fRPdKccY7mgBK8E90Q"},
    {"name": "九菇凉", "id": "UCP9N46LjGL-_UkhiEMxfMug"}
]

def get_channel_uploads_playlist_id(youtube, channel_id):
    try:
        res = youtube.channels().list(id=channel_id, part="contentDetails").execute()
        items = res.get("items", [])
        if items:
            return items[0]["contentDetails"]["relatedPlaylists"]["uploads"]
    except Exception as e:
        print(f"Error fetching playlist id for {channel_id}: {e}")
    return None

def fetch_recent_videos(youtube, playlist_id, channel_name, max_results=50):
    if not playlist_id:
        return []
        
    playlist_res = youtube.playlistItems().list(
        playlistId=playlist_id,
        part="snippet",
        maxResults=max_results
    ).execute()

    video_ids = [item["snippet"]["resourceId"]["videoId"] for item in playlist_res.get("items", [])]
    if not video_ids:
        return []

    video_res = youtube.videos().list(
        id=",".join(video_ids),
        part="snippet,statistics"
    ).execute()

    now = datetime.datetime.now(datetime.timezone.utc)
    videos = []

    for item in video_res.get("items", []):
        published_at_str = item["snippet"]["publishedAt"]
        published_at = datetime.datetime.fromisoformat(published_at_str.replace("Z", "+00:00"))
        hours_diff = (now - published_at).total_seconds() / 3600.0

        videos.append({
            "channel_name": channel_name,
            "title": item["snippet"]["title"],
            "url": f"https://www.youtube.com/watch?v={item['id']}",
            "published_at": published_at.strftime("%Y-%m-%d %H:%M:%S UTC"),
            "views": int(item["statistics"].get("viewCount", 0)),
            "hours_ago": hours_diff
        })
    return videos

def main():
    youtube = build("youtube", "v3", developerKey=API_KEY)
    all_videos = []

    for channel in CHANNELS:
        print(f"正在抓取：{channel['name']}...")
        playlist_id = get_channel_uploads_playlist_id(youtube, channel["id"])
        videos = fetch_recent_videos(youtube, playlist_id, channel["name"], max_results=50)
        all_videos.extend(videos)

    output_data = {
        "updated_at": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
        "channels": [c["name"] for c in CHANNELS],
        "videos": all_videos
    }

    # 輸出為 JSON 資料檔供前端調用
    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)

    print("資料更新成功，已寫入 data.json！")

if __name__ == "__main__":
    main()

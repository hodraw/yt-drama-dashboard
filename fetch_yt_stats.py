import os
import json
import datetime
from googleapiclient.discovery import build

API_KEY = os.environ.get("YOUTUBE_API_KEY")

if not API_KEY:
    raise ValueError("找不到 YOUTUBE_API_KEY，請確認 GitHub Secrets 設定。")

CHANNELS = [
    {"name": "劇翻天 Drama Go", "id": "UCIXjvnAhFma9fn8dJk6dMKg"},
    {"name": "盛世短剧", "id": "UC_GcrznCXn6b-i1Y7DOn54A"},
    {"name": "六翼至尊剧场", "id": "UCEoo7fRPdKccY7mgBK8E90Q"},
    {"name": "九菇凉", "id": "UCP9N46LjGL-_UkhiEMxfMug"}
]

# 最大抓取天數 (168 小時 = 7 天)，超過此時間的影片就停止繼續往前抓
MAX_FETCH_HOURS = 168 

def get_channel_uploads_playlist_id(youtube, channel_id):
    try:
        res = youtube.channels().list(id=channel_id, part="contentDetails").execute()
        items = res.get("items", [])
        if items:
            return items[0]["contentDetails"]["relatedPlaylists"]["uploads"]
    except Exception as e:
        print(f"Error fetching playlist id for {channel_id}: {e}")
    return None

def fetch_recent_videos_with_pagination(youtube, playlist_id, channel_name):
    if not playlist_id:
        return []
        
    now = datetime.datetime.now(datetime.timezone.utc)
    all_raw_items = []
    next_page_token = None
    
    # 步驟 1：利用分頁向下抓取，直到遇到超過 168 小時的影片為止
    while True:
        playlist_res = youtube.playlistItems().list(
            playlistId=playlist_id,
            part="snippet",
            maxResults=50,
            pageToken=next_page_token
        ).execute()

        items = playlist_res.get("items", [])
        if not items:
            break

        stop_fetching = False
        for item in items:
            published_at_str = item["snippet"]["publishedAt"]
            published_at = datetime.datetime.fromisoformat(published_at_str.replace("Z", "+00:00"))
            hours_diff = (now - published_at).total_seconds() / 3600.0

            if hours_diff > MAX_FETCH_HOURS:
                stop_fetching = True
                break
            
            all_raw_items.append(item)

        next_page_token = playlist_res.get("nextPageToken")
        
        # 如果已經遇到超過 7 天的影片，或是沒有下一頁了，就終止迴圈
        if stop_fetching or not next_page_token:
            break

    video_ids = [item["snippet"]["resourceId"]["videoId"] for item in all_raw_items]
    if not video_ids:
        return []

    # 步驟 2：分批向 videos API 查詢觀看次數 (API 每次最多查詢 50 個 ID)
    videos = []
    chunk_size = 50
    for i in range(0, len(video_ids), chunk_size):
        chunk_ids = video_ids[i:i + chunk_size]
        video_res = youtube.videos().list(
            id=",".join(chunk_ids),
            part="snippet,statistics"
        ).execute()

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
        print(f"正在完整抓取近 7 天影片：{channel['name']}...")
        playlist_id = get_channel_uploads_playlist_id(youtube, channel["id"])
        videos = fetch_recent_videos_with_pagination(youtube, playlist_id, channel["name"])
        all_videos.extend(videos)
        print(f"-> {channel['name']} 共抓取到 {len(videos)} 筆符合時間內的影片。")

    output_data = {
        "updated_at": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
        "channels": [c["name"] for c in CHANNELS],
        "videos": all_videos
    }

    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)

    print("資料更新成功，已寫入 data.json！")

if __name__ == "__main__":
    main()

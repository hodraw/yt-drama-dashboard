import os
import json
import datetime
from zoneinfo import ZoneInfo
from googleapiclient.discovery import build
from opencc import OpenCC

API_KEY = os.environ.get("YOUTUBE_API_KEY")

if not API_KEY:
    raise ValueError("找不到 YOUTUBE_API_KEY，請確認 GitHub Secrets 設定。")

CHANNELS = [
    {"name": "爱看动漫Animation", "id": "UC5FQ3sxZsjxD9Bej9PsPt9Q"},
    {"name": "盛世短剧", "id": "UC_GcrznCXn6b-i1Y7DOn54A"},
    {"name": "九菇凉", "id": "UCP9N46LjGL-_UkhiEMxfMug"},
    {"name": "劇翻天 Drama Go", "id": "UCIXjvnAhFma9fn8dJk6dMKg"},
    {"name": "浅浅说漫", "id": "UCdeW-4k31PuecTuMQ4Az3xg"},
    {"name": "火龍劇場", "id": "UCThqrNqzKngrnnfJaqhHGnQ"},
    {"name": "甜梦剧场", "id": "UCYANeI_-jbGRXoZQrFBVY9w"},
    {"name": "Mini Drama777", "id": "UCR8kbE4RT723quTog78jRbg"},
    {"name": "天馬短劇", "id": "UC5f6yhQbJ7ZDHH0B6Am8VNw"},
    {"name": "世界短劇", "id": "UCUpppsP5x1KHIAwfIujFMIg"},
    {"name": "燚棠短剧NO1SHORTFILM", "id": "UCI-N31kUSHbtyj5Lkn8VBhQ"},
    {"name": "苍龙剧场", "id": "UCcMyhLA_16r7B6Ud9GFGDKg"},
    {"name": "日笙短劇社", "id": "UCPk97AuvU6eORLrNIB07C8g"},
    {"name": "頂好劇場ShortDrama", "id": "UCPCNrZCIV7LkrmR86cgNP9g"},
    {"name": "王者热血剧场", "id": "UC_aakc4eZBWKOt3l_ENCgng"},
    {"name": "风云剧场", "id": "UCKtxY6fus0ZSPitIwdLy29Q"},
    {"name": "神漫剧场・真人版", "id": "UC8drAG0BV-uai3b2rplzmlw"},
    {"name": "星梦AI社", "id": "UCUDZ-mp8iNVypuhFe9-CS5Q"}
]

MAX_FETCH_HOURS = 168 
TAIPEI_TZ = ZoneInfo("Asia/Taipei")
cc = OpenCC('s2twp')

def get_channel_uploads_playlist_id(youtube, channel_id):
    """透過 API 正確獲取頻道的上傳播放清單 ID"""
    try:
        res = youtube.channels().list(id=channel_id, part="contentDetails").execute()
        items = res.get("items", [])
        if items:
            return items[0]["contentDetails"]["relatedPlaylists"]["uploads"]
    except Exception as e:
        print(f"⚠️ 無法取得頻道 {channel_id} 的播放清單 ID: {e}")
    return None

def fetch_recent_videos_with_pagination(youtube, playlist_id, channel_name):
    if not playlist_id:
        print(f"⚠️ 頻道【{channel_name}】無有效的播放清單，已跳過。")
        return []
        
    now = datetime.datetime.now(datetime.timezone.utc)
    all_raw_items = []
    next_page_token = None
    
    try:
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
            if stop_fetching or not next_page_token:
                break

    except Exception as e:
        print(f"⚠️ 抓取【{channel_name}】影片列表時發生錯誤 (已跳過): {e}")
        return []

    video_ids = [item["snippet"]["resourceId"]["videoId"] for item in all_raw_items]
    if not video_ids:
        return []

    videos = []
    chunk_size = 50
    for i in range(0, len(video_ids), chunk_size):
        chunk_ids = video_ids[i:i + chunk_size]
        try:
            video_res = youtube.videos().list(
                id=",".join(chunk_ids),
                part="snippet,statistics"
            ).execute()

            for item in video_res.get("items", []):
                published_at_str = item["snippet"]["publishedAt"]
                published_at_utc = datetime.datetime.fromisoformat(published_at_str.replace("Z", "+00:00"))
                
                published_at_taipei = published_at_utc.astimezone(TAIPEI_TZ)
                hours_diff = (now - published_at_utc).total_seconds() / 3600.0

                stats = item.get("statistics", {})
                raw_title = item["snippet"]["title"]
                traditional_title = cc.convert(raw_title)

                videos.append({
                    "channel_name": channel_name,
                    "title": traditional_title,
                    "url": f"https://www.youtube.com/watch?v={item['id']}",
                    "published_at": published_at_taipei.strftime("%Y-%m-%d %H:%M:%S"),
                    "views": int(stats.get("viewCount", 0)),
                    "likes": int(stats.get("likeCount", 0)),
                    "hours_ago": hours_diff
                })
        except Exception as e:
            print(f"⚠️ 抓取【{channel_name}】影片詳細數據時發生錯誤: {e}")

    return videos

def main():
    youtube = build("youtube", "v3", developerKey=API_KEY)
    all_videos = []

    for channel in CHANNELS:
        print(f"正在完整抓取近 7 天影片：{channel['name']}...")
        playlist_id = get_channel_uploads_playlist_id(youtube, channel["id"])
        videos = fetch_recent_videos_with_pagination(youtube, playlist_id, channel["name"])
        all_videos.extend(videos)

    now_taipei = datetime.datetime.now(TAIPEI_TZ)

    output_data = {
        "updated_at": now_taipei.strftime("%Y-%m-%d %H:%M:%S"),
        "channels": [c["name"] for c in CHANNELS],
        "videos": all_videos
    }

    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)

    print("資料更新成功！")

if __name__ == "__main__":
    main()

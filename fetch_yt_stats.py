import os
import json
import datetime
from zoneinfo import ZoneInfo
from googleapiclient.discovery import build

API_KEY = os.environ.get("YOUTUBE_API_KEY")

if not API_KEY:
    raise ValueError("找不到 YOUTUBE_API_KEY，請確認 GitHub Secrets 設定。")

CHANNELS = [
    {"name": "劇翻天 Drama Go", "id": "UCIXjvnAhFma9fn8dJk6dMKg"},
    {"name": "盛世短剧", "id": "UC_GcrznCXn6b-i1Y7DOn54A"},
    {"name": "六翼至尊剧场", "id": "UCEoo7fRPdKccY7mgBK8E90Q"},
    {"name": "九菇凉", "id": "UCP9N46LjGL-_UkhiEMxfMug"},
    {"name": "烟雨短剧", "id": "UCO5bVW2lg3ashkw-yFYRMGg"},
    {"name": "風月短劇社", "id": "UCBRC7b_IuXLWGxvYm82tEgA"},
    {"name": "橘子TV剧场 Tangerine TV Drama", "id": "UCLkRCRHQL8kDRbaQav4v8bg"},
    {"name": "星夢短劇ReelShort", "id": "UCw4B_6Ub1KqV-tfh7N8vW2g"},
    {"name": "燚棠短剧NO1SHORTFILM", "id": "UCI-N31kUSHbtyj5Lkn8VBhQ"},
    {"name": "星甜追劇-Drama", "id": "UCz2rdrXuqJP9gdn1Wtqe_fw"},
    {"name": "TL橙光撩劇SHORT", "id": "UCYzEiq8nybQhcjeCuSQr5yA"},
    {"name": "WarmthField-Drama", "id": "UCgYgXtidvtmBxOJhQs_yvAA"},
    {"name": "朝朝短剧", "id": "UCZG2RYht0TeVOpaIrQqC3XQ"},
    {"name": "凌雲爽劇社TopDrama", "id": "UCbLceRJ8dEXObuqPeRDbOSw"},
    {"name": "鴻途劇場dramaclub", "id": "UCfuav-iX0gmHcAWzrtM6vpA"},
    {"name": "繁花剧场ShortTV", "id": "UCEyRpRNpchMK_1aL8iQNRSw"},
    {"name": "深空劇場SkyDrama", "id": "UCj9FuR2C9H6n1s5bHNF6a2A"},
    {"name": "有料短劇NO1Drama", "id": "UCjq-hv609ECQZtbAxOHkxsQ"},
    {"name": "如梦短剧DreamSpace", "id": "UCo9qH7rqeGUMlaQkzMjAvEQ"},
    {"name": "傲心短劇No1Drama", "id": "UC9-ESao-1lM2X1WWlJU24Yw"},
    {"name": "棠糖短剧NO1SWEETFILM", "id": "UCl_CPIOXOJoT1CIG2s2O_EQ"},
    {"name": "森鹿劇場No1Drama", "id": "UC9RuPsIP2qLm1XQr2PUvLJQ"},
    {"name": "清欢剧场ShortTV", "id": "UCQF_OX6ISwaMbxLJEklyk-g"},
    {"name": "木芽劇場DramaBox", "id": "UCT-vFTNCSc5XfSHFRaFpKdg"},
    {"name": "阿姐追剧-DramaSister", "id": "UC5q4F4flH8yOnnO4DvvJ1xA"},
    {"name": "雷凌短劇社No1Drama", "id": "UCWjems-9LdDPKzOANOQ2RQw"},
    {"name": "瑤光劇場Gemlight drama", "id": "UCLwVOYv5gYoeV0TRVm4aZsw"},
    {"name": "銀汐短劇", "id": "UCQo-taFoXd97DdC_RCbqyww"},
    {"name": "星河剧场BurstSweetDrama", "id": "UCiDLFGO02Fe2ycWQuGqNPxw"},
    {"name": "爆款短剧城", "id": "UCnynguz8OC9m0AucHJvDJHw"}
]

MAX_FETCH_HOURS = 168 
TAIPEI_TZ = ZoneInfo("Asia/Taipei")

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

    video_ids = [item["snippet"]["resourceId"]["videoId"] for item in all_raw_items]
    if not video_ids:
        return []

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
            published_at_utc = datetime.datetime.fromisoformat(published_at_str.replace("Z", "+00:00"))
            
            published_at_taipei = published_at_utc.astimezone(TAIPEI_TZ)
            hours_diff = (now - published_at_utc).total_seconds() / 3600.0

            stats = item.get("statistics", {})

            videos.append({
                "channel_name": channel_name,
                "title": item["snippet"]["title"],
                "url": f"https://www.youtube.com/watch?v={item['id']}",
                "published_at": published_at_taipei.strftime("%Y-%m-%d %H:%M:%S"),
                "views": int(stats.get("viewCount", 0)),
                "likes": int(stats.get("likeCount", 0)),  # 擷取喜歡/按讚次數
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

    now_taipei = datetime.datetime.now(TAIPEI_TZ)

    output_data = {
        "updated_at": now_taipei.strftime("%Y-%m-%d %H:%M:%S"),
        "channels": [c["name"] for c in CHANNELS],
        "videos": all_videos
    }

    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)

    print("資料更新成功，已包含喜歡次數（likes）！")

if __name__ == "__main__":
    main()

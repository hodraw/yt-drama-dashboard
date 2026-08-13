import os
import datetime
from googleapiclient.discovery import build

# 從環境變數讀取 API Key (保障安全)
API_KEY = os.environ.get("YOUTUBE_API_KEY")
CHANNEL_ID = "UCIXjvnAhFma9fn8dJk6dMKg"  # 劇翻天 Drama Go

if not API_KEY:
    raise ValueError("找不到 YOUTUBE_API_KEY，請確認 GitHub Secrets 設定。")

def get_channel_uploads_playlist_id(youtube, channel_id):
    res = youtube.channels().list(id=channel_id, part="contentDetails").execute()
    return res["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]

def fetch_recent_videos(youtube, playlist_id, max_results=50):
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
            "title": item["snippet"]["title"],
            "url": f"https://www.youtube.com/watch?v={item['id']}",
            "published_at": published_at.strftime("%Y-%m-%d %H:%M:%S UTC"),
            "views": int(item["statistics"].get("viewCount", 0)),
            "hours_ago": hours_diff
        })
    return videos

def filter_top_videos(videos, max_hours, top_n):
    filtered = [v for v in videos if v["hours_ago"] <= max_hours]
    sorted_videos = sorted(filtered, key=lambda x: x["views"], reverse=True)
    return sorted_videos[:top_n]

def generate_html(data_dict, output_path="index.html"):
    updated_time = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    
    html_content = f"""<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="refresh" content="600"> <!-- 每10分鐘自動重新整理網頁 -->
    <title>劇翻天 Drama Go - 近期熱門影片分析</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #f8f9fa; color: #333; margin: 0; padding: 20px; }}
        .container {{ max-width: 900px; margin: 0 auto; background: #fff; padding: 30px; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.08); }}
        h1 {{ border-bottom: 2px solid #e0e0e0; padding-bottom: 10px; color: #111; margin-top: 0; }}
        .timestamp {{ color: #666; font-size: 0.9em; margin-bottom: 25px; }}
        h2 {{ margin-top: 30px; color: #cc0000; border-left: 4px solid #cc0000; padding-left: 10px; font-size: 1.25em; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 10px; }}
        th, td {{ border: 1px solid #e9ecef; padding: 12px; text-align: left; }}
        th {{ background-color: #f1f3f5; font-weight: bold; color: #495057; }}
        tr:nth-child(even) {{ background-color: #f8f9fa; }}
        a {{ color: #065fd4; text-decoration: none; font-weight: 500; }}
        a:hover {{ text-decoration: underline; }}
        .no-data {{ color: #868e96; font-style: italic; background: #f8f9fa; padding: 12px; border-radius: 4px; border: 1px dashed #dee2e6; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>劇翻天 Drama Go 數據監測 Dashboard</h1>
        <p class="timestamp">最後更新時間：{updated_time}</p>
    """

    sections = [
        ("上架 2 小時內（觀看數前 3 名）", "2h"),
        ("上架 12 小時內（觀看數前 5 名）", "12h"),
        ("上架 48 小時內（觀看數前 5 名）", "48h"),
        ("上架 168 小時 (7天) 內（觀看數前 5 名）", "168h"),
    ]

    for title, key in sections:
        html_content += f"<h2>{title}</h2>"
        items = data_dict[key]
        if not items:
            html_content += "<p class='no-data'>此時間區間內暫無新發布影片。</p>"
        else:
            html_content += """<table>
                <thead>
                    <tr>
                        <th style="width: 50%;">影片名稱</th>
                        <th style="width: 25%;">發布時間 (UTC)</th>
                        <th style="width: 25%;">觀看次數</th>
                    </tr>
                </thead>
                <tbody>"""
            for item in items:
                html_content += f"""
                    <tr>
                        <td><a href="{item['url']}" target="_blank">{item['title']}</a></td>
                        <td>{item['published_at']}</td>
                        <td><strong>{item['views']:,}</strong> 次</td>
                    </tr>"""
            html_content += "</tbody></table>"

    html_content += "</div></body></html>"

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_content)

def main():
    youtube = build("youtube", "v3", developerKey=API_KEY)
    playlist_id = get_channel_uploads_playlist_id(youtube, CHANNEL_ID)
    all_recent_videos = fetch_recent_videos(youtube, playlist_id, max_results=50)

    data = {
        "2h": filter_top_videos(all_recent_videos, max_hours=2, top_n=3),
        "12h": filter_top_videos(all_recent_videos, max_hours=12, top_n=5),
        "48h": filter_top_videos(all_recent_videos, max_hours=48, top_n=5),
        "168h": filter_top_videos(all_recent_videos, max_hours=168, top_n=5),
    }

    generate_html(data)
    print("HTML 報告生成完成！")

if __name__ == "__main__":
    main()

# 🎬 短劇頻道數據即時監測儀表板 (YouTube Short Drama Dashboard)

[![Automated Data Update](https://github.com/hodraw/yt-drama-dashboard/actions/workflows/update_stats.yml/badge.svg)](https://github.com/hodraw/yt-drama-dashboard/actions)
[![Live Demo](https://img.shields.io/badge/Live_Demo-GitHub_Pages-blue?logo=github)](https://hodraw.github.io/yt-drama-dashboard/)

這是一個專為追蹤 YouTube 熱門短劇頻道設計的**自動化數據監測儀表板**。透過 GitHub Actions 與 YouTube Data API v3，定時自動抓取指定短劇頻道的最新影片數據，並提供多維度的動態篩選與熱門排名分析。

🌐 **線上展示頁面**：[https://hodraw.github.io/yt-drama-dashboard/](https://hodraw.github.io/yt-drama-dashboard/)

---

## 🌟 核心功能

* ⏱️ **自動化定時更新**：利用 GitHub Actions 每 4 小時自動執行 Python 腳本，同步最新影片統計數據。
* 🔍 **多時段靈活篩選**：支援篩選 **6 小時內**、**24 小時內**、**72 小時 (3天) 內**及 **240 小時 (10天) 內** 上架的最新影片。
* 📊 **雙重排序維度**：可根據 **觀看次數 (Views)** 或 **喜歡次數 (Likes/按讚數)** 進行動態排名與分析。
* 🏆 **自訂排名數量**：支援顯示前 **5 名**、**10 名**、**20 名** 或 **50 名** 導向檢視。
* 🔤 **自動繁簡轉換**：整合 OpenCC 自動將簡體標題轉為台灣繁體中文，優化閱讀體驗。
* 🌏 **台北時間 (UTC+8) 標準化**：資料更新時間與影片發布時間均已精準轉換為台北時間，方便即時對照。
* 🔄 **分頁深度抓取 (Pagination)**：解決高頻發片頻道在限制筆數下遺漏歷史資料的問題，完整涵蓋近 10 天 (240小時) 的所有影片。

---

## 🛠️ 技術架構

* **Frontend**：HTML5, CSS3, Vanilla JavaScript (無額外框架，載入極速)
* **Backend / Data Pipeline**：Python 3 (`google-api-python-client`, `opencc-python-reimplemented`, `zoneinfo`)
* **Automation / CI-CD**：GitHub Actions
* **Hosting**：GitHub Pages
* **Data Source**：YouTube Data API v3 (`playlistItems`, `videos`)

---

## 📂 專案結構

```text
yt-drama-dashboard/
├── .github/
│   └── workflows/
│       └── update_stats.yml   # GitHub Actions 定時自動化工作流
├── fetch_yt_stats.py          # 呼叫 YouTube API 抓取數據並寫入 JSON 的 Python 腳本
├── index.html                 # 儀表板前端視覺化與篩選邏輯
├── data.json                  # 儲存最新抓取與轉換後的影片數據庫
└── README.md                  # 專案說明文件
```

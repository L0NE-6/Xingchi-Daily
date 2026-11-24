<div align="center">

<sub><strong>L0NE-6 · DAILY SIGNAL</strong></sub>

# 🌟 Xingchi Daily

**星馳 AI 每日簽到 · 多帳號 · GET/POST 狀態回讀 · JSONL**

[简体中文](../README.md) · [English](README.en.md) · **繁體中文** · [日本語](README.ja.md) · [한국어](README.ko.md) · [Português (BR)](README.pt-BR.md)
> 版本：**v1.0.0**（2026-11-24）

</div>

## 功能

使用星馳網頁面板 JWT 讀取今日簽到狀態，在可領取時提交簽到。POST 後會再次讀取狀態，只有 `claimed_today=true` 才回報 `CLAIMED`。

## 設定

使用 `XINGCHI_TOKENS`（多帳號，每行 `備註|JWT`）或 `XINGCHI_TOKEN`（單帳號）。也可使用 `XINGCHI_ACCOUNT_FILE`、`XINGCHI_API_BASE`、`XINGCHI_PROXY`、`XINGCHI_WAIT_SECONDS` 及可選推送變數。

## 協議

```http
GET  /api/v1/user/checkin
POST /api/v1/user/checkin
GET  /api/v1/user/checkin
Authorization: Bearer <JWT>
```

第一次 GET 讀取 `enabled`、`claimed_today`、`amount` 等欄位；POST 無 body；第二次 GET 必須確認 `claimed_today=true`。回讀失敗或仍為 false 時標記 `UNCONFIRMED`。

## 執行

```bash
python -m pip install -r requirements.txt
export XINGCHI_TOKEN='eyJ...'
python xingchi_daily.py
python xingchi_daily.py --query
python xingchi_daily.py --only 1,3-4
```

## 隱私

不要提交 JWT、帳號檔案、報告、日誌或含憑證的截圖。腳本會遮蔽手機號、Token 與推送憑證。

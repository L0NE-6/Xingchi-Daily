<div align="center">

<sub><strong>L0NE-6 · DAILY SIGNAL</strong></sub>

# 🌟 Xingchi Daily

**Xingchi AI 毎日チェックイン · 複数アカウント · GET/POST 状態の再読取 · JSONL**

[简体中文](../README.md) · [English](README.en.md) · [繁體中文](README.zh-Hant.md) · [日本語](README.ja.md) · [한국어](README.ko.md) · [Português (BR)](README.pt-BR.md)

</div>

## 機能

Web パネルの JWT で Xingchi のチェックイン状態を読み取り、受取可能な場合に毎日の報酬を申請します。POST 後に状態を再読取し、`claimed_today=true` の場合だけ `CLAIMED` と報告します。

## 設定

`XINGCHI_TOKENS`（複数アカウント、`ラベル|JWT`）または `XINGCHI_TOKEN`（単一アカウント）を設定します。`XINGCHI_ACCOUNT_FILE`、`XINGCHI_API_BASE`、`XINGCHI_PROXY`、`XINGCHI_WAIT_SECONDS` も利用できます。

## プロトコル

```http
GET  /api/v1/user/checkin
POST /api/v1/user/checkin
GET  /api/v1/user/checkin
Authorization: Bearer <JWT>
```

最初の GET で `enabled`、`claimed_today`、`amount` などを読み取ります。POST は body なしです。POST 後の GET が `claimed_today=true` でない場合は `UNCONFIRMED` とします。

## 実行

```bash
python -m pip install -r requirements.txt
export XINGCHI_TOKEN='eyJ...'
python xingchi_daily.py
python xingchi_daily.py --query
python xingchi_daily.py --only 1,3-4
```

## プライバシー

JWT、アカウントファイル、レポート、ログ、認証情報を含む画像をコミットしないでください。出力では電話番号、Token、通知用の秘密情報を伏せます。


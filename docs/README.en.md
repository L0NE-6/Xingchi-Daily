<div align="center">

<sub><strong>L0NE-6 · DAILY SIGNAL</strong></sub>

# 🌟 Xingchi Daily
[简体中文](../README.md) · **English** · [繁體中文](README.zh-Hant.md) · [日本語](README.ja.md) · [한국어](README.ko.md) · [Português (BR)](README.pt-BR.md)
> Version: **v1.0.0** (2026-11-24)

**Xingchi AI daily check-in · multi-account · GET/POST status readback · JSONL**


</div>

## What it does

This repository reads the Xingchi panel check-in state and claims the daily
reward with a panel JWT. After the POST it reads the status again; only
`claimed_today=true` is reported as `CLAIMED`.

## Configuration

| Variable | Required | Description |
| :--- | :---: | :--- |
| `XINGCHI_TOKENS` | one of two | Multi-account lines in `label\|JWT` form |
| `XINGCHI_TOKEN` | one of two | Single-account JWT |
| `XINGCHI_ACCOUNT_FILE` | optional | Local account file |
| `XINGCHI_API_BASE` | optional | API base override |
| `XINGCHI_PROXY` | optional | HTTP(S) proxy |
| `XINGCHI_WAIT_SECONDS` | optional | Wait before status readback |
| `PUSHPLUS_TOKEN` | optional | PushPlus |
| `BARK_URL` | optional | Bark |
| `WECOM_WEBHOOK` | optional | WeCom bot |
| `DINGTALK_WEBHOOK` | optional | DingTalk bot |
| `GENERIC_WEBHOOK_URL` | optional | Generic JSON webhook |

## Protocol and success

```http
GET  /api/v1/user/checkin
POST /api/v1/user/checkin
GET  /api/v1/user/checkin
Authorization: Bearer <XINGCHI_PANEL_JWT>
```

The first GET reads `enabled`, `claimed_today`, `amount`, `total_count`,
`total_amount`, and `next_claim_at`. The POST has no body. A successful claim
must be followed by a GET with `claimed_today=true`; an unchanged or unreadable
state is `UNCONFIRMED`.

## Run locally

```bash
python -m pip install -r requirements.txt
export XINGCHI_TOKEN='eyJ...'
python xingchi_daily.py
python xingchi_daily.py --query
python xingchi_daily.py --only 1,3-4
```

## Deploy

For Qinglong, upload `xingchi_daily.py`, set `XINGCHI_TOKENS` or `XINGCHI_TOKEN`,
and run `task xingchi_daily.py`. For GitHub Actions, add the same value as a
repository Secret and run the included workflow.

## Privacy

Do not commit JWTs, account files, reports, logs, or screenshots containing
credentials. The script redacts phone numbers, tokens, and notification
secrets from errors and output.

## Test

```bash
python -m unittest discover -s tests -v
python -m compileall -q .
python -m ruff check .
```

All tests use fake HTTP sessions and do not call the live service.

## License and support

MIT. See `LICENSE`, `NOTICE.md`, and `THIRD_PARTY_NOTICES.md`. Donation QR codes
are only for voluntary support of the author.

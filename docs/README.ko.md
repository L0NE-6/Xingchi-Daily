<div align="center">

<sub><strong>L0NE-6 · DAILY SIGNAL</strong></sub>

# 🌟 Xingchi Daily

**Xingchi AI 일일 체크인 · 다중 계정 · GET/POST 상태 재조회 · JSONL**

[简体中文](../README.md) · [English](README.en.md) · [繁體中文](README.zh-Hant.md) · [日本語](README.ja.md) · [한국어](README.ko.md) · [Português (BR)](README.pt-BR.md)

</div>

## 기능

웹 패널 JWT로 Xingchi의 체크인 상태를 읽고, 받을 수 있을 때 일일 보상을 요청합니다. POST 후 상태를 다시 읽고 `claimed_today=true`인 경우에만 `CLAIMED`로 보고합니다.

## 설정

`XINGCHI_TOKENS`(다중 계정, 각 줄 `라벨|JWT`) 또는 `XINGCHI_TOKEN`(단일 계정)을 설정합니다. `XINGCHI_ACCOUNT_FILE`, `XINGCHI_API_BASE`, `XINGCHI_PROXY`, `XINGCHI_WAIT_SECONDS`도 지원합니다.

## 프로토콜

```http
GET  /api/v1/user/checkin
POST /api/v1/user/checkin
GET  /api/v1/user/checkin
Authorization: Bearer <JWT>
```

첫 GET은 `enabled`, `claimed_today`, `amount` 등을 읽습니다. POST에는 body가 없습니다. POST 후 GET에서 `claimed_today=true`가 확인되지 않으면 `UNCONFIRMED`입니다.

## 실행

```bash
python -m pip install -r requirements.txt
export XINGCHI_TOKEN='eyJ...'
python xingchi_daily.py
python xingchi_daily.py --query
python xingchi_daily.py --only 1,3-4
```

## 개인정보

JWT, 계정 파일, 보고서, 로그, 자격 증명이 포함된 스크린샷을 커밋하지 마세요. 출력에서는 전화번호, Token, 알림 비밀값을 가립니다.


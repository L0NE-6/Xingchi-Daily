<div align="center">

<sub><strong>L0NE-6 · DAILY SIGNAL</strong></sub>

# 🌟 Xingchi Daily

**Check-in diário do Xingchi AI · múltiplas contas · leitura de estado GET/POST · JSONL**

[简体中文](../README.md) · [English](README.en.md) · [繁體中文](README.zh-Hant.md) · [日本語](README.ja.md) · [한국어](README.ko.md) · **Português (BR)**
> Versão: **v1.0.0** (2026-11-24)

</div>

## O que faz

Lê o estado de check-in do Xingchi com um JWT do painel web e solicita a
recompensa diária quando disponível. Após o POST, lê o estado novamente; só
`claimed_today=true` é informado como `CLAIMED`.

## Configuração

Use `XINGCHI_TOKENS` (várias contas, uma por linha no formato `rótulo|JWT`) ou
`XINGCHI_TOKEN` (uma conta). Também estão disponíveis `XINGCHI_ACCOUNT_FILE`,
`XINGCHI_API_BASE`, `XINGCHI_PROXY` e `XINGCHI_WAIT_SECONDS`.

## Protocolo

```http
GET  /api/v1/user/checkin
POST /api/v1/user/checkin
GET  /api/v1/user/checkin
Authorization: Bearer <JWT>
```

O primeiro GET lê `enabled`, `claimed_today`, `amount` e campos relacionados.
O POST não envia body. Se o GET posterior não confirmar `claimed_today=true`, o
resultado é `UNCONFIRMED`.

## Execução

```bash
python -m pip install -r requirements.txt
export XINGCHI_TOKEN='eyJ...'
python xingchi_daily.py
python xingchi_daily.py --query
python xingchi_daily.py --only 1,3-4
```

## Privacidade

Não faça commit de JWT, arquivos de conta, relatórios, logs ou capturas com
credenciais. O script oculta telefone, Token e segredos de notificação.

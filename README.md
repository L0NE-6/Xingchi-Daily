<div align="center">

<sub><strong>L0NE-6 · DAILY SIGNAL</strong></sub>

# 🌟 Xingchi Daily

**星驰 AI 每日签到 · 多账号 · GET/POST 状态回读 · JSONL 结果**

> 当前版本：**v1.0.0**（2026-11-24） · 由 L0NE-6 原创维护

[简体中文](README.md) · [English](docs/README.en.md) · [繁體中文](docs/README.zh-Hant.md) · [日本語](docs/README.ja.md) · [한국어](docs/README.ko.md) · [Português (BR)](docs/README.pt-BR.md)

🔐 网页面板令牌 · 🎁 每日签到 · 👥 多账号隔离 · 🧾 JSONL · 📢 可选推送 · 🐧 青龙友好 · ☁️ GitHub Actions

<img src="https://img.shields.io/badge/Version-v1.0.0-2ea44f?style=for-the-badge&logo=github" />
<img src="https://img.shields.io/badge/Python-3.9+-3776AB?style=for-the-badge&logo=python&logoColor=white" />
<img src="https://img.shields.io/badge/Platform-Windows%20%7C%20Linux%20%7C%20%E9%9D%92%E9%BE%99-4EAA25?style=for-the-badge&logo=linux&logoColor=white" />
<img src="https://img.shields.io/badge/Deploy-%E9%9D%92%E9%BE%99%20%7C%20GitHub%20Actions-2088FF?style=for-the-badge&logo=githubactions&logoColor=white" />
<img src="https://img.shields.io/badge/License-MIT-F472B6?style=for-the-badge" />

</div>

---

<a id="usage-policy"></a>
## 🚫 使用边界

> [!IMPORTANT]
> **官方版本永久免费。** 未经作者书面许可，禁止付费包装、搬运引流、冒充作者，或使用作者身份与二维码制造官方授权假象。

禁止将本仓库、脚本、部署说明或 Release 包装成付费资源、内部版、独家版、会员权益、收费课程、代部署服务或包更新服务；禁止删除作者与版权信息后冒充原创。完整规则见 **[NOTICE.md](NOTICE.md)**。

---

## ✨ 30 秒速览

| 维度 | 说明 |
| :--- | :--- |
| **做什么** | 使用星驰网页面板令牌，读取今日签到状态并在可领取时提交签到。 |
| **输入** | `XINGCHI_TOKENS` 多账号，或 `XINGCHI_TOKEN` 单账号；也支持账号文件。 |
| **输出** | 每账号一行 JSON，最后一行 `SUMMARY` JSON；不输出面板令牌。 |
| **部署** | Windows / Linux / 青龙面板 / GitHub Actions。 |
| **依赖** | Python 3.9+；运行时依赖 `requests`。 |
| **成功判据** | `POST` 后重新 `GET /api/v1/user/checkin`，必须读到 `claimed_today=true`；只有领取响应不算成功。 |

---

## 🧠 签到与回读

脚本使用面板登录令牌访问：

```http
GET  /api/v1/user/checkin
POST /api/v1/user/checkin
GET  /api/v1/user/checkin
Authorization: Bearer <XINGCHI_PANEL_JWT>
```

`GET` 读取 `enabled`、`claimed_today`、`amount`、`total_count`、`total_amount` 和 `next_claim_at`。

`POST` 不带请求体。提交后必须再次读取状态，只有 `claimed_today=true` 才报告 `CLAIMED`。`CHECKIN_ALREADY_CLAIMED` 或重复领取状态按中性 `ALREADY` 处理；`enabled=false` 按 `INACTIVE` 处理；回读仍为 false 时报告 `UNCONFIRMED`。

---

## 🔑 获取面板令牌

在浏览器登录星驰网页面板，从登录会话中取得面板 JWT。不要把令牌发到 Issue、群聊、日志或截图。

账号格式：

```text
主号|eyJ...
小号|eyJ...
```

也支持 JSON：

```json
[{"name":"主号","panelToken":"eyJ..."},{"name":"小号","panelToken":"eyJ..."}]
```

---

## 🚀 部署方式一：青龙面板

1. 将 `xingchi_daily.py` 上传到青龙脚本目录。
2. 在青龙环境变量中新增 `XINGCHI_TOKENS` 或 `XINGCHI_TOKEN`。
3. 新建任务，命令使用 `task xingchi_daily.py`。
4. 在青龙依赖管理中安装 `requests`，或执行 `pip3 install requests`。

建议每天运行一次，例如 `17 7 * * *`。

---

## ☁️ 部署方式二：GitHub Actions

工作流位于 `.github/workflows/xingchi.yml`：

- `push` 到 `main`：运行测试、编译检查和 Ruff；
- `schedule`：每天执行一次；
- `workflow_dispatch`：手动运行；
- 未配置 Secret 时显示 SKIPPED，不把空凭据当成签到失败；
- 原始 JSONL 会作为 artifact 保留。

添加 Secret：

| Secret | 必填 | 内容 |
| :--- | :---: | :--- |
| `XINGCHI_TOKENS` | 二选一 | 多账号，每行 `备注\|JWT` |
| `XINGCHI_TOKEN` | 二选一 | 单账号 JWT |

---

## 🔧 环境变量

| 变量 | 必填 | 说明 |
| :--- | :---: | :--- |
| `XINGCHI_TOKENS` | 二选一 | 多账号，每行 `备注\|JWT` |
| `XINGCHI_TOKEN` | 二选一 | 单账号 JWT |
| `XINGCHI_ACCOUNT_FILE` | 可选 | 账号文件路径；环境变量为空时读取 |
| `XINGCHI_API_BASE` | 可选 | API 根地址覆盖，默认 `https://api.xingchiapi.com` |
| `XINGCHI_PROXY` | 可选 | HTTP(S) 代理 |
| `XINGCHI_WAIT_SECONDS` | 可选 | 领取后状态回读等待秒数，默认 `0.5` |
| `PUSHPLUS_TOKEN` | 可选 | PushPlus |
| `BARK_URL` | 可选 | Bark |
| `WECOM_WEBHOOK` | 可选 | 企业微信机器人 |
| `DINGTALK_WEBHOOK` | 可选 | 钉钉机器人 |
| `GENERIC_WEBHOOK_URL` | 可选 | 通用 JSON webhook |

---

## ⌨️ 本地运行

```powershell
python -m pip install -r requirements.txt
$env:XINGCHI_TOKEN = "eyJ..."
python .\xingchi_daily.py
python .\xingchi_daily.py --query
python .\xingchi_daily.py --only 1,3-4
python .\xingchi_daily.py --no-notify
```

`--query` 只读取签到状态，不发送签到请求。

---

## ✅ 结果状态

| 状态 | 含义 | 是否成功 |
| :--- | :--- | :---: |
| `CLAIMED` | POST 后回读 `claimed_today=true` | ✅ |
| `ALREADY` | 服务端确认今天已经领取 | ✅ |
| `QUERY` | 查询模式，未发送签到请求 | ✅ |
| `INACTIVE` | 服务端明确表示活动未启用 | ✅ |
| `AUTH_EXPIRED` | 面板令牌失效或需要重新登录 | ❌ |
| `UNCONFIRMED` | 请求已发，但状态回读未确认 | ❌ |
| `API_ERROR` / `INVALID_RESPONSE` | HTTP、JSON 或业务结构错误 | ❌ |

`SUMMARY.ok=true` 需要至少一个账号且所有结果均为成功或中性状态。

---

## 🧪 测试与质量检查

```powershell
python -m unittest discover -s tests -v
python -m compileall -q .
python -m ruff check .
```

测试使用 fake session，不访问真实星驰接口，不需要真实令牌。

---

## 🔒 隐私说明

- 仓库不包含账号、手机号、面板 JWT 或推送凭据。
- JWT 只通过环境变量、青龙变量或 GitHub Secrets 注入。
- 输出会脱敏手机号，错误信息会遮蔽 JWT 和推送凭据。
- `.gitignore` 已排除本地账号文件、报告、缓存和日志。

---

## 📁 目录结构

```text
Xingchi-Daily/
├── .github/workflows/xingchi.yml
├── assets/
│   ├── donate-alipay.jpg
│   └── donate-wechat.png
├── docs/
│   ├── README.en.md
│   ├── README.zh-Hant.md
│   ├── README.ja.md
│   ├── README.ko.md
│   └── README.pt-BR.md
├── tests/test_xingchi_daily.py
├── CHANGELOG.md
├── LICENSE
├── NOTICE.md
├── THIRD_PARTY_NOTICES.md
├── xingchi_daily.py
├── pyproject.toml
├── README.md
└── requirements.txt
```

---

## ☕ 支持与投喂

脚本完全免费。如果它确实帮你省了时间，欢迎自愿赞赏；不影响任何功能，也不影响 Issue 响应。

<p align="center">
  <img src="assets/donate-wechat.png" width="260" alt="微信赞赏码" />
  &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
  <img src="assets/donate-alipay.jpg" width="260" alt="支付宝收款码" />
</p>
<p align="center"><sub>💚 微信支付（左） &nbsp;|&nbsp; 💙 支付宝（右）</sub></p>

---

## ⚠️ 免责声明

本项目用于个人学习和合法的个人自动化。星驰 AI 的活动规则、接口、奖励数量和账号资格由平台决定；使用前请确认对应服务条款，并自行承担账号、网络和活动变化带来的风险。


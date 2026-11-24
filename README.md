<div align="center">

<sub><strong>L0NE-6 · XINGCHI SIGNAL</strong></sub>

# Xingchi Daily

**星驰 AI 每日签到 · 多账号 · GET/POST 状态回读 · JSONL 结果**

> 当前版本：**v1.0.0**（2026-11-24） · 提交签到后重新 GET，只有 claimed_today=true 才算完成

[简体中文](README.md) · [English](docs/README.en.md) · [繁體中文](docs/README.zh-Hant.md) · [日本語](docs/README.ja.md) · [한국어](docs/README.ko.md) · [Português (BR)](docs/README.pt-BR.md)

<img src="https://img.shields.io/badge/Features-GET%20%2F%20POST-6F42C1?style=for-the-badge" alt="Features" />
<a href="https://github.com/L0NE-6/Xingchi-Daily/releases"><img src="https://img.shields.io/github/v/release/L0NE-6/Xingchi-Daily?style=for-the-badge&label=Release&color=2ea44f&logo=github" alt="Release" /></a>
<a href="https://github.com/L0NE-6/Xingchi-Daily/stargazers"><img src="https://img.shields.io/github/stars/L0NE-6/Xingchi-Daily?style=for-the-badge&label=Stars&color=FFC75F&logo=github" alt="Stars" /></a>
<img src="https://img.shields.io/badge/Python-3.9%2B-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python" />
<img src="https://img.shields.io/badge/Platform-Windows%20%7C%20Linux%20%7C%20Qinglong-4EAA25?style=for-the-badge&logo=linux&logoColor=white" alt="Platform" />
<img src="https://img.shields.io/badge/License-MIT-F472B6?style=for-the-badge" alt="License" />

🔐 面板 JWT · 🎁 每日签到 · 👥 多账号 · 🧾 JSONL · 📢 推送 · 🐧 青龙 · ☁️ Actions

[⚡ 30 秒速览](#quick-look) · [🔁 协议与回读](#protocol) · [🔐 凭据](#credentials) · [🐧 青龙](#qinglong) · [☁️ Actions](#actions) · [⌨️ CLI](#cli-json) · [✅ 成功判据](#success) · [✦ 星轨](#star-trail)

</div>

---

<a id="usage-policy"></a>
## 🚫 使用边界与禁止倒卖

> [!IMPORTANT]
> **官方版本永久免费。** 未经作者书面许可，禁止倒卖、付费包装、搬运引流、冒充作者，或使用作者身份与二维码制造官方授权假象。

本仓库、脚本、部署说明和 Release 下载保持免费公开。禁止将本项目或其轻度改名版本包装为付费资源、内部版、独家版、会员权益、收费课程、代部署服务或包更新服务；禁止搬运到其他账号、群组、频道、网盘、电商平台或付费社群进行涨粉、截流、倒卖和引流；禁止删除作者与版权信息后冒充原创。

完整规则见 [NOTICE.md](NOTICE.md)。第三方以“下载费 / 激活费 / 内部版 / 代部署 / 会员门槛”等名义收费，均与作者无关，请停止付款并保留证据。

---

<a id="quick-look"></a>
## ⚡ 30 秒速览

| 维度 | 说明 |
| :--- | :--- |
| **做什么** | 使用星驰网页面板令牌读取今日签到状态并在可领取时提交。 |
| **输入** | `XINGCHI_TOKENS` 多账号，或 `XINGCHI_TOKEN` 单账号；也支持账号文件。 |
| **协议** | `GET /api/v1/user/checkin` → `POST` → 再次 `GET`。 |
| **回读** | 读取 `enabled`、`claimed_today`、`amount` 和累计字段。 |
| **输出** | 每账号一条 JSON，最后一行 `SUMMARY` JSON。 |
| **成功判据** | POST 后回读 `claimed_today=true`。 |

---

## 🧭 这是什么 / 覆盖范围

星驰脚本使用网页面板 JWT 访问 `api.xingchiapi.com`，先读取签到状态，再按需提交 POST，最后再次 GET 确认。

### 覆盖范围

- `XINGCHI_TOKENS`、`XINGCHI_TOKEN`、JSON 账号和账号文件。
- `--query` 只读状态，不发送签到请求。
- `enabled=false` 中性返回 `INACTIVE`。
- `CHECKIN_ALREADY_CLAIMED` / 409 在回读确认后返回 `ALREADY`。
- 奖励、累计次数、累计金额和下次领取时间记录。
- JSONL、Actions artifact 和可选通知。

---

<a id="protocol"></a>
## 🔁 协议与回读流程

### 请求链

```http
GET  /api/v1/user/checkin
POST /api/v1/user/checkin
GET  /api/v1/user/checkin
Authorization: Bearer <XINGCHI_PANEL_JWT>
```

POST 不带请求体。提交后必须重新读取状态，只有 `claimed_today=true` 才报告 `CLAIMED`。

| 字段 | 说明 |
| :--- | :--- |
| `enabled` | 签到功能是否开启。 |
| `claimed_today` | 今日是否已领取。 |
| `amount` | 本次奖励。 |
| `total_count` | 累计领取次数。 |
| `total_amount` | 累计领取金额。 |
| `next_claim_at` | 下次可领取时间。 |

`CHECKIN_ALREADY_CLAIMED` 或重复领取只在回读确认已签后按 `ALREADY` 处理。回读仍为 false 时返回 `UNCONFIRMED`。

---

<a id="credentials"></a>
## 🔐 凭据与环境变量

### 账号格式

```text
主号|eyJ...
小号|eyJ...
```

也支持 JSON 字段 `name`、`panelToken`。

| 变量 | 必填 | 说明 |
| :--- | :---: | :--- |
| `XINGCHI_TOKENS` | 二选一 | 多账号，每行 `备注\|JWT`。 |
| `XINGCHI_TOKEN` | 二选一 | 单账号 JWT。 |
| `XINGCHI_ACCOUNT_FILE` | 否 | 账号文件路径。 |
| `XINGCHI_API_BASE` | 否 | API 根地址，默认 `https://api.xingchiapi.com`。 |
| `XINGCHI_PROXY` | 否 | HTTP(S) 代理。 |
| `XINGCHI_WAIT_SECONDS` | 否 | 回读等待秒数，默认 `0.5`。 |
| `PUSHPLUS_TOKEN` / `BARK_URL` | 否 | 推送。 |
| `WECOM_WEBHOOK` / `DINGTALK_WEBHOOK` | 否 | 群机器人。 |
| `GENERIC_WEBHOOK_URL` | 否 | 通用 JSON webhook。 |

---

## 💻 本地快速开始

### PowerShell

```powershell
python -m pip install -r requirements.txt
$env:XINGCHI_TOKEN = "eyJ..."
python .\xingchi_daily.py
```

### Bash

```bash
python -m pip install -r requirements.txt
export XINGCHI_TOKEN='eyJ...'
python xingchi_daily.py
```

常用参数：`--query`、`--only 1,3-4`、`--accounts-file xingchi_accounts.txt`、`--api-base https://api.xingchiapi.com`、`--wait-seconds 0.5`、`--no-notify`。

---

<a id="qinglong"></a>
## 🐧 青龙

1. 在青龙依赖管理中安装 `requests`，或执行 `pip3 install -r requirements.txt`。
2. 上传 `xingchi_daily.py` 到脚本目录。
3. 在环境变量中配置 `XINGCHI_TOKENS` 或 `XINGCHI_TOKEN`。
4. 新建定时任务，命令使用 `task xingchi_daily.py`，不要直接写裸 `python`。
5. 建议北京时间：`17 7 * * *`。青龙按面板本地时间执行。

```bash
pip3 install -r requirements.txt
task xingchi_daily.py
```

---

<a id="actions"></a>
## ☁️ GitHub Actions、Secrets 与定时

工作流：`.github/workflows/xingchi.yml`。

| 事件 | 行为 |
| :--- | :--- |
| `push` 到 `main` | pytest、编译检查、Ruff。 |
| `schedule` | 先测试，再执行签到并上传 JSONL artifact。 |
| `workflow_dispatch` | 手动执行。 |
| 未配置 Secret | 输出 notice 并跳过在线执行。 |

### Secrets

| Secret | 说明 |
| :--- | :--- |
| `XINGCHI_TOKENS` | 多账号 JWT。 |
| `XINGCHI_TOKEN` | 单账号 JWT。 |
| `PUSHPLUS_TOKEN` / `BARK_URL` | 推送。 |
| `WECOM_WEBHOOK` / `DINGTALK_WEBHOOK` | 群机器人。 |
| `GENERIC_WEBHOOK_URL` | 通用 JSON webhook。 |

内置定时为 UTC `17 23 * * *`，对应北京时间约 07:17。原始 JSONL 作为 `xingchi-report` artifact 保留。

---

<a id="cli-json"></a>
## ⌨️ CLI 与 JSON 输出

```powershell
python .\xingchi_daily.py
python .\xingchi_daily.py --query
python .\xingchi_daily.py --only 1,3-4
python .\xingchi_daily.py --no-notify
```

账号 JSON 示例：

```json
{"type":"account","provider":"xingchi","index":1,"label":"主号","status":"CLAIMED","ok":true,"message":"服务端确认签到","http_status":200,"amount":"1","total_count":"12","total_amount":"12","next_claim_at":"2026-11-25T00:00:00+08:00","details":[]}
```

| 字段 | 说明 |
| :--- | :--- |
| `status` / `ok` | 结果状态与是否成功。 |
| `amount` / `total_count` / `total_amount` | 本次奖励与累计值。 |
| `next_claim_at` | 下次可领取时间。 |
| `details` | 非敏感补充信息。 |

---

<a id="result-codes"></a>
## 🧾 结果码

| 结果码 | 成功 | 含义 |
| :--- | :---: | :--- |
| `CLAIMED` | 是 | POST 后回读 `claimed_today=true`。 |
| `ALREADY` | 是 | 服务端确认今天已经领取。 |
| `QUERY` | 是 | 查询模式，未发送签到请求。 |
| `INACTIVE` | 是 | 服务端明确表示活动未启用。 |
| `AUTH_EXPIRED` | 否 | 面板令牌失效或需要重新登录。 |
| `UNCONFIRMED` | 否 | 请求已发，但状态回读未确认。 |
| `API_ERROR` | 否 | HTTP、JSON 或业务结构错误。 |
| `CONFIG_ERROR` | 否 | 账号、站点或参数配置错误。 |

---

<a id="success"></a>
## ✅ 成功判据

| 场景 | 必须满足 |
| :--- | :--- |
| 本次签到 | POST 后再次 GET，`claimed_today=true`。 |
| 今日已签到 | 运行前 `claimed_today=true`，或重复领取后回读确认。 |
| 查询模式 | 只读状态，不发送 POST。 |
| 未确认 | 回读仍为 false 或结构异常时失败。 |

---

## 🧪 测试与静态检查

```bash
python -m pytest -q
python -m compileall -q .
python -m ruff check .
```

离线测试覆盖账号解析、查询模式、POST 后回读、回读未确认、已签到短路、站点未开启、鉴权、重复领取后回读和状态结构异常。

---

## 🧱 设计原则

- **GET → POST → GET**：每次领取都有明确前后状态。
- **令牌隔离**：单账号令牌只服务本账号。
- **已领取中性**：重复运行不制造失败。
- **活动未开启**：`enabled=false` 单独分类。
- **输出脱敏**：手机号和 JWT 不进入日志。

---

## 🔒 隐私

仓库不包含账号、手机号、面板 JWT、日志或真实响应。`xingchi_accounts.txt`、`xingchi-report.json`、`xingchi-report.jsonl`、`auth.json`、Cookie 和缓存已由 `.gitignore` 排除。

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

## 📦 版本与发布

- 当前清单版本：`v1.0.0`，日期 `2026-11-24`。
- 脚本版本与 `xingchi_daily.py` 内的 `VERSION` 保持一致。
- 更新记录见 [CHANGELOG.md](CHANGELOG.md)，下载入口见 [Releases](https://github.com/L0NE-6/Xingchi-Daily/releases)。
- Release 徽标由 GitHub 实时生成；如果页面尚未创建对应 Release，以 `CHANGELOG.md` 和仓库提交为准。

---

## ⚠️ 免责声明

本项目用于个人学习与个人自动化。星驰 AI 的活动规则、接口、奖励、风控策略和账号资格由服务方决定。使用前请确认对应服务条款，并自行承担接口变化、账号限制和网络环境带来的风险。

---

## ☕ 支持与投喂

脚本完全免费，赞赏纯自愿，不影响任何功能，也不影响 Issue 响应。

<p align="center">
  <img src="assets/donate-wechat.png" width="260" alt="微信赞赏码" />
  &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
  <img src="assets/donate-alipay.jpg" width="260" alt="支付宝收款码" />
</p>
<p align="center"><sub>💚 微信支付（左） &nbsp;|&nbsp; 💙 支付宝（右，支持信用卡 / 花呗）</sub></p>

> 收款码仅用于向作者自愿赞赏。任何第三方以代下载、代部署、内部资源或会员群为由收费，均与作者无关。

---

## 💬 反馈与贡献

- 提交 [Issue](https://github.com/L0NE-6/Xingchi-Daily/issues) 时附运行日志、脱敏后的错误字段和复现步骤。
- 发起 [Pull Request](https://github.com/L0NE-6/Xingchi-Daily/pulls) 时保持单文件运行、离线测试和凭据脱敏约束。
- 不要在任何 Issue、PR、截图或日志中粘贴真实 Token、Cookie、密码、UID、手机号或邮箱。

---

<a id="star-trail"></a>
## ✦ Star History / 星轨

<a href="https://star-history.com/#L0NE-6/Xingchi-Daily&Date">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/svg?repos=L0NE-6/Xingchi-Daily&type=Date&theme=dark" />
    <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/svg?repos=L0NE-6/Xingchi-Daily&type=Date" />
    <img alt="Xingchi-Daily Star History" src="https://api.star-history.com/svg?repos=L0NE-6/Xingchi-Daily&type=Date" />
  </picture>
</a>

<div align="center">
  <sub>L0NE-6 · DAILY SIGNAL &nbsp;|&nbsp; 点个 <b>Star</b>，让下一轮自动化有迹可循</sub>
</div>

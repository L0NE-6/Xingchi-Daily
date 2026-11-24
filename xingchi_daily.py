#!/usr/bin/env python3
"""Xingchi daily check-in runner with strict status readback."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

import requests


VERSION = "1.0.0"
PROVIDER = "xingchi"
API_BASE = "https://api.xingchiapi.com"
CHECKIN_PATH = "/api/v1/user/checkin"

TOKENS_ENV = "XINGCHI_TOKENS"
TOKEN_ENV = "XINGCHI_TOKEN"
ACCOUNT_FILE_ENV = "XINGCHI_ACCOUNT_FILE"
API_BASE_ENV = "XINGCHI_API_BASE"
PROXY_ENV = "XINGCHI_PROXY"
WAIT_ENV = "XINGCHI_WAIT_SECONDS"
DEFAULT_ACCOUNT_FILE = "xingchi_accounts.txt"

DEFAULT_TIMEOUT = 20.0
DEFAULT_WAIT_SECONDS = 0.5
SUCCESS_STATUSES = {"CLAIMED", "ALREADY", "QUERY", "INACTIVE"}
PHONE_PATTERN = re.compile(r"(?<!\d)(?:\+?86[- ]?)?(1[3-9]\d{9})(?!\d)")


class XingchiError(Exception):
    """Base class for controlled Xingchi errors."""


class ConfigError(XingchiError):
    """Account or command configuration is invalid."""


class SessionExpired(XingchiError):
    """The panel token is no longer accepted."""


class APIError(XingchiError):
    """The service returned an HTTP, JSON, or business error."""

    def __init__(self, message: str, *, status: int = 0, code: str = "") -> None:
        super().__init__(message)
        self.status = status
        self.code = code


@dataclass(frozen=True)
class Account:
    name: str
    token: str

    @property
    def label(self) -> str:
        return redact_phone(self.name or "Xingchi-%s" % mask_secret(self.token, keep=4))


@dataclass
class CheckinStatus:
    enabled: bool
    claimed_today: bool
    amount: Optional[Decimal] = None
    total_count: Optional[Decimal] = None
    total_amount: Optional[Decimal] = None
    next_claim_at: str = ""


@dataclass
class RunResult:
    index: int
    label: str
    status: str
    message: str
    http_status: int = 0
    amount: Optional[Decimal] = None
    total_count: Optional[Decimal] = None
    total_amount: Optional[Decimal] = None
    next_claim_at: str = ""
    detail_lines: List[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return self.status in SUCCESS_STATUSES

    def as_dict(self) -> Dict[str, Any]:
        return {
            "type": "account",
            "provider": PROVIDER,
            "index": self.index,
            "label": self.label,
            "status": self.status,
            "ok": self.ok,
            "message": self.message,
            "http_status": self.http_status,
            "amount": format_decimal(self.amount),
            "total_count": format_decimal(self.total_count),
            "total_amount": format_decimal(self.total_amount),
            "next_claim_at": self.next_claim_at,
            "details": list(self.detail_lines),
        }


def emit(payload: Dict[str, Any]) -> None:
    print(
        json.dumps(payload, ensure_ascii=False, sort_keys=True, default=str),
        flush=True,
    )


def env_text(name: str, default: str = "") -> str:
    return os.environ.get(name, default).strip()


def redact_phone(text: str) -> str:
    def replace(match: re.Match[str]) -> str:
        phone = match.group(1)
        return "%s****%s" % (phone[:3], phone[-4:])

    return PHONE_PATTERN.sub(replace, str(text or ""))


def mask_secret(value: Any, keep: int = 4) -> str:
    text = str(value or "").strip()
    if not text:
        return "-"
    if len(text) <= keep + 4:
        return "****"
    return "%s****%s" % (text[:keep], text[-4:])


def sanitize_message(message: Any, account: Optional[Account] = None) -> str:
    text = str(message or "").replace("\r", " ").replace("\n", " ").strip()
    if account is not None and account.token:
        text = text.replace(account.token, "[redacted-token]")
    for name in (
        "PUSHPLUS_TOKEN",
        "BARK_URL",
        "WECOM_WEBHOOK",
        "DINGTALK_WEBHOOK",
        "GENERIC_WEBHOOK_URL",
        PROXY_ENV,
    ):
        value = env_text(name)
        if value:
            text = text.replace(value, "[redacted-%s]" % name.lower())
    return redact_phone(text)[:800]


def parse_decimal(value: Any) -> Optional[Decimal]:
    if value is None or isinstance(value, bool):
        return None
    try:
        number = Decimal(str(value).strip())
    except (InvalidOperation, ValueError):
        return None
    if not number.is_finite():
        return None
    return number


def format_decimal(value: Optional[Decimal]) -> Optional[str]:
    if value is None:
        return None
    normalized = value.normalize()
    if normalized == normalized.to_integral():
        return str(normalized.quantize(Decimal("1")))
    return format(normalized, "f").rstrip("0").rstrip(".")


def normalize_token(value: Any) -> str:
    token = str(value or "").strip()
    if token.lower().startswith("bearer "):
        token = token[7:].strip()
    if not token or any(char.isspace() for char in token):
        return ""
    if any(ord(char) < 32 or ord(char) == 127 for char in token):
        return ""
    return token


def _json_accounts(value: Any) -> List[Account]:
    items = value.get("accounts") if isinstance(value, dict) else value
    if not isinstance(items, list):
        raise ConfigError("XINGCHI account JSON must be a list or an object with accounts[]")
    accounts: List[Account] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        token = normalize_token(
            item.get("token")
            or item.get("panelToken")
            or item.get("access")
            or item.get("key")
        )
        if not token:
            continue
        name = str(
            item.get("name") or item.get("label") or item.get("note") or ""
        ).strip()
        accounts.append(Account(name=name, token=token))
    return accounts


def parse_accounts(raw: str) -> List[Account]:
    text = str(raw or "").strip()
    if not text:
        return []
    if text.startswith("[") or text.startswith("{"):
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError as error:
            raise ConfigError("XINGCHI account JSON is invalid: %s" % error) from error
        accounts = _json_accounts(parsed)
    else:
        accounts = []
        for line_number, raw_line in enumerate(text.splitlines(), 1):
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            if "|" in line:
                name, token = line.split("|", 1)
            else:
                name, token = "", line
            normalized = normalize_token(token)
            if not normalized:
                raise ConfigError("XINGCHI account line %d has no valid token" % line_number)
            accounts.append(Account(name=name.strip(), token=normalized))

    deduped: List[Account] = []
    seen = set()
    for account in accounts:
        if account.token in seen:
            continue
        seen.add(account.token)
        deduped.append(account)
    return deduped


def load_accounts(account_file: Optional[str] = None) -> List[Account]:
    raw = env_text(TOKENS_ENV) or env_text(TOKEN_ENV)
    if not raw:
        path = account_file or env_text(ACCOUNT_FILE_ENV)
        if not path and Path(DEFAULT_ACCOUNT_FILE).exists():
            path = DEFAULT_ACCOUNT_FILE
        if path:
            try:
                raw = Path(path).read_text(encoding="utf-8")
            except OSError as error:
                raise ConfigError("cannot read XINGCHI account file: %s" % error) from error
    accounts = parse_accounts(raw)
    if not accounts:
        raise ConfigError(
            "XINGCHI_TOKENS, XINGCHI_TOKEN, or XINGCHI_ACCOUNT_FILE is not configured"
        )
    return accounts


def parse_only(value: str, total: int) -> set[int]:
    if not value.strip():
        return set(range(1, total + 1))
    selected: set[int] = set()
    for part in value.split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            start_text, end_text = part.split("-", 1)
            try:
                start, end = int(start_text), int(end_text)
            except ValueError as error:
                raise ConfigError("invalid --only range: %s" % part) from error
            if start > end:
                start, end = end, start
            selected.update(range(start, end + 1))
        else:
            try:
                selected.add(int(part))
            except ValueError as error:
                raise ConfigError("invalid --only item: %s" % part) from error
    if not selected or min(selected) < 1 or max(selected) > total:
        raise ConfigError("--only contains an account outside 1..%d" % total)
    return selected


def unwrap_data(payload: Any) -> Any:
    if isinstance(payload, dict) and isinstance(payload.get("data"), dict):
        return payload["data"]
    return payload


def payload_code(payload: Any) -> str:
    if not isinstance(payload, dict):
        return ""
    for source in (payload, payload.get("data")):
        if not isinstance(source, dict):
            continue
        for key in ("code", "reason", "error"):
            value = source.get(key)
            if isinstance(value, dict):
                value = value.get("code") or value.get("type")
            if value is not None and str(value).strip():
                return str(value).strip()
    return ""


def payload_message(payload: Any) -> str:
    if not isinstance(payload, dict):
        return ""
    for source in (payload, payload.get("data")):
        if not isinstance(source, dict):
            continue
        for key in ("message", "msg", "desc", "detail"):
            value = source.get(key)
            if value is not None and str(value).strip():
                return str(value).strip()
    return ""


def is_auth_error(status: int, payload: Any) -> bool:
    code = payload_code(payload).upper()
    return status in (401, 403) or code in {
        "INVALID_TOKEN",
        "UNAUTHORIZED",
        "TOKEN_EXPIRED",
        "AUTH_EXPIRED",
    }


def parse_status(payload: Any, status: int = 0) -> CheckinStatus:
    if is_auth_error(status, payload):
        raise SessionExpired("Xingchi panel login expired")
    code = payload_code(payload).upper()
    if payload.get("success") is False or code not in {"", "0", "SUCCESS"}:
        raise APIError(
            "Xingchi check-in status returned a business error: %s"
            % (payload_message(payload) or code),
            status=status,
            code=code or "INVALID_RESPONSE",
        )
    data = unwrap_data(payload)
    if not isinstance(data, dict):
        raise APIError(
            "Xingchi check-in data is not an object",
            status=status,
            code="INVALID_RESPONSE",
        )
    enabled = data.get("enabled")
    claimed = data.get("claimed_today")
    if not isinstance(enabled, bool) or not isinstance(claimed, bool):
        raise APIError(
            "Xingchi check-in response lacks enabled/claimed_today booleans",
            status=status,
            code="INVALID_RESPONSE",
        )
    return CheckinStatus(
        enabled=enabled,
        claimed_today=claimed,
        amount=parse_decimal(data.get("amount")),
        total_count=parse_decimal(data.get("total_count")),
        total_amount=parse_decimal(data.get("total_amount")),
        next_claim_at=str(data.get("next_claim_at") or ""),
    )


class XingchiClient:
    """HTTP client with a replaceable session factory for offline tests."""

    def __init__(
        self,
        api_base: str = API_BASE,
        timeout: float = DEFAULT_TIMEOUT,
        wait_seconds: float = DEFAULT_WAIT_SECONDS,
        proxy: str = "",
        session_factory: Any = None,
        sleeper: Any = time.sleep,
    ) -> None:
        self.api_base = str(api_base or API_BASE).rstrip("/")
        self.timeout = max(1.0, float(timeout))
        self.wait_seconds = max(0.0, float(wait_seconds))
        self.proxy = str(proxy or "").strip()
        self.session_factory = session_factory or requests.Session
        self.sleeper = sleeper

    def _new_session(self) -> Any:
        session = self.session_factory()
        session.headers.update(
            {
                "Accept": "application/json",
                "User-Agent": "Xingchi-Daily/1.0",
            }
        )
        if self.proxy:
            session.proxies.update({"http": self.proxy, "https": self.proxy})
        return session

    def _request(
        self,
        account: Account,
        method: str,
    ) -> Tuple[int, Any]:
        session = self._new_session()
        headers = {
            "Authorization": "Bearer %s" % account.token,
            "Accept": "application/json",
        }
        try:
            response = session.request(
                method,
                self.api_base + CHECKIN_PATH,
                headers=headers,
                timeout=self.timeout,
                allow_redirects=False,
            )
        except requests.RequestException as error:
            raise APIError(
                "Xingchi network request failed: %s"
                % sanitize_message(error, account)
            ) from error
        finally:
            session.close()

        status = int(getattr(response, "status_code", 0) or 0)
        if 300 <= status < 400:
            raise APIError(
                "Xingchi returned a redirect (HTTP %d)" % status,
                status=status,
                code="REDIRECT",
            )
        try:
            payload = json.loads(
                getattr(response, "text", ""),
                parse_float=Decimal,
                parse_int=int,
            )
        except (json.JSONDecodeError, TypeError) as error:
            raise APIError(
                "Xingchi returned non-JSON data (HTTP %d)" % status,
                status=status,
                code="INVALID_JSON",
            ) from error
        if not isinstance(payload, dict):
            raise APIError(
                "Xingchi JSON top level is not an object (HTTP %d)" % status,
                status=status,
                code="INVALID_RESPONSE",
            )
        return status, payload

    def status(self, account: Account) -> Tuple[int, Any, CheckinStatus]:
        status, payload = self._request(account, "GET")
        return status, payload, parse_status(payload, status)

    def claim(self, account: Account) -> Tuple[int, Any]:
        return self._request(account, "POST")


def claim_amount(payload: Any) -> Optional[Decimal]:
    data = unwrap_data(payload)
    if isinstance(data, dict):
        value = parse_decimal(data.get("amount"))
        if value is not None:
            return value
        nested = data.get("status")
        if isinstance(nested, dict):
            return parse_decimal(nested.get("amount"))
    return None


def run_account(
    index: int,
    account: Account,
    client: XingchiClient,
    query_only: bool = False,
) -> RunResult:
    label = account.label
    try:
        http_status, _, before = client.status(account)
        if not before.enabled:
            return RunResult(
                index=index,
                label=label,
                status="INACTIVE",
                message="站点当前没有开启每日签到活动",
                http_status=http_status,
                amount=before.amount,
                total_count=before.total_count,
                total_amount=before.total_amount,
                next_claim_at=before.next_claim_at,
            )
        if query_only:
            return RunResult(
                index=index,
                label=label,
                status="QUERY",
                message="查询完成；未发送签到请求",
                http_status=http_status,
                amount=before.amount,
                total_count=before.total_count,
                total_amount=before.total_amount,
                next_claim_at=before.next_claim_at,
                detail_lines=[
                    "今日已签：%s" % ("是" if before.claimed_today else "否"),
                    "今日奖励：%s" % (format_decimal(before.amount) or "-"),
                ],
            )
        if before.claimed_today:
            return RunResult(
                index=index,
                label=label,
                status="ALREADY",
                message="今日已签到（服务端状态确认）",
                http_status=http_status,
                amount=before.amount,
                total_count=before.total_count,
                total_amount=before.total_amount,
                next_claim_at=before.next_claim_at,
            )

        claim_status, claim_payload = client.claim(account)
        if is_auth_error(claim_status, claim_payload):
            raise SessionExpired("Xingchi panel login expired")
        claim_code = payload_code(claim_payload).upper()
        claim_message = sanitize_message(payload_message(claim_payload), account)
        if claim_status == 409 or claim_code == "CHECKIN_ALREADY_CLAIMED":
            already = True
        elif not 200 <= claim_status < 300:
            return RunResult(
                index=index,
                label=label,
                status="API_ERROR",
                message=claim_message or "签到请求失败（HTTP %d）" % claim_status,
                http_status=claim_status,
                amount=before.amount,
                total_count=before.total_count,
                total_amount=before.total_amount,
                next_claim_at=before.next_claim_at,
            )
        else:
            already = False

        if client.wait_seconds:
            client.sleeper(client.wait_seconds)
        try:
            read_status, _, after = client.status(account)
        except SessionExpired:
            return RunResult(
                index=index,
                label=label,
                status="AUTH_EXPIRED",
                message="领取请求已发出，但回读时登录态失效，结果未确认",
                http_status=claim_status,
                amount=claim_amount(claim_payload) or before.amount,
            )
        except XingchiError as error:
            return RunResult(
                index=index,
                label=label,
                status="UNCONFIRMED",
                message="领取请求已发出，但服务端状态回读失败：%s"
                % sanitize_message(error, account),
                http_status=claim_status,
                amount=claim_amount(claim_payload) or before.amount,
            )

        if after.claimed_today:
            amount = claim_amount(claim_payload) or after.amount
            return RunResult(
                index=index,
                label=label,
                status="ALREADY" if already else "CLAIMED",
                message=(
                    "今日已签到（服务端回读确认）"
                    if already
                    else "签到成功，服务端已确认今日签到"
                ),
                http_status=read_status,
                amount=amount,
                total_count=after.total_count,
                total_amount=after.total_amount,
                next_claim_at=after.next_claim_at,
            )

        return RunResult(
            index=index,
            label=label,
            status="UNCONFIRMED",
            message="领取请求已返回，但服务端 claimed_today 仍为 false，不能确认到账",
            http_status=read_status,
            amount=claim_amount(claim_payload) or after.amount,
            total_count=after.total_count,
            total_amount=after.total_amount,
            next_claim_at=after.next_claim_at,
        )
    except SessionExpired as error:
        return RunResult(
            index=index,
            label=label,
            status="AUTH_EXPIRED",
            message=sanitize_message(error, account),
        )
    except APIError as error:
        return RunResult(
            index=index,
            label=label,
            status="UNCONFIRMED"
            if error.code in {"INVALID_RESPONSE", "INVALID_JSON"}
            else "API_ERROR",
            message=sanitize_message(error, account),
            http_status=error.status,
        )


def build_summary(results: Sequence[RunResult]) -> Dict[str, Any]:
    counts: Dict[str, int] = {}
    for result in results:
        counts[result.status] = counts.get(result.status, 0) + 1
    return {
        "type": "SUMMARY",
        "provider": PROVIDER,
        "ok": bool(results) and all(result.ok for result in results),
        "accounts": len(results),
        "claimed": counts.get("CLAIMED", 0),
        "already": counts.get("ALREADY", 0),
        "query": counts.get("QUERY", 0),
        "inactive": counts.get("INACTIVE", 0),
        "failed": sum(1 for result in results if not result.ok),
        "status_counts": counts,
    }


def build_report(results: Sequence[RunResult], summary: Dict[str, Any]) -> str:
    lines = [
        "Xingchi Daily",
        "账号：%d；已领取：%d；今日已签：%d；失败：%d"
        % (
            len(results),
            summary["claimed"],
            summary["already"],
            summary["failed"],
        ),
    ]
    for result in results:
        lines.append(
            "%s 账号%d %s：%s"
            % ("✅" if result.ok else "❌", result.index, result.label, result.message)
        )
    return "\n".join(lines)


def _post_notification(url: str, payload: Dict[str, Any]) -> None:
    requests.post(url, json=payload, timeout=10)


def notify_all(title: str, content: str) -> None:
    pushplus = env_text("PUSHPLUS_TOKEN")
    if pushplus:
        try:
            _post_notification(
                "https://www.pushplus.plus/send",
                {
                    "token": pushplus,
                    "title": title,
                    "content": content,
                    "template": "markdown",
                },
            )
        except requests.RequestException:
            pass
    wecom = env_text("WECOM_WEBHOOK")
    if wecom:
        try:
            _post_notification(wecom, {"msgtype": "markdown", "markdown": {"content": content}})
        except requests.RequestException:
            pass
    dingtalk = env_text("DINGTALK_WEBHOOK")
    if dingtalk:
        try:
            _post_notification(
                dingtalk,
                {"msgtype": "markdown", "markdown": {"title": title, "text": content}},
            )
        except requests.RequestException:
            pass
    bark = env_text("BARK_URL")
    if bark:
        try:
            requests.get(bark, params={"title": title, "body": content}, timeout=10)
        except requests.RequestException:
            pass
    generic = env_text("GENERIC_WEBHOOK_URL")
    if generic:
        try:
            _post_notification(generic, {"title": title, "content": content})
        except requests.RequestException:
            pass


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Xingchi daily check-in")
    parser.add_argument("--query", "--status", action="store_true", dest="query", help="read status only")
    parser.add_argument("--only", default="", help="account indexes, e.g. 1,3-4")
    parser.add_argument("--accounts-file", default="", help="account file path")
    parser.add_argument("--api-base", default="", help="override API base URL")
    parser.add_argument("--wait-seconds", type=float, default=None, help="wait before status readback")
    parser.add_argument("--no-notify", action="store_true", help="disable notifications")
    parser.add_argument("--version", action="version", version=VERSION)
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        accounts = load_accounts(args.accounts_file or None)
        selected = parse_only(args.only, len(accounts))
    except ConfigError as error:
        emit(
            {
                "type": "SUMMARY",
                "provider": PROVIDER,
                "ok": False,
                "accounts": 0,
                "error": sanitize_message(error),
            }
        )
        return 2

    wait_seconds = (
        DEFAULT_WAIT_SECONDS
        if args.wait_seconds is None
        else max(0.0, float(args.wait_seconds))
    )
    if args.wait_seconds is None and env_text(WAIT_ENV):
        try:
            wait_seconds = max(0.0, float(env_text(WAIT_ENV)))
        except ValueError:
            pass

    client = XingchiClient(
        api_base=args.api_base or env_text(API_BASE_ENV, API_BASE),
        wait_seconds=wait_seconds,
        proxy=env_text(PROXY_ENV),
    )
    results: List[RunResult] = []
    for index, account in enumerate(accounts, 1):
        if index not in selected:
            continue
        result = run_account(index, account, client, query_only=args.query)
        results.append(result)
        emit(result.as_dict())

    summary = build_summary(results)
    emit(summary)
    if not args.no_notify:
        notify_all("Xingchi Daily", build_report(results, summary))
    return 0 if summary["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

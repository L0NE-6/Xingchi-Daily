import importlib.util
import json
import sys
import unittest
from decimal import Decimal
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("xingchi_daily", ROOT / "xingchi_daily.py")
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


class FakeResponse:
    def __init__(self, payload, status=200, text=None):
        self.status_code = status
        self.text = text if text is not None else json.dumps(payload)


class FakeSession:
    def __init__(self, response):
        self.response = response
        self.headers = {}
        self.proxies = {}
        self.calls = []
        self.closed = False

    def request(self, method, url, **kwargs):
        self.calls.append((method, url, kwargs))
        return self.response

    def close(self):
        self.closed = True


class FakeTransport:
    def __init__(self, *responses):
        self.responses = list(responses)
        self.sessions = []

    def __call__(self):
        if not self.responses:
            raise AssertionError("unexpected HTTP request")
        session = FakeSession(self.responses.pop(0))
        self.sessions.append(session)
        return session


class AccountParsingTests(unittest.TestCase):
    def test_plain_accounts_and_duplicate_removal(self):
        accounts = MODULE.parse_accounts("主号|panel-one\n副号|panel-two\n重复|panel-one")
        self.assertEqual([item.name for item in accounts], ["主号", "副号"])
        self.assertEqual([item.token for item in accounts], ["panel-one", "panel-two"])

    def test_json_accounts(self):
        accounts = MODULE.parse_accounts(
            json.dumps([{"name": "json", "panelToken": "panel-json"}])
        )
        self.assertEqual(accounts[0].name, "json")
        self.assertEqual(accounts[0].token, "panel-json")

    def test_only_ranges(self):
        self.assertEqual(MODULE.parse_only("1,3-4", 5), {1, 3, 4})


class FlowTests(unittest.TestCase):
    def account(self):
        return MODULE.Account("测试", "panel-secret")

    def client(self, *responses):
        transport = FakeTransport(*responses)
        client = MODULE.XingchiClient(
            api_base="https://xingchi.example",
            wait_seconds=0,
            session_factory=transport,
        )
        return client, transport

    def test_query_only_never_posts(self):
        client, transport = self.client(
            FakeResponse(
                {
                    "code": 0,
                    "data": {
                        "enabled": True,
                        "claimed_today": False,
                        "amount": 300,
                    },
                }
            )
        )
        result = MODULE.run_account(1, self.account(), client, query_only=True)
        self.assertEqual(result.status, "QUERY")
        self.assertEqual(len(transport.sessions), 1)
        self.assertEqual(transport.sessions[0].calls[0][0], "GET")

    def test_claim_requires_post_claim_readback(self):
        client, transport = self.client(
            FakeResponse(
                {
                    "data": {
                        "enabled": True,
                        "claimed_today": False,
                        "amount": 300,
                        "total_count": 2,
                    }
                }
            ),
            FakeResponse({"code": 0, "data": {"amount": 300}}),
            FakeResponse(
                {
                    "data": {
                        "enabled": True,
                        "claimed_today": True,
                        "amount": 300,
                        "total_count": 3,
                        "next_claim_at": "2026-11-25T00:00:00+08:00",
                    }
                }
            ),
        )
        result = MODULE.run_account(1, self.account(), client)
        self.assertEqual(result.status, "CLAIMED")
        self.assertEqual(result.amount, Decimal("300"))
        self.assertEqual(result.total_count, Decimal("3"))
        self.assertEqual(
            [session.calls[0][0] for session in transport.sessions],
            ["GET", "POST", "GET"],
        )
        post_kwargs = transport.sessions[1].calls[0][2]
        self.assertNotIn("json", post_kwargs)
        self.assertNotIn("data", post_kwargs)

    def test_claim_without_readback_confirmation_is_unconfirmed(self):
        client, _ = self.client(
            FakeResponse(
                {"data": {"enabled": True, "claimed_today": False, "amount": 300}}
            ),
            FakeResponse({"code": 0, "data": {"amount": 300}}),
            FakeResponse(
                {"data": {"enabled": True, "claimed_today": False, "amount": 300}}
            ),
        )
        result = MODULE.run_account(1, self.account(), client)
        self.assertEqual(result.status, "UNCONFIRMED")
        self.assertIn("claimed_today", result.message)

    def test_already_checked_in_skips_post(self):
        client, transport = self.client(
            FakeResponse(
                {
                    "data": {
                        "enabled": True,
                        "claimed_today": True,
                        "amount": 300,
                    }
                }
            )
        )
        result = MODULE.run_account(1, self.account(), client)
        self.assertEqual(result.status, "ALREADY")
        self.assertEqual(len(transport.sessions), 1)

    def test_inactive_site_is_neutral(self):
        client, _ = self.client(
            FakeResponse(
                {"data": {"enabled": False, "claimed_today": False, "amount": 0}}
            )
        )
        result = MODULE.run_account(1, self.account(), client)
        self.assertEqual(result.status, "INACTIVE")
        self.assertTrue(result.ok)

    def test_auth_error_is_visible(self):
        client, _ = self.client(FakeResponse({}, status=401))
        result = MODULE.run_account(1, self.account(), client)
        self.assertEqual(result.status, "AUTH_EXPIRED")
        self.assertFalse(result.ok)

    def test_duplicate_claim_then_readback_is_already(self):
        client, _ = self.client(
            FakeResponse(
                {"data": {"enabled": True, "claimed_today": False, "amount": 300}}
            ),
            FakeResponse(
                {"code": 409, "reason": "CHECKIN_ALREADY_CLAIMED"},
                status=409,
            ),
            FakeResponse(
                {"data": {"enabled": True, "claimed_today": True, "amount": 300}}
            ),
        )
        result = MODULE.run_account(1, self.account(), client)
        self.assertEqual(result.status, "ALREADY")

    def test_malformed_status_is_failure(self):
        client, _ = self.client(FakeResponse({"data": {"enabled": True}}))
        result = MODULE.run_account(1, self.account(), client)
        self.assertEqual(result.status, "UNCONFIRMED")
        self.assertFalse(result.ok)


if __name__ == "__main__":
    unittest.main()

"""Thin HTTP client for the Sumry API.

Sumry only accepts a JWT, and the only way to mint one is POST /api/users/login.
Tokens live 30 days, so rather than store one and let it rot, this logs in with
the credentials from the environment and caches the token in memory for the
lifetime of the process, re-authenticating whenever the API answers 401.
"""

from __future__ import annotations

import json
import os
import threading
import urllib.error
import urllib.parse
import urllib.request

DEFAULT_BASE_URL = "https://sumry-api.elyesghazel.ch"
TIMEOUT_SECONDS = 20

# Cloudflare fronts the API and bans urllib's default signature outright
# (error 1010), so identify honestly rather than going out as Python-urllib.
USER_AGENT = "sumry-mcp/1.0 (+https://sumry.elyesghazel.ch)"


class SumryError(RuntimeError):
    """An API call failed in a way worth showing the user verbatim."""


class SumryClient:
    def __init__(
        self,
        base_url: str | None = None,
        email: str | None = None,
        password: str | None = None,
        token: str | None = None,
    ) -> None:
        self.base_url = (base_url or os.environ.get("SUMRY_API_URL") or DEFAULT_BASE_URL).rstrip("/")
        self.email = email or os.environ.get("SUMRY_EMAIL")
        self.password = password or os.environ.get("SUMRY_PASSWORD")
        # A pre-minted token is honoured, but then there is nothing to refresh
        # with, so a 401 becomes a hard error instead of a silent re-login.
        self._token = token or os.environ.get("SUMRY_TOKEN")
        self._token_is_static = bool(self._token)
        self._lock = threading.Lock()

    # ------------------------------------------------------------------ auth

    def _login(self) -> str:
        if not self.email or not self.password:
            raise SumryError(
                "No Sumry credentials. Set SUMRY_EMAIL and SUMRY_PASSWORD "
                "(see ~/.claude/secrets.fish.example), then re-run "
                "`fish ~/.claude/bin/mcp-bootstrap.fish`."
            )
        body = self._raw_request(
            "POST",
            "/api/users/login",
            payload={"email": self.email, "password": self.password},
            token=None,
        )
        token = (body or {}).get("token")
        if not token:
            raise SumryError("Login succeeded but returned no token.")
        return token

    def _ensure_token(self) -> str:
        with self._lock:
            if not self._token:
                self._token = self._login()
            return self._token

    # --------------------------------------------------------------- request

    def _raw_request(self, method: str, path: str, payload=None, token: str | None = None):
        url = f"{self.base_url}{path}"
        data = None
        headers = {"Accept": "application/json", "User-Agent": USER_AGENT}
        if payload is not None:
            data = json.dumps(payload).encode("utf-8")
            headers["Content-Type"] = "application/json"
        if token:
            headers["Authorization"] = f"Bearer {token}"

        req = urllib.request.Request(url, data=data, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=TIMEOUT_SECONDS) as resp:
                raw = resp.read()
                if resp.status == 204 or not raw:
                    return None
                return json.loads(raw.decode("utf-8"))
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", "replace").strip()
            raise _HttpFailure(exc.code, detail or exc.reason) from None
        except urllib.error.URLError as exc:
            raise SumryError(f"Cannot reach Sumry at {self.base_url}: {exc.reason}") from None

    def request(self, method: str, path: str, payload=None, params: dict | None = None):
        if params:
            path = f"{path}?{urllib.parse.urlencode(params)}"

        try:
            return self._raw_request(method, path, payload, self._ensure_token())
        except _HttpFailure as exc:
            # A 401 on a token we minted ourselves means it expired; one retry
            # with a fresh login is enough, and a second 401 is a real problem.
            if exc.status == 401 and not self._token_is_static:
                with self._lock:
                    self._token = None
                try:
                    return self._raw_request(method, path, payload, self._ensure_token())
                except _HttpFailure as retry_exc:
                    raise SumryError(_describe(retry_exc)) from None
            raise SumryError(_describe(exc)) from None

    # ------------------------------------------------------------- shortcuts

    def get(self, path, params=None):
        return self.request("GET", path, params=params)

    def post(self, path, payload=None):
        return self.request("POST", path, payload=payload)

    def put(self, path, payload=None):
        return self.request("PUT", path, payload=payload)

    def delete(self, path):
        return self.request("DELETE", path)


class _HttpFailure(Exception):
    def __init__(self, status: int, detail: str) -> None:
        super().__init__(detail)
        self.status = status
        self.detail = detail


def _describe(exc: _HttpFailure) -> str:
    # A 403 is ambiguous: Spring sends one for another user's record, but so does
    # the Cloudflare in front of it when it dislikes the request. Say which.
    if exc.status == 403 and "cloudflare" in exc.detail.lower():
        hint = "Cloudflare blocked the request before it reached Sumry (403)."
    else:
        hint = {
            401: "Sumry rejected the credentials (401).",
            403: "That record belongs to another user (403).",
            404: "Not found (404) — check the account id or category label.",
        }.get(exc.status, f"Sumry returned HTTP {exc.status}.")
    # Spring's error body is JSON with a "message"; fall back to the raw text.
    try:
        parsed = json.loads(exc.detail)
        message = parsed.get("message") or parsed.get("error") or exc.detail
    except (ValueError, AttributeError):
        message = exc.detail
    return f"{hint} {message}".strip()

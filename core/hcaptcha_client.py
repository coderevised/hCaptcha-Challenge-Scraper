from __future__ import annotations
import json
import random
import re
import time
import urllib.parse
from typing import Any, Optional
import requests

from .http_client import HttpClient


class HcaptchaClient:
    DEFAULT_USER_AGENT = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/147.0.0.0 Safari/537.36"
    )

    def __init__(
        self,
        *,
        proxy: Optional[str] = None,
        timeout: float = 30.0,
        user_agent: Optional[str] = None,
        headers: Optional[dict[str, str]] = None,
    ) -> None:
        self._http = HttpClient(
            proxy=proxy,
            timeout=timeout,
            headers={
                "Accept": "application/json, application/octet-stream",
                "Accept-Language": "en-US,en;q=0.9",
                "Content-Type": "application/x-www-form-urlencoded",
                "User-Agent": user_agent or self.DEFAULT_USER_AGENT,
                **(headers or {}),
            },
        )
        self.user_agent = user_agent or self.DEFAULT_USER_AGENT

        with open("./fingerprint.json", "r", encoding="utf-8") as f:
            self.fp = json.load(f)

    def get(self, url: str, *, headers: Optional[dict[str, str]] = None) -> requests.Response:
        return self._http.get(url, headers=headers)

    def post(
        self,
        url: str,
        *,
        data: Optional[Any] = None,
        json_data: Optional[dict] = None,
        headers: Optional[dict[str, str]] = None,
    ) -> requests.Response:
        return self._http.post(url, data=data, json_data=json_data, headers=headers)

    def _get_pem(self, host: str = "api.hcaptcha.com") -> dict:
        csc = random.uniform(20.0, 85.0)
        return {
            "csc": round(csc, 15),
            "csch": host,
            "cscrt": 0,
            "cscft": round(csc, 15),
        }

    def get_version(self, referer: str = "https://example.com/") -> str:
        url = "https://js.hcaptcha.com/1/api.js?onload=CaptchaLoaded&render=explicit"
        resp = self.get(
            url,
            headers={
                "Accept": "*/*",
                "Sec-Fetch-Dest": "script",
                "Sec-Fetch-Mode": "no-cors",
                "Sec-Fetch-Site": "cross-site",
                "Referer": referer,
            },
        )
        matches = re.findall(r'v1/([a-f0-9]+)/static', resp.text)
        if matches:
            return matches[0]
        raise RuntimeError("version_fetch_failed: asset version not found in api.js")

    def get_site_config(self, v: str, host: str, sitekey: str) -> dict[str, Any]:
        headers = {
            "Accept": "application/json",
            "Content-Type": "text/plain",
            "Origin": "https://newassets.hcaptcha.com",
            "Referer": "https://newassets.hcaptcha.com/",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-site",
        }
        resp = self.post(
            url=(
                f"https://api.hcaptcha.com/checksiteconfig"
                f"?v={v}&host={host}&sitekey={sitekey}&sc=1&swa=1&spst=1"
            ),
            headers=headers,
        )
        if resp.status_code != 200:
            raise Exception(f"checksiteconfig failed: {resp.status_code} {resp.text[:200]}")
        data = resp.json()
        try:
            return data["c"]
        except (KeyError, TypeError):
            raise RuntimeError("checksiteconfig response missing 'c' field")

    def get_hsl(
        self,
        version: str,
        sitekey: str,
        url: str,
        site_config: dict[str, Any],
    ) -> requests.Response:
        parsed = urllib.parse.urlparse(url)
        host = parsed.netloc or parsed.path.split("/")[0]
        hcapurl = f"https://api.hcaptcha.com/getcaptcha/{sitekey}"

        from .motion import getcaptcha

        now = int(time.time() * 1000)
        pdc = {
            "s": now,
            "n": 0,
            "bfp": 1,
            "bfc": 1,
            "big": 0,
            "p": 0,
            "gcs": 1,
        }
        pem = self._get_pem(host="api.hcaptcha.com")
        client_options = {
            "sentry": True,
            "reportapi": "https://accounts.hcaptcha.com",
            "recaptchacompat": "true",
            "custom": False,
            "hl": "en",
            "tplinks": "on",
            "andint": "off",
            "pat": "on",
            "pstissuer": "https://pst-issuer.hcaptcha.com",
            "endpoint": "https://api.hcaptcha.com",
            "theme": "light",
            "size": "normal",
            "confirm-nav": False,
        }

        payload1 = {
            "v": version,
            "sitekey": sitekey,
            "host": host,
            "hl": "en",
            "motionData": getcaptcha(fingerprint=self.fp, href=url),
            "pdc": json.dumps(pdc),
            "pem": json.dumps(pem),
            "n": "fail",
            "e": "asset-error",
            "c": json.dumps(site_config),
            "clientOptions": json.dumps(client_options),
        }

        resp1 = self.post(hcapurl, data=urllib.parse.urlencode(payload1))
        data1 = resp1.json()

        if "c" not in data1 or "req" not in data1["c"]:
            return resp1

        hsj_req = data1["c"]["req"]

        pdc["s"] = int(time.time() * 1000)
        pem = self._get_pem(host="api.hcaptcha.com")
        payload2 = {
            "v": version,
            "sitekey": sitekey,
            "host": host,
            "hl": "en",
            "motionData": getcaptcha(fingerprint=self.fp, href=url),
            "pdc": json.dumps(pdc),
            "pem": json.dumps(pem),
            "n": "fail",
            "e": "asset-error",
            "c": json.dumps({"type": "hsj", "req": hsj_req}),
            "clientOptions": json.dumps(client_options),
        }

        resp2 = self.post(hcapurl, data=urllib.parse.urlencode(payload2))
        return resp2

    def get_challenge(
        self,
        version: str,
        sitekey: str,
        url: str,
        n: str,
        site_config: dict[str, Any],
    ) -> requests.Response:
        parsed = urllib.parse.urlparse(url)
        host = parsed.netloc or parsed.path.split("/")[0]
        hcapurl = f"https://api2.hcaptcha.com/getcaptcha/{sitekey}"

        from .motion import getcaptcha

        now = int(time.time() * 1000)
        pdc = {
            "s": now,
            "n": 0,
            "bfp": 1,
            "bfc": 1,
            "big": 0,
            "p": 0,
            "gcs": 1,
        }
        pem = self._get_pem(host="api2.hcaptcha.com")
        client_options = {
            "sentry": True,
            "reportapi": "https://accounts.hcaptcha.com",
            "recaptchacompat": "true",
            "custom": False,
            "hl": "en",
            "tplinks": "on",
            "andint": "off",
            "pat": "on",
            "pstissuer": "https://pst-issuer.hcaptcha.com",
            "endpoint": "https://api2.hcaptcha.com",
            "theme": "light",
            "size": "normal",
            "confirm-nav": False,
        }

        payload = {
            "v": version,
            "sitekey": sitekey,
            "host": host,
            "hl": "en",
            "motionData": getcaptcha(fingerprint=self.fp, href=url),
            "pdc": json.dumps(pdc),
            "pem": json.dumps(pem),
            "n": n,
            "c": json.dumps(site_config),
            "clientOptions": json.dumps(client_options),
        }

        return self.post(
            hcapurl,
            data=urllib.parse.urlencode(payload),
            headers={"Accept": "application/json"},
        )

    @property
    def session(self):
        return self._http.session

    def set_cf_bm(self, value: str, *, url: Optional[str] = None) -> None:
        if url:
            domain = urllib.parse.urlparse(url).netloc
            self._http.session.cookies.set("__cf_bm", value, domain=domain)
        else:
            self._http.session.cookies.set("__cf_bm", value)

    def set_hmt_id(self, value: str, *, url: Optional[str] = "https://hcaptcha.com") -> None:
        domain = urllib.parse.urlparse(url).netloc
        self._http.session.cookies.set("hmt_id", value, domain=domain)

    def set_cflb(self, value: str, *, url: Optional[str] = None) -> None:
        if url:
            domain = urllib.parse.urlparse(url).netloc
            self._http.session.cookies.set("__cflb", value, domain=domain)
        else:
            self._http.session.cookies.set("__cflb", value)
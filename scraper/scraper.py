import time
from contextlib import contextmanager
from pathlib import Path
from urllib.parse import urlparse
import requests

from core.hcaptcha_client import HcaptchaClient
from core.hsl_solver import solve_hsl_local
from core.saver import save_challenge
from core.telemetry import HcaptchaTelemetry

from .logger import get_logger
from .config import ScraperConfig, CHALLENGES_DIR, DEFAULT_RETRY_DELAY


@contextmanager
def timer(callback):
    start = time.perf_counter()
    yield
    callback((time.perf_counter() - start) * 1000)

class HCaptchaChallengeScraper:
    def __init__(self, config: ScraperConfig) -> None:
        self.config = config
        self._telemetry = HcaptchaTelemetry()
        self._client: HcaptchaClient | None = None
        self._session: requests.Session | None = None
        self._site_config: dict | None = None
        self._version: str | None = None
        self._host: str | None = None
        self.log = get_logger("Collector")

    def _initialize_client(self) -> None:
        session_log = get_logger("Session")
        parsed = urlparse(self.config.url)
        self._host = parsed.netloc
        referer = f"{parsed.scheme or 'https'}://{self._host}/"
        session_log.info("Creating hCaptcha session...")
        self._client = HcaptchaClient(proxy=self.config.proxy)
        self._session = self._client.session
        session_log.ok("Session established")
        print()

        self._version = self._client.get_version(referer=referer)

        start = time.perf_counter()
        self._site_config = self._client.get_site_config(
            v=self._version,
            host=self._host,
            sitekey=self.config.sitekey,
        )
        self._telemetry.record_checksiteconfig((time.perf_counter() - start) * 1000)

    def _solve_hsl(self) -> tuple[str, dict]:
        solver_log = get_logger("Solver")
        try:
            hsl_resp = self._client.get_hsl(
                version=self._version,
                sitekey=self.config.sitekey,
                url=self.config.url,
                site_config=self._site_config,
            )
            hsl_resp.raise_for_status()
            hsl_data = hsl_resp.json()
        except requests.RequestException:
            solver_log.error("Failed to fetch HSL data")
            raise

        jwt = hsl_data["c"]["req"]
        start = time.perf_counter()
        try:
            proof = solve_hsl_local(jwt)
            elapsed = (time.perf_counter() - start) * 1000
            solver_log.ok("HSL solved in %.0f ms", elapsed)
        except Exception:
            solver_log.error("Failed to solve HSL")
            raise
        return proof, hsl_data["c"]

    def _fetch_challenge(self, proof: str, hsl_config: dict) -> dict:
        with timer(self._telemetry.record_getcaptcha):
            challenge_resp = self._client.get_challenge(
                version=self._version,
                sitekey=self.config.sitekey,
                url=self.config.url,
                n=proof,
                site_config=hsl_config,
            )
        challenge_resp.raise_for_status()
        return challenge_resp.json()

    def _get_expected_media_count(self, challenge: dict) -> int:
        media_paths = [
            ("media",),
            ("task", "media"),
            ("task", "data", "media"),
            ("images",),
            ("task", "images"),
            ("assets",),
            ("files",),
        ]
        for path in media_paths:
            obj = challenge
            for key in path:
                if isinstance(obj, dict) and key in obj:
                    obj = obj[key]
                else:
                    obj = None
                    break
            if isinstance(obj, list):
                if obj and isinstance(obj[0], dict) and any(k in obj[0] for k in ("url", "data", "src", "path", "name", "type")):
                    return len(obj)
                if path[-1].lower() in ("media", "images", "assets", "files"):
                    return len(obj)

        def find_media_list(obj):
            if isinstance(obj, dict):
                for key, value in obj.items():
                    if isinstance(value, list) and value:
                        if isinstance(value[0], dict) and any(k in value[0] for k in ("url", "data", "src", "path", "name", "type")):
                            return value
                        if key.lower() in ("media", "images", "assets", "files", "media_files"):
                            return value
                    result = find_media_list(value)
                    if result is not None:
                        return result
            elif isinstance(obj, list):
                for item in obj:
                    result = find_media_list(item)
                    if result is not None:
                        return result
            return None

        media_list = find_media_list(challenge)
        return len(media_list) if media_list else 0

    def _count_saved_files(self, folder_path) -> int:
        folder = Path(folder_path)
        if not folder.exists():
            return 0
        return sum(1 for _ in folder.rglob("*") if _.is_file())

    def _save_challenge(self, challenge: dict) -> tuple[Path, int]:
        folder, idx = save_challenge(challenge, self._session)
        return folder, idx

    def _print_summary(self, collected: dict[str, int]) -> None:
        total = sum(collected.values())
        summary_log = get_logger("Summary")
        summary_log.info("Finished — %d challenges saved to ./%s", total, CHALLENGES_DIR)
        for rtype, count in sorted(collected.items()):
            summary_log.info("  • %s: %d", rtype, count)

    def scrape(self) -> dict[str, int]:
        self._initialize_client()
        collected: dict[str, int] = {}
        for attempt in range(self.config.max_challenges):
            self.log.info("Fetching challenge %02d/%d", attempt + 1, self.config.max_challenges)
            try:
                proof, hsl_config = self._solve_hsl()
                challenge = self._fetch_challenge(proof, hsl_config)
                folder, idx = self._save_challenge(challenge)
                expected_media = self._get_expected_media_count(challenge)
                actual_files = self._count_saved_files(folder)
                if expected_media > 0 and actual_files == 0:
                    storage_log = get_logger("Storage")
                    storage_log.warning("No media files saved for challenge_%s (expected %d)", idx, expected_media)
                    print()
                    continue

                req_type = challenge.get("request_type", "unknown")
                collected[req_type] = collected.get(req_type, 0) + 1

                file_count = actual_files
                storage_log = get_logger("Storage")
                if expected_media > 0 and actual_files < expected_media:
                    storage_log.save("Saved challenge_%s (%s • %d/%d files)", idx, req_type, actual_files, expected_media)
                else:
                    storage_log.save("Saved challenge_%s (%s • %d files)", idx, req_type, file_count)
                print()

                if self.config.delay_sec:
                    time.sleep(self.config.delay_sec)

            except requests.RequestException as exc:
                network_log = get_logger("Network")
                network_log.warning("SKIP: %s", exc)
                print()
                continue

            except Exception as exc:
                storage_log = get_logger("Storage")
                storage_log.error("Failed to save challenge: %s", exc)
                print()
                time.sleep(DEFAULT_RETRY_DELAY)
                continue

        self._print_summary(collected)
        return collected
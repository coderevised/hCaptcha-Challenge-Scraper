import json
import logging
import re
import base64
import concurrent.futures
from urllib.parse import urlparse
from pathlib import Path
import requests

logger = logging.getLogger(__name__)
CHALLENGES_DIR = Path("challenges")

def _get_extension_from_content_type(content_type: str) -> str:
    ct = content_type.lower()
    if "png" in ct:
        return "png"
    elif "jpeg" in ct or "jpg" in ct:
        return "jpg"
    elif "gif" in ct:
        return "gif"
    elif "webp" in ct:
        return "webp"
    elif "mp4" in ct:
        return "mp4"
    elif "webm" in ct:
        return "webm"
    return None


def _copy_hcaptcha_cookies(session: requests.Session, target_domain: str):
    for cookie in session.cookies:
        if cookie.domain and "hcaptcha.com" in cookie.domain:
            try:
                session.cookies.set(
                    cookie.name,
                    cookie.value,
                    domain=target_domain,
                    path=cookie.path or "/",
                )
            except Exception:
                pass

def _make_thread_session(base_session: requests.Session, target_domain: str) -> requests.Session:
    s = requests.Session()
    s.headers.update(base_session.headers)
    s.proxies = base_session.proxies
    for cookie in base_session.cookies:
        if cookie.domain and "hcaptcha.com" in cookie.domain:
            try:
                s.cookies.set(cookie.name, cookie.value, domain=target_domain, path=cookie.path or "/")
            except Exception:
                pass
    return s


def _download_media(session: requests.Session, url: str, filepath: Path) -> bool:
    url_path = urlparse(url).path
    url_ext = Path(url_path).suffix.lower().lstrip('.')
    if url_ext in ("png", "jpg", "jpeg", "gif", "webp", "mp4", "webm"):
        ext = url_ext
    else:
        ext = "webm"

    target_domain = urlparse(url).netloc
    _copy_hcaptcha_cookies(session, target_domain)

    if ext in ("mp4", "webm"):
        accept_header = "video/webm, video/mp4, video/*;q=0.8"
    else:
        accept_header = "image/png, image/jpeg, image/webp, image/*;q=0.8"

    headers = {
        "Accept": accept_header,
        "Referer": "https://newassets.hcaptcha.com/",
    }

    try:
        resp = session.get(url, timeout=15, headers=headers)
        resp.raise_for_status()

        content_type = resp.headers.get("content-type", "").lower()
        ct_ext = _get_extension_from_content_type(content_type)
        if ct_ext:
            ext = ct_ext

        final_path = filepath if filepath.suffix.lower() == f".{ext}" else filepath.with_suffix(f".{ext}")
        with open(final_path, "wb") as f:
            f.write(resp.content)
        return True

    except requests.HTTPError as e:
        if e.response.status_code == 403:
            candidates = []
            if not url.endswith(".webm"):
                candidates.append(url + ".webm")
            if not url.endswith(".mp4"):
                candidates.append(url + ".mp4")

            for candidate_url in candidates:
                try:
                    resp = session.get(candidate_url, timeout=15, headers={
                        "Accept": "video/webm, video/mp4, video/*;q=0.8",
                        "Referer": "https://newassets.hcaptcha.com/",
                    })
                    resp.raise_for_status()
                    candidate_ext = ".webm" if candidate_url.endswith(".webm") else ".mp4"
                    final_path = filepath.with_suffix(candidate_ext)
                    with open(final_path, "wb") as f:
                        f.write(resp.content)
                    logger.info("Recovered as %s: %s", candidate_ext, final_path.name)
                    return True
                except Exception:
                    continue

        logger.warning("Failed to download %s: HTTP %s", url, e.response.status_code)
        return False
    except Exception as e:
        logger.warning("Failed to download %s: %s", url, e)
        return False

def _download_media_worker(base_session: requests.Session, url: str, filepath: Path) -> bool:
    target_domain = urlparse(url).netloc
    s = _make_thread_session(base_session, target_domain)
    return _download_media(s, url, filepath)

def _get_next_index(type_folder: Path) -> int:
    if not type_folder.exists():
        return 0
    max_idx = -1
    pattern = re.compile(r"^challenge_(\d+)$")
    for entry in type_folder.iterdir():
        if entry.is_dir():
            m = pattern.match(entry.name)
            if m:
                max_idx = max(max_idx, int(m.group(1)))
    return max_idx + 1

def _find_existing_type_folder(base_dir: Path, request_type: str) -> Path:
    standard = base_dir / request_type.replace("_", " ")
    if standard.exists():
        return standard
    old = base_dir / request_type
    if old.exists():
        return old
    return standard

def save_challenge(challenge: dict, session: requests.Session, base_dir: Path = CHALLENGES_DIR) -> tuple[Path, int]:
    request_type = challenge.get("request_type", "unknown")

    folder_map = {
        "image_label_binary": "image label binary",
        "image_label_area_select": "image label area select",
        "image_drag_drop": "image drag drop",
    }
    folder_name = folder_map.get(request_type, request_type.replace("_", " "))

    type_folder = _find_existing_type_folder(base_dir, request_type)
    type_folder.mkdir(parents=True, exist_ok=True)

    # Extract requester_question text
    req_question = challenge.get("requester_question")
    question_text = ""
    if isinstance(req_question, dict):
        question_text = req_question.get("en") or next((val for val in req_question.values() if isinstance(val, str)), "")
    elif isinstance(req_question, str):
        question_text = req_question

    # Sanitize the question text for a directory name
    sanitized_text = re.sub(r'[\\/*?:"<>|]', '', question_text).strip()
    if not sanitized_text:
        sanitized_text = "unknown_question"
    else:
        sanitized_text = sanitized_text[:120].strip()

    target_folder = type_folder / sanitized_text
    target_folder.mkdir(parents=True, exist_ok=True)

    index = _get_next_index(target_folder)
    challenge_dir = target_folder / f"challenge_{index}"
    challenge_dir.mkdir(parents=True, exist_ok=True)

    with open(challenge_dir / "challenge.json", "w", encoding="utf-8") as f:
        json.dump(challenge, f, indent=2, ensure_ascii=False)

    download_tasks: list[tuple[str, Path]] = []

    example_url = challenge.get("requester_question_example")
    if example_url and isinstance(example_url, str) and example_url.startswith("http"):
        download_tasks.append((example_url, challenge_dir / "example"))

    tasklist = challenge.get("tasklist", [])
    for i, task in enumerate(tasklist):
        if not isinstance(task, dict):
            continue

        img_data = None
        for key in ("datapoint_uri", "image", "image_url", "url", "src", "data"):
            if key in task and task[key]:
                img_data = task[key]
                break

        if img_data and isinstance(img_data, str):
            filename_base = task.get("task_key") or task.get("uuid") or f"img_{i}"
            filename_base = re.sub(r'[^\w\-_]', '_', str(filename_base))

            if img_data.startswith("data:image"):
                try:
                    header, b64 = img_data.split(",", 1)
                    ext = header.split(";")[0].split("/")[-1]
                    if ext not in ("png", "jpg", "jpeg", "gif", "webp"):
                        ext = "png"
                    filepath = challenge_dir / f"{filename_base}.{ext}"
                    with open(filepath, "wb") as f:
                        f.write(base64.b64decode(b64))
                except Exception as e:
                    logger.warning("Base64 decode failed for %s: %s", filename_base, e)

            elif img_data.startswith("http"):
                filepath = challenge_dir / filename_base
                download_tasks.append((img_data, filepath))

            elif len(img_data) > 200:
                try:
                    filepath = challenge_dir / f"{filename_base}.png"
                    with open(filepath, "wb") as f:
                        f.write(base64.b64decode(img_data))
                except Exception:
                    pass

        entities = task.get("entities", [])
        for entity in entities:
            if not isinstance(entity, dict):
                continue
            entity_uri = entity.get("entity_uri")
            entity_id = entity.get("entity_id")
            if not entity_uri or not entity_id:
                continue
            if isinstance(entity_uri, str) and entity_uri.startswith("http"):
                safe_id = re.sub(r'[^\w\-_]', '_', str(entity_id))
                download_tasks.append((entity_uri, challenge_dir / safe_id))

    images_saved = 0

    if download_tasks:
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
            future_to_task = {
                executor.submit(_download_media_worker, session, url, filepath): (url, filepath)
                for url, filepath in download_tasks
            }
            for future in concurrent.futures.as_completed(future_to_task):
                url, filepath = future_to_task[future]
                try:
                    success = future.result()
                    if success:
                        images_saved += 1
                except Exception as e:
                    logger.warning("Download error for %s: %s", url, e)

    for field in ("requester_question", "question", "target"):
        val = challenge.get(field)
        if not isinstance(val, dict):
            continue
        for subkey, subval in val.items():
            if isinstance(subval, str) and subval.startswith("data:image"):
                try:
                    header, b64 = subval.split(",", 1)
                    ext = header.split(";")[0].split("/")[-1]
                    if ext not in ("png", "jpg", "jpeg", "gif", "webp"):
                        ext = "png"
                    filename = f"{field}_{subkey}".replace("/", "_")
                    filepath = challenge_dir / f"{filename}.{ext}"
                    with open(filepath, "wb") as f:
                        f.write(base64.b64decode(b64))
                    images_saved += 1
                except Exception:
                    pass

    return challenge_dir, index

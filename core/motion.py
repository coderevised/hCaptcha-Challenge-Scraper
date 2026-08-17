import base64
import json
import os
import random
import re
import time
import uuid
from typing import List, Tuple, Dict, Any, Optional, Sequence
import numpy as np
import urllib.request

from .cursorflow import (
    ScreenConfig,
    MovementStyle,
    Trajectory,
    generate,
    merge,
    deduplicate,
)

_DEFAULT_SITE_INFO: Dict[str, Any] = {}

def load_site_info(path: str = "site_info.json") -> Dict[str, Any]:
    
    global _DEFAULT_SITE_INFO
    if not os.path.isfile(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        return {}
    _DEFAULT_SITE_INFO = data
    return data

def get_site_config(href: str, site_info: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    
    if site_info is None:
        site_info = _DEFAULT_SITE_INFO
    if not site_info:
        return {}

    if href in site_info:
        return site_info[href].get("widget", {})
    for key, val in site_info.items():
        if key in href or href in key:
            return val.get("widget", {})
    return {}

def _generate_imd() -> str:
    chars = "0123456789abcdef"
    random_id = "".join(random.choice(chars) for _ in range(12))
    url = f"https://{random_id}.w.hcaptcha.com/logo.png"
    
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36",
            "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
            "Referer": "https://newassets.hcaptcha.com/",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return base64.b64encode(resp.read()).decode("utf-8")
    except Exception:
        return base64.b64encode(url.encode("utf-8")).decode("utf-8")


def _generate_widget_id(length: int = 12) -> str:
    chars = "abcdefghijklmnopqrstuvwxyz0123456789"
    return "".join(random.choice(chars) for _ in range(length))


def _parse_fingerprint(fp: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    if not fp:
        return {}

    comp = fp.get("components", {})
    nav_comp = comp.get("navigator", {})
    screen_comp = comp.get("screen", {})

    ua = nav_comp.get("user_agent", "")
    chrome_match = re.search(r"Chrome/(\d+)", ua)
    chrome_ver = chrome_match.group(1) if chrome_match else "150"

    hw_concurrency = 8
    device_memory = 8
    languages = nav_comp.get("languages", ["en-US"])
    language = nav_comp.get("language", "en-US")
    platform = nav_comp.get("platform", "Win32")
    max_touch = nav_comp.get("max_touch_points", 0)
    webdriver = nav_comp.get("webdriver", False)
    brands = []

    for evt in fp.get("events", []):
        if len(evt) >= 2 and isinstance(evt[1], str):
            try:
                parsed = json.loads(evt[1])
                if (
                    isinstance(parsed, list)
                    and len(parsed) > 8
                    and isinstance(parsed[0], str)
                    and "AppleWebKit" in parsed[0]
                ):
                    device_memory = parsed[2] if len(parsed) > 2 and isinstance(parsed[2], int) else device_memory
                    hw_concurrency = parsed[3] if len(parsed) > 3 and isinstance(parsed[3], int) else hw_concurrency
                    language = parsed[4] if len(parsed) > 4 and isinstance(parsed[4], str) else language
                    languages = parsed[5] if len(parsed) > 5 and isinstance(parsed[5], list) else languages
                    platform = parsed[6] if len(parsed) > 6 and isinstance(parsed[6], str) else platform
                    raw_brands = parsed[8] if len(parsed) > 8 and isinstance(parsed[8], list) else []
                    for b in raw_brands:
                        if isinstance(b, str):
                            parts = b.rsplit(" ", 1)
                            if len(parts) == 2 and parts[1].isdigit():
                                brands.append({"brand": parts[0], "version": parts[1]})
                    if len(parsed) > 11 and isinstance(parsed[11], int):
                        max_touch = parsed[11]
                    break
            except Exception:
                continue

    if not brands:
        brands = [
            {"brand": "Not;A=Brand", "version": "8"},
            {"brand": "Chromium", "version": chrome_ver},
            {"brand": "Google Chrome", "version": chrome_ver},
        ]

    if "Win" in platform:
        plat_ua = "Windows"
    elif "Mac" in platform:
        plat_ua = "macOS"
    else:
        plat_ua = "Linux"

    return {
        "user_agent": ua,
        "app_version": ua.replace("Mozilla/", ""),
        "platform": platform,
        "language": language,
        "languages": languages,
        "max_touch_points": max_touch,
        "webdriver": webdriver,
        "vendor": fp.get("vendor", "Google Inc."),
        "chrome_version": chrome_ver,
        "hardware_concurrency": hw_concurrency,
        "device_memory": device_memory,
        "screen_width": screen_comp.get("width", 1920),
        "screen_height": screen_comp.get("height", 1080),
        "avail_width": screen_comp.get("avail_width", 1920),
        "avail_height": screen_comp.get("avail_height", 1032),
        "color_depth": screen_comp.get("color_depth", 24),
        "pixel_depth": screen_comp.get("pixel_depth", 24),
        "plat_ua": plat_ua,
        "brands": brands,
    }


def compute_model_error(points: np.ndarray, timestamps: np.ndarray) -> float:
    if len(points) < 4:
        return 0.0

    diffs = np.diff(points, axis=0)
    seg_lens = np.sqrt(np.sum(diffs**2, axis=1))
    cum_len = np.concatenate(([0.0], np.cumsum(seg_lens)))
    total = cum_len[-1]
    if total == 0:
        return 0.0
    s = cum_len / total

    coeffs_x = np.polyfit(s, points[:, 0], 3)
    coeffs_y = np.polyfit(s, points[:, 1], 3)
    fitted_x = np.polyval(coeffs_x, s)
    fitted_y = np.polyval(coeffs_y, s)

    errors = np.sqrt((points[:, 0] - fitted_x)**2 + (points[:, 1] - fitted_y)**2)
    mean_error = np.mean(errors)

    return float(mean_error * 2.0)


def compute_click_error(points: np.ndarray, timestamps: np.ndarray,
                        click_events: List[List[float]]) -> float:
    if len(points) < 4 or not click_events:
        return 0.0

    diffs = np.diff(points, axis=0)
    seg_lens = np.sqrt(np.sum(diffs**2, axis=1))
    cum_len = np.concatenate(([0.0], np.cumsum(seg_lens)))
    total = cum_len[-1]
    if total == 0:
        return 0.0
    s = cum_len / total
    coeffs_x = np.polyfit(s, points[:, 0], 3)
    coeffs_y = np.polyfit(s, points[:, 1], 3)

    total_error = 0.0
    for x, y, t in click_events:
        idx = np.searchsorted(timestamps, t)
        idx = np.clip(idx, 0, len(timestamps)-1)
        t_norm = (t - timestamps[0]) / (timestamps[-1] - timestamps[0]) if timestamps[-1] > timestamps[0] else 0
        t_norm = np.clip(t_norm, 0, 1)
        fitted_x = np.polyval(coeffs_x, t_norm)
        fitted_y = np.polyval(coeffs_y, t_norm)
        dist = np.sqrt((x - fitted_x)**2 + (y - fitted_y)**2)
        total_error += dist
    return total_error


def generate_motion_trajectory(
    waypoints: Sequence[Sequence[float]],
    config: Optional[ScreenConfig] = None,
    style: Optional[MovementStyle] = None,
) -> Trajectory:
    if config is None:
        config = ScreenConfig()
    if style is None:
        style = MovementStyle.random()

    if isinstance(waypoints[0], (list, tuple)) and len(waypoints[0]) == 2:
        xs = [p[0] for p in waypoints]
        ys = [p[1] for p in waypoints]
        coords = [xs, ys]
    else:
        coords = waypoints

    segs = generate(coords, config, style)
    merged = merge(segs)
    return deduplicate(merged)


def add_timing_jitter(traj: Trajectory, std: float = 1.5) -> Trajectory:
    n = len(traj.t)
    if n < 2:
        return traj
    jitter = np.random.normal(0, std, size=n)
    t_new = traj.t + jitter
    t_new = np.clip(t_new, 0, traj.t[-1])
    t_new = np.sort(t_new)
    return Trajectory(x=traj.x, y=traj.y, t=t_new, v=traj.v)


def generate_payload_from_trajectories(
    traj_pm: Trajectory,
    traj_mm: Trajectory,
    click_events: List[Tuple[float, float, float]] = None,
    start_time: Optional[int] = None,
    config: Optional[ScreenConfig] = None,
    fingerprint: Optional[Dict[str, Any]] = None,
    href: str = "https://example.com/",
    site_info: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    if start_time is None:
        start_time = int(time.time() * 1000)
    if config is None:
        config = ScreenConfig()
    if click_events is None:
        click_events = []

    site_cfg = get_site_config(href, site_info)
    dr = site_cfg.get("dr", "")
    pel = site_cfg.get("pel", '<div id="hcap-script"></div>')
    theme = site_cfg.get("theme", random.randint(1_000_000_000, 2_000_000_000))
    inv = site_cfg.get("inv", False)
    exec_mode = site_cfg.get("exec", "m")

    pm_list = [
        [float(x), float(y), int(t)]
        for x, y, t in zip(traj_pm.x, traj_pm.y, traj_pm.t)
    ]
    mm_list = [
        [float(x), float(y), int(t)]
        for x, y, t in zip(traj_mm.x, traj_mm.y, traj_mm.t)
    ]

    pm_pts = np.column_stack((traj_pm.x, traj_pm.y))
    mm_pts = np.column_stack((traj_mm.x, traj_mm.y))
    pm_mp = compute_model_error(pm_pts, traj_pm.t)
    mm_mp = compute_model_error(mm_pts, traj_mm.t)

    md = []
    mu = []
    for i, (x, y, t) in enumerate(click_events):
        if i % 2 == 0:
            md.append([int(x), int(y), int(t)])
        else:
            mu.append([int(x), int(y), int(t)])

    md_mp = compute_click_error(pm_pts, traj_pm.t, md) if md else 0.0
    mu_mp = compute_click_error(pm_pts, traj_pm.t, mu) if mu else 0.0

    widget_id = _generate_widget_id()

    payload = {
        "st": start_time,
        "dct": start_time,
        "pm": pm_list,
        "pm-mp": float(pm_mp),
        "mm": mm_list,
        "mm-mp": float(mm_mp),
        "md": md,
        "md-mp": float(md_mp),
        "mu": mu,
        "mu-mp": float(mu_mp),
        "v": 1,
        "session": [],
        "widgetList": [widget_id],
        "widgetId": widget_id,
        "imd": _generate_imd(),
        "topLevel": generate_toplevel(
            start_time,
            fingerprint=fingerprint,
            dr=dr,
            pel=pel,
            theme=theme,
            inv=inv,
            exec_mode=exec_mode,
        ),
        "href": href,
        "prev": {
            "escaped": False,
            "passed": False,
            "expiredChallenge": False,
            "expiredResponse": False,
        },
        "vmdata": "[[0,\"WmOt6dmZ2PXpbsaoiYYn5RasdzAjz0kMkw9tF4C6FNWGe2Py1Q4TzYXFHn4K0Q7wIVWjNvEPVwgfnJ6l+xGSWZiQ5+rwwYnvTHvUd8dCm1DYdw5p66ZELtZjrf1ebRNWSW2VsG/xt+wre+RtJiGFK/ZDqygP3df0hMlhsQWrnzxedrZLisJQz2Gs5g/ky4eWMxTM4w6kuJV8tp6l+nQKkZe8RiLxfdrnE1xhOUNshOmBduIyLHkt++Nctf5ADflzg8OBwHXEgEMxno0M9o+hXsnZHmlr0V7e6SGXQ9SRjUduLBztZpw28Dx9xAof1cxOb4pBkWn3+9T0kxRbNuaCRWjI9nrlg3Vh1RDReOKf130TwdYdw+10lOAeYxfdv9Xfyh20PIG6tLIW5CrvlvXzkeU+4jMEccNKKpSIt+BBJ81S/Mp+PCAc1qH1RmHX3FIQ\\\"]\"]",
    }
    return payload


def generate_toplevel(
    start_time: int,
    fingerprint: Optional[Dict[str, Any]] = None,
    dr: str = "",
    pel: str = '<div id="hcap-script"></div>',
    theme: Optional[int] = None,
    inv: bool = False,
    exec_mode: str = "m",
) -> Dict[str, Any]:
    fp = _parse_fingerprint(fingerprint) if fingerprint else {}

    if theme is None:
        theme = random.randint(1_000_000_000, 2_000_000_000)

    screen_width = fp.get("screen_width", 1920)
    screen_height = fp.get("screen_height", 1080)
    avail_width = fp.get("avail_width", 1920)
    avail_height = fp.get("avail_height", 1032)
    color_depth = fp.get("color_depth", 24)
    pixel_depth = fp.get("pixel_depth", 24)

    inner_w = max(200, avail_width - random.randint(10, 60))
    inner_h = max(200, avail_height - random.randint(40, 200))

    orient = "landscape" if screen_width >= screen_height else "portrait"

    return {
        "st": start_time,
        "sc": {
            "availWidth": avail_width,
            "availHeight": avail_height,
            "width": screen_width,
            "height": screen_height,
            "colorDepth": color_depth,
            "pixelDepth": pixel_depth,
            "availLeft": 0,
            "availTop": 0,
            "onchange": None,
            "isExtended": True,
        },
        "or": orient,
        "wi": [inner_w, inner_h],
        "nv": {
            "vendorSub": "",
            "productSub": "20030107",
            "vendor": fp.get("vendor", "Google Inc."),
            "maxTouchPoints": fp.get("max_touch_points", 0),
            "hardwareConcurrency": fp.get("hardware_concurrency", 12),
            "cookieEnabled": True,
            "appCodeName": "Mozilla",
            "appName": "Netscape",
            "appVersion": fp.get("app_version", "5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/150.0.0.0 Safari/537.36"),
            "platform": fp.get("platform", "Win32"),
            "product": "Gecko",
            "userAgent": fp.get("user_agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/150.0.0.0 Safari/537.36"),
            "language": fp.get("language", "nl-BE"),
            "languages": fp.get("languages", ["nl-BE", "nl-NL", "nl", "en-US", "en"]),
            "onLine": True,
            "webdriver": fp.get("webdriver", False),
            "pdfViewerEnabled": True,
            "deviceMemory": fp.get("device_memory", 16),
            "userAgentData": {
                "brands": fp.get("brands", [
                    {"brand": "Not;A=Brand", "version": "8"},
                    {"brand": "Chromium", "version": "150"},
                    {"brand": "Google Chrome", "version": "150"},
                ]),
                "mobile": False,
                "platform": fp.get("plat_ua", "Windows"),
            },
            "plugins": [
                "internal-pdf-viewer",
                "internal-pdf-viewer",
                "internal-pdf-viewer",
                "internal-pdf-viewer",
                "internal-pdf-viewer",
            ],
        },
        "dr": dr,
        "inv": inv,
        "theme": theme,
        "pel": pel,
        "exec": exec_mode,
        "wn": [[inner_w, inner_h, 1, start_time + random.randint(1, 6)]],
        "wn-mp": 0,
        "xy": [[0, random.randint(0, 400), 1, start_time + random.randint(0, 2)]],
        "xy-mp": 0,
        "pm": [],
        "pm-mp": 0,
        "mm": [],
        "mm-mp": 0,
        "md": [],
        "md-mp": 0,
        "mu": [],
        "mu-mp": 0,
    }


def getcaptcha(
    start: Optional[Tuple[float, float]] = None,
    end: Optional[Tuple[float, float]] = None,
    config: Optional[ScreenConfig] = None,
    style: Optional[MovementStyle] = None,
    start_time: Optional[int] = None,
    fingerprint: Optional[Dict[str, Any]] = None,
    href: str = "https://example.com/",
    site_info: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    if config is None:
        config = ScreenConfig(sample_rate=60, width=1920, height=1080)

    if style is None:
        style = MovementStyle.random()
        style.speed_factor = np.random.uniform(0.6, 1.0)
        style.precision = np.random.uniform(0.8, 1.2)
        style.nervousness = np.random.uniform(0.3, 0.6)
        style.overshoot_tendency = 0.3

    if start is None:
        start = (np.random.randint(300, 600), np.random.randint(300, 600))
    if end is None:
        dx = np.random.randint(-30, 30)
        dy = np.random.randint(-30, 30)
        end = (start[0] + dx, start[1] + dy)

    style_pm = style
    style_mm = MovementStyle(
        speed_factor=style.speed_factor * np.random.uniform(0.9, 1.1),
        precision=style.precision * np.random.uniform(0.9, 1.1),
        nervousness=style.nervousness * np.random.uniform(0.9, 1.1),
        overshoot_tendency=style.overshoot_tendency,
        sub_movement_count=style.sub_movement_count,
        jerk_smoothness=style.jerk_smoothness,
    )

    traj_pm = generate_motion_trajectory([start, end], config, style_pm)
    traj_mm = generate_motion_trajectory([start, end], config, style_mm)

    traj_pm = add_timing_jitter(traj_pm, std=1.5)
    traj_mm = add_timing_jitter(traj_mm, std=1.5)

    last_x = int(traj_pm.x[-1] + np.random.randint(-2, 3))
    last_y = int(traj_pm.y[-1] + np.random.randint(-2, 3))
    last_t = int(traj_pm.t[-1])
    down_delay = np.random.randint(20, 60)
    up_delay = down_delay + np.random.randint(50, 120)
    click_events = [
        (last_x, last_y, last_t + down_delay),
        (last_x, last_y, last_t + up_delay),
    ]

    payload = generate_payload_from_trajectories(
        traj_pm, traj_mm, click_events, start_time, config,
        fingerprint=fingerprint, href=href, site_info=site_info,
    )

    top_traj_pm = generate_motion_trajectory([(50, 50), (800, 300)], config, MovementStyle.random())
    top_traj_mm = generate_motion_trajectory([(50, 50), (800, 300)], config, MovementStyle.random())

    site_cfg = get_site_config(href, site_info)
    top_level = generate_toplevel(
        start_time or int(time.time()*1000),
        fingerprint=fingerprint,
        dr=site_cfg.get("dr", ""),
        pel=site_cfg.get("pel", '<div id="hcap-script"></div>'),
        theme=site_cfg.get("theme"),
        inv=site_cfg.get("inv", False),
        exec_mode=site_cfg.get("exec", "m"),
    )
    top_level["pm"] = [[float(x), float(y), int(t)] for x, y, t in zip(top_traj_pm.x, top_traj_pm.y, top_traj_pm.t)]
    top_level["mm"] = [[float(x), float(y), int(t)] for x, y, t in zip(top_traj_mm.x, top_traj_mm.y, top_traj_mm.t)]
    top_level["pm-mp"] = compute_model_error(np.column_stack((top_traj_pm.x, top_traj_pm.y)), top_traj_pm.t)
    top_level["mm-mp"] = compute_model_error(np.column_stack((top_traj_mm.x, top_traj_mm.y)), top_traj_mm.t)
    top_level["md"] = []
    top_level["mu"] = []
    top_level["md-mp"] = 0
    top_level["mu-mp"] = 0
    payload["topLevel"] = top_level

    return payload


def checkcaptcha(
    start: Optional[Tuple[float, float]] = None,
    end: Optional[Tuple[float, float]] = None,
    config: Optional[ScreenConfig] = None,
    style: Optional[MovementStyle] = None,
    start_time: Optional[int] = None,
    fingerprint: Optional[Dict[str, Any]] = None,
    href: str = "https://example.com/",
    site_info: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    if config is None:
        config = ScreenConfig(sample_rate=60, width=1920, height=1080)
    if style is None:
        style = MovementStyle.random()
        style.speed_factor = np.random.uniform(0.6, 1.0)
        style.precision = np.random.uniform(0.8, 1.2)
        style.nervousness = np.random.uniform(0.3, 0.6)
        style.overshoot_tendency = 0.3

    if start_time is None:
        start_time = int(time.time() * 1000)

    if start is not None and end is not None:
        mid = (
            (start[0] + end[0]) / 2 + np.random.randint(-100, 100),
            (start[1] + end[1]) / 2 + np.random.randint(-100, 100),
        )
        waypoints = [start, mid, end]
    else:
        waypoints = [
            (100, 100),
            (400, 300),
            (600, 500),
            (300, 400),
            (500, 200),
            (200, 600),
        ]

    traj_pm = generate_motion_trajectory(waypoints, config, style)
    style_mm = MovementStyle(
        speed_factor=style.speed_factor * np.random.uniform(0.9, 1.1),
        precision=style.precision * np.random.uniform(0.9, 1.1),
        nervousness=style.nervousness * np.random.uniform(0.9, 1.1),
        overshoot_tendency=style.overshoot_tendency,
        sub_movement_count=style.sub_movement_count,
        jerk_smoothness=style.jerk_smoothness,
    )
    traj_mm = generate_motion_trajectory(waypoints, config, style_mm)

    traj_pm = add_timing_jitter(traj_pm, std=1.5)
    traj_mm = add_timing_jitter(traj_mm, std=1.5)

    total_pts = len(traj_pm.x)
    click_indices = [int(total_pts * 0.2), int(total_pts * 0.5), int(total_pts * 0.8)]
    click_events = []
    for idx in click_indices:
        if idx < total_pts:
            x = int(traj_pm.x[idx] + np.random.randint(-2, 3))
            y = int(traj_pm.y[idx] + np.random.randint(-2, 3))
            t = int(traj_pm.t[idx])
            down_delay = np.random.randint(20, 60)
            up_delay = down_delay + np.random.randint(50, 120)
            click_events.append((x, y, t + down_delay))
            click_events.append((x, y, t + up_delay))

    payload = generate_payload_from_trajectories(
        traj_pm, traj_mm, click_events, start_time, config,
        fingerprint=fingerprint, href=href, site_info=site_info,
    )

    top_waypoints = [
        (800, 50),
        (600, 200),
        (300, 300),
        (100, 500),
        (400, 600),
        (700, 400),
    ]
    top_traj_pm = generate_motion_trajectory(top_waypoints, config, MovementStyle.random())
    top_traj_mm = generate_motion_trajectory(top_waypoints, config, MovementStyle.random())
    top_traj_pm = add_timing_jitter(top_traj_pm, std=1.5)
    top_traj_mm = add_timing_jitter(top_traj_mm, std=1.5)

    site_cfg = get_site_config(href, site_info)
    top_level = generate_toplevel(
        start_time,
        fingerprint=fingerprint,
        dr=site_cfg.get("dr", ""),
        pel=site_cfg.get("pel", '<div id="hcap-script"></div>'),
        theme=site_cfg.get("theme"),
        inv=site_cfg.get("inv", False),
        exec_mode=site_cfg.get("exec", "m"),
    )
    top_level["pm"] = [[float(x), float(y), int(t)] for x, y, t in zip(top_traj_pm.x, top_traj_pm.y, top_traj_pm.t)]
    top_level["mm"] = [[float(x), float(y), int(t)] for x, y, t in zip(top_traj_mm.x, top_traj_mm.y, top_traj_mm.t)]
    top_level["pm-mp"] = compute_model_error(np.column_stack((top_traj_pm.x, top_traj_pm.y)), top_traj_pm.t)
    top_level["mm-mp"] = compute_model_error(np.column_stack((top_traj_mm.x, top_traj_mm.y)), top_traj_mm.t)
    top_level["md"] = []
    top_level["mu"] = []
    top_level["md-mp"] = 0
    top_level["mu-mp"] = 0
    payload["topLevel"] = top_level

    payload["tc"] = {
        str(uuid.uuid4()): [1, 10, 130],
        str(uuid.uuid4()): [1, 10, 130],
    }
    return payload
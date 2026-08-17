import json
import random

def rand_u64():
    return str(random.randint(0, 2**63 - 1))

def rand_u32():
    return random.randint(0, 2**32 - 1)

SCREEN_PRESETS = [
    (2560, 1440, 2560, 1392, 32, 32),
    (1920, 1080, 1920, 1040, 24, 24),
    (1366, 768, 1366, 728, 24, 24),
    (1536, 864, 1536, 816, 24, 24),
]

screen_width, screen_height, avail_width, avail_height, color_depth, pixel_depth = random.choice(SCREEN_PRESETS)

CHROME_VERSIONS = [
    "Chrome/147.0.0.0",
    "Chrome/146.0.0.0",
    "Chrome/145.0.0.0",
    "Chrome/144.0.0.0",
]
chrome_version = random.choice(CHROME_VERSIONS)
full_chrome_version = chrome_version.replace("Chrome/", "") + " (official build)"

user_agent = f"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) {chrome_version} Safari/537.36"

languages = random.sample(["en", "en-US", "en-GB", "nb", "da-DK"], k=random.randint(1, 3))
if "en" not in languages:
    languages.insert(0, "en")
language = languages[0]

hardware_concurrency = random.choice([4, 6, 8, 12, 16])
device_memory = random.choice([4, 8, 16, 32])
max_touch_points = 0

brands = [
    {"brand": "Not;A=Brand", "version": "8"},
    {"brand": "Chromium", "version": chrome_version.split("/")[1].split(".")[0]},
    {"brand": "Google Chrome", "version": chrome_version.split("/")[1].split(".")[0]},
]

vendor = random.choice([
    "Google Inc. (AMD)",
    "Google Inc. (NVIDIA)",
    "Google Inc. (Intel)",
])
renderer = random.choice([
    "ANGLE (AMD, AMD Radeon RX 7700 XT (0x0000747E) Direct3D11 vs_5_0 ps_5_0, D3D11)",
    "ANGLE (NVIDIA, NVIDIA GeForce RTX 4070 (0x00002786) Direct3D11 vs_5_0 ps_5_0, D3D11)",
    "ANGLE (Intel, Intel(R) UHD Graphics 770 (0x00004680) Direct3D11 vs_5_0 ps_5_0, D3D11)",
])

canvas_hash = str(random.randint(0, 2**63 - 1))
web_gl_hash = str(random.randint(0, 2**63 - 1))
webrtc_hash = str(random.randint(0, 2**63 - 1))
performance_hash = str(random.randint(0, 2**63 - 1))
parent_win_hash = str(random.randint(0, 2**63 - 1))
common_keys_hash = random.randint(0, 2**32 - 1)
audio_hash = "-1"

timezone = random.choice(["Europe/Oslo", "Europe/London", "America/New_York", "Asia/Tokyo"])

fingerprint = {
    "errs": {"list": []},
    "rand": [round(random.random(), 15) for _ in range(2)],
    "events": [],
    "vendor": vendor,
    "renderer": renderer,
    "components": {
        "chrome": True,
        "screen": {
            "width": screen_width,
            "height": screen_height,
            "avail_width": avail_width,
            "color_depth": color_depth,
            "pixel_depth": pixel_depth,
            "avail_height": avail_height,
        },
        "features": {
            "fetch": True,
            "web_rtc": True,
            "canvas_2d": True,
            "web_audio": True,
            "performance_entries": True,
        },
        "has_touch": False,
        "navigator": {
            "language": language,
            "platform": "Win32",
            "languages": languages,
            "webdriver": False,
            "user_agent": user_agent,
            "max_touch_points": max_touch_points,
            "plugins_undefined": False,
            "notification_query_permission": "Default",
        },
        "audio_hash": audio_hash,
        "extensions": [False],
        "canvas_hash": canvas_hash,
        "err_firefox": None,
        "r_bot_score": 0,
        "unique_keys": "0,Object,Function,Array,Number,parseFloat,parseInt,Infinity,NaN,undefined,Boolean,String,Symbol,Date,Promise,RegExp,Error,AggregateError,EvalError,RangeError,ReferenceError,SyntaxError,TypeError,URIError,globalThis,JSON,Math,Intl,ArrayBuffer,Atomics,Uint8Array,Int8Array,Uint16Array,Int16Array,Uint32Array,Int32Array,BigUint64Array,BigInt64Array,Uint8ClampedArray,Float32Array,Float64Array,DataView,Map,BigInt,Set,Iterator,WeakMap,WeakSet,Proxy,Reflect",
        "web_gl_hash": web_gl_hash,
        "webrtc_hash": webrtc_hash,
        "r_bot_score_2": 0,
        "has_indexed_db": True,
        "inv_unique_keys": "localStorage,sessionStorage",
        "parent_win_hash": parent_win_hash,
        "common_keys_hash": common_keys_hash,
        "common_keys_tail": "m6goztb,fuzn9KK,q_FSmf,NpQi3cc,tYAehvh,crv0SMN,NNwQMu,RES74Dh,OpuHnbl,M2TpNCZ,rnB5Lb,ae9TA4,qwhYE1,SDdabD,setupEnforcement,FingerprintJS,iSUgDe,F8Tx0z1,ym5EGMM,U0H0YeX,ak4YFT,__globalObject,__TextDecoder,__Uint8Array,__Buffer,__String,__Array,utf8ArrayToStr,_HQ1y1d,sG9PJ6,KZ57iW2,T8QwtO9,arkoseLabsClientApibc605911,regeneratorRuntime,ark",
        "performance_hash": performance_hash,
        "to_string_length": 0,
        "has_local_storage": True,
        "device_pixel_ratio": 1,
        "has_session_storage": True,
        "notification_api_permission": "Default",
        "r_bot_score_suspicious_keys": [],
    },
    "stack_data": [
        "new __Array\npPiZ7z\nObject.get",
        "new __Array\npPiZ7z",
        "Array.forEach (<anonymous>)",
        "Array.reduce (<anonymous>)",
        "<anonymous>",
        "Generator.next (<anonymous>)",
        "new Promise (<anonymous>)",
        "Array.map (<anonymous>)\nGenerator.next (<anonymous>)",
        "Array.map (<anonymous>)\nnew Promise (<anonymous>)",
    ],
    "suspicious_events": [],
}

special_event = [
    random.randint(0, 2**32 - 1),
    json.dumps([
        user_agent,
        user_agent.replace("Mozilla/", ""),
        device_memory,
        hardware_concurrency,
        language,
        languages,
        "Win32",
        None,
        [f"{b['brand']} {b['version']}" for b in brands],
        False,
        "Windows",
        max_touch_points,
        random.randint(0, 10),
        True,
        False,
        False,
        False,
        True,
        "[object Keyboard]",
        False,
        False,
    ]),
]
fingerprint["events"].append(special_event)

extra_events = [
    [random.randint(0, 2**32 - 1), json.dumps([random.randint(0, 2**32 - 1), random.randint(0, 2**32 - 1), random.randint(0, 2**32 - 1)])],
    [random.randint(0, 2**32 - 1), str(random.randint(0, 2**63 - 1))],
    [random.randint(0, 2**32 - 1), json.dumps([random.randint(0, 2**16 - 1), random.randint(0, 2**16 - 1), random.randint(0, 2**16 - 1)])],
    [random.randint(0, 2**32 - 1), json.dumps([random.randint(0, 2**32 - 1), random.randint(0, 2**32 - 1)])],
    [random.randint(0, 2**32 - 1), json.dumps([1, 2, 3, 4])],
    [random.randint(0, 2**32 - 1), json.dumps([0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31])],
    [random.randint(0, 2**32 - 1), json.dumps({"s": 0, "n": 0, "bfp": 1, "bfc": 1, "big": 0, "p": 0, "gcs": 1})],
    [random.randint(0, 2**32 - 1), json.dumps([random.randint(0, 2**32 - 1), random.randint(0, 2**32 - 1), random.randint(0, 2**32 - 1)])],
    [random.randint(0, 2**32 - 1), str(random.randint(0, 2**63 - 1))],
    [random.randint(0, 2**32 - 1), json.dumps([random.randint(0, 2**16 - 1), random.randint(0, 2**16 - 1)])],
    [random.randint(0, 2**32 - 1), json.dumps([0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20])],
]
fingerprint["events"].extend(extra_events)

with open("fingerprint.json", "w", encoding="utf-8") as f:
    json.dump(fingerprint, f, indent=2, ensure_ascii=False)

print("[+] New fingerprint saved to fingerprint.json")
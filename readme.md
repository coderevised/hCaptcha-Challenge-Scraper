<p align="center">
  <h1 align="center">hCaptcha Challenge Scraper</h1>
  <p align="center">
    A high-performance tool for collecting hCaptcha challenge datasets, including images, metadata, and challenge configurations. Built for researchers and developers working on captcha analysis and machine learning pipelines.
  </p>
</p>

---

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Supported Challenge Types](#supported-challenge-types)
- [Proxy Provider](#proxy-provider)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Project Structure](#project-structure)
- [Screenshots](#screenshots)
- [License](#license)

---

## Overview

hCaptcha Challenge Scraper automates the process of fetching and archiving hCaptcha challenges from any site that uses hCaptcha. It handles the full hCaptcha lifecycle — version detection, site configuration retrieval, HSL proof-of-work solving, challenge fetching, and media downloading — all through direct HTTP requests with no browser automation required.

Challenges are saved in an organized directory structure with full JSON metadata and all associated media files (images, videos), ready for dataset construction or further analysis.

---

## Features

- **No Browser Required** — Pure HTTP-based approach using `requests`. No Selenium, Playwright, or headless browsers.
- **HSL Proof-of-Work Solver** — Built-in local solver for hCaptcha's hashcash-style proof-of-work challenges.
- **Realistic Fingerprinting** — Generates randomized browser fingerprints with plausible screen resolutions, GPU renderers, user agents, and telemetry data.
- **Full Motion Data** — Produces synthetic mouse movement, cursor flow, and interaction telemetry that passes hCaptcha's behavioral checks.
- **Concurrent Media Downloads** — Multi-threaded image and video downloading with automatic format detection and fallback handling.
- **Proxy Support** — Route all traffic through HTTP proxies to avoid rate limiting and IP-based blocking.
- **Organized Output** — Challenges are saved by type (`image label binary`, `image label area select`, `image drag drop`) and further grouped by the challenge's request question text (`requester_question`).
- **Configurable** — Control the number of challenges to fetch, delay between requests, target sitekey, and proxy settings via a single JSON config file.
- **Styled CLI Output** — Color-coded, timestamped logging with component labels for clear visibility into each step of the scraping process.

---

## Supported Challenge Types

| Type | Description |
|---|---|
| `image_label_binary` | Select all images matching a given prompt |
| `image_label_area_select` | Click on a specific region within an image |
| `image_drag_drop` | Drag an element to the correct position |

Additional challenge types are saved automatically under their respective `request_type` folder names.

---

## Recommended Proxy Provider

<a href="https://infinixproxy.net/">
  <img src="images/infinix_proxy.png" alt="InfinixProxy" width="100%">
</a>

This project is supported by [InfinixProxy](https://infinixproxy.net/) — high-quality residential and datacenter proxies at **$0.75/GB**. Reliable, fast, and affordable. If you are scraping at scale or need to rotate IPs to avoid rate limits, InfinixProxy is the recommended provider for this tool.

Visit [infinixproxy.net](https://infinixproxy.net/) to get started.

---

## Prerequisites

- Python 3.10 or higher
- `pip` package manager
- A working HTTP proxy

---

## Installation

```bash
git clone https://github.com/CodeRevised/hCaptcha-Challenge-Scraper.git
cd hCaptcha-Challenge-Scraper
pip install -r requirements.txt
```

### Dependencies

| Package | Purpose |
|---|---|
| `requests` | HTTP client for all API calls and media downloads |
| `numpy` | Numerical operations for motion data generation |
| `matplotlib` | Curve fitting used in synthetic cursor trajectories |
| `wcwidth` | Terminal width calculations for the CLI banner |

---

## Configuration

### 1. Generate a Fingerprint

Before scraping, generate a browser fingerprint that will be used across all requests:

```bash
python generate_fingerprint.py
```

This creates a `fingerprint.json` file containing a randomized but internally consistent browser fingerprint — screen dimensions, GPU info, user agent, canvas/WebGL hashes, and more.

### 2. Edit the Config File

Create or modify `config/config.json`:

```json
{
  "proxy": "http://user:pass@host:port",
  "sitekey": "a5f74b19-9e45-40e0-b45d-47ff91b7a6c2",
  "url": "https://accounts.hcaptcha.com/demo",
  "max_challenges": 10,
  "delay_sec": 0
}
```

| Field | Type | Description |
|---|---|---|
| `proxy` | `string` | HTTP proxy URL (required) |
| `sitekey` | `string` | The hCaptcha sitekey to target (required) |
| `url` | `string` | The page URL where hCaptcha is deployed (required) |
| `max_challenges` | `int` | Number of challenges to fetch per run (default: `30`) |
| `delay_sec` | `float` | Delay in seconds between challenge fetches (default: `0`) |

---

## Usage

```bash
python fetcher.py
```

Or specify a custom config path:

```bash
python fetcher.py --config path/to/config.json
```

The scraper will:
1. Display the CLI banner with version and environment info
2. Load the config and establish an HTTP session through the configured proxy
3. Fetch the current hCaptcha API version
4. Retrieve the site configuration for the target sitekey
5. For each challenge:
   - Solve the HSL proof-of-work locally
   - Request a challenge from hCaptcha's API
   - Download all associated media files (images/videos) concurrently
   - Save the challenge JSON and media to `./challenges/<type>/<question_text>/challenge_<N>/`
6. Print a summary of all challenges collected, grouped by type

### Output Structure

```
challenges/
├── image label binary/
│     └── Select every animal that spends time in trees/
│         └── challenge_0/
│              ├── challenge.json
│              ├── img_0.png
│              └── img_1.png
├── image label area select/
│    └── Please click on the center of the flower/
│         └── challenge_0/
│              ├── challenge.json
│              └── example.png
└── image drag drop/
     └── Please drag the shape to the arrow/
          └── challenge_0/
        ...
```

---

## Project Structure

```
hcaptcha-challenge-scraper/
├── fetcher.py
├── generate_fingerprint.py
├── requirements.txt
├── config/
│   ├── config.json
├── core/
│   ├── hcaptcha_client.py
│   ├── hsl_solver.py
│   ├── http_client.py
│   ├── motion.py
│   ├── cursorflow.py
│   ├── telemetry.py
│   ├── saver.py
├── scraper/
│   ├── __init__.py
│   ├── scraper.py
│   ├── config.py
│   ├── banner.py
│   ├── logger.py
└── challenges/
```

---

## Screenshots

### Fingerprint Generation

<img src="images/fingerprint_run.png" alt="Fingerprint generation output" width="100%">

### Challenge Fetching

<img src="images/fetcher_run.png" alt="Challenge fetcher output showing collected challenges and summary" width="100%">

---

## License

This project is licensed under the [MIT License](LICENSE).

© 2026 CodeRevised. All rights reserved.

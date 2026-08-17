# 🕸️ hCaptcha Challenge Scraper

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white">
  <img src="https://img.shields.io/badge/License-MIT-green?style=for-the-badge">
  <img src="https://img.shields.io/badge/Platform-Windows%20%7C%20Linux-blue?style=for-the-badge">
</p>

<p align="center">
  <b>Automated hCaptcha dataset collection with browser fingerprinting, human-like motion simulation, HSL solving, and structured media extraction.</b>
</p>

---

## 📌 Overview

**hCaptcha Challenge Scraper** is a modular Python project for collecting hCaptcha challenge datasets.

It automates the complete collection pipeline—from realistic browser fingerprint generation and human-like cursor simulation to HSL proof solving, challenge retrieval, media downloading, and structured dataset organization.

The project was built with maintainability in mind, featuring a clean architecture, colorful component-based logging, telemetry, proxy support, and robust error handling.

> **Educational & Research Project**
>
> This project is intended for security research, reverse engineering, dataset generation, and academic experimentation.

---

# ✨ Features

* 🎯 Automated hCaptcha challenge collection
* 🧠 Local HSL proof solving
* 🖥️ Realistic browser fingerprint generation
* 🖱️ Human-like cursor movement simulation
* 📈 Motion curve generation
* 🌐 HTTP/HTTPS proxy support
* 📥 Automatic media downloading
* 📂 Structured dataset organization
* 🎨 Beautiful Sakura-themed CLI
* 📊 Performance telemetry
* 🧩 Modular architecture
* ⚡ Lightweight & easy to extend

---

# 📂 Project Structure

```text
hcaptcha-challenge-scraper/
│
├── fetcher.py
├── generate_fingerprint.py
├── fingerprint.json
├── requirements.txt
├── README.md
│
├── scraper/
│   ├── __init__.py
│   ├── banner.py
│   ├── config.py
│   ├── logger.py
│   └── scraper.py
│
├── core/
│   ├── cursorflow.py
│   ├── hcaptcha_client.py
│   ├── hsl_solver.py
│   ├── http_client.py
│   ├── motion.py
│   ├── saver.py
│   └── telemetry.py
│
├── config/
│   └── config.json
│
└── challenges/
    ├── image_drag_drop/
    ├── image_label_binary/
    ├── image_label_area_select/
    └── ...
```

---

# 🔄 Workflow

```text
Generate Fingerprint
        │
        ▼
Load Configuration
        │
        ▼
Initialize Session
        │
        ▼
Fetch Site Config
        │
        ▼
Solve HSL Proof
        │
        ▼
Request Challenge
        │
        ▼
Download Media
        │
        ▼
Validate Files
        │
        ▼
Save Dataset
```

---

# 🧠 Browser Fingerprinting

The project generates realistic browser fingerprints before starting a scraping session.

Generated information includes:

* User-Agent
* Platform
* Screen Resolution
* Timezone
* Language
* Canvas Fingerprint
* WebGL Vendor
* Rendering Information

The fingerprint is stored inside:

```text
fingerprint.json
```

and reused by the HTTP client to mimic real browser sessions.

---

# 🖱️ Human-like Behavior

To emulate realistic browser interaction, the scraper includes two dedicated modules.

### `core/motion.py`

Generates natural motion curves.

Features:

* Smooth acceleration
* Smooth deceleration
* Variable speed

---

### `core/cursorflw.py`

Creates realistic mouse paths.

Features:

* Human-like trajectories
* Curved movement
* Natural randomness
* Position interpolation

---

# 🔐 HSL Solver

The scraper performs HSL proof computation locally.

Benefits:

* No external solving service
* Faster execution
* Reduced latency
* Complete control over the solving process

Timing statistics are automatically recorded using the telemetry module.

---

# 🌐 HTTP Client

The custom HTTP client extends `requests.Session` with:

* Browser fingerprints
* Proxy support
* Browser headers
* Session management
* Retry handling

---

# 📥 Dataset Organization

Every collected challenge is saved automatically.

```text
challenges/
│
├── image_drag_drop/
│   └── challenge_0/
│       ├── challenge.json
│       └── media/
│           ├── 0001.webp
│           ├── 0002.webp
│           └── ...
│
├── image_label_binary/
│   └── challenge_1/
│
└── image_label_area_select/
```

Each challenge contains:

* Original challenge JSON
* All associated media
* Preserved file structure

---

# 📋 Configuration

Example configuration:

```json
{
    "proxy": "http://username:password@host:port",
    "sitekey": "site_key_here",
    "url": "https://example.com",
    "max_challenges": 30,
    "delay_sec": 2
}
```

| Option         | Description            |
| -------------- | ---------------------- |
| proxy          | HTTP/HTTPS proxy       |
| sitekey        | hCaptcha Site Key      |
| url            | Target website         |
| max_challenges | Number of challenges   |
| delay_sec      | Delay between requests |

---

# 🎨 Logging

The project includes a custom logging framework.

Example output:

```text
22:11:31 INFO      Collector      Fetching challenge 21/30
22:11:33 OK        Solver         HSL solved in 0 ms
22:11:42 SAVE      Storage        Saved challenge_6 (image_label_area_select • 2 files)

22:11:44 WARNING   Network        HTTPSConnectionPool(...)
```

Features:

* Component-based logging
* ANSI colors
* Fixed-width formatting
* Session summaries
* Clean alignment
* Timestamped output

---

# 📊 Telemetry

Performance metrics currently tracked:

* Site Configuration
* Challenge Retrieval
* HSL Solve Time

The telemetry module can easily be extended with additional metrics.

---

# ⚙️ Installation

Clone the repository:

```bash
git clone https://github.com/CodeRevised/hcaptcha-challenge-scraper.git
cd hcaptcha-challenge-scraper
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Generate a fingerprint:

```bash
python generate_fingerprint.py
```

Configure:

```text
config/config.json
```

Run:

```bash
python fetcher.py
```

---

# 📦 Requirements

```
Python 3.10+
matplotlib>=3.7.0
numpy>=1.24.0
requests>=2.31.0
wcwidth>=0.2.5
```

---

# 🔧 Core Modules

| Module                  | Purpose                        |
| ----------------------- | ------------------------------ |
| generate_fingerprint.py | Browser fingerprint generation |
| core/http_client.py     | HTTP session with fingerprints |
| core/hcaptcha_client.py | hCaptcha API interactions      |
| core/hsl_solver.py      | HSL proof solver               |
| core/motion.py          | Motion simulation              |
| core/cursorflw.py       | Cursor movement generation     |
| core/saver.py           | Media downloading              |
| core/telemetry.py       | Performance metrics            |
| scraper/logger.py       | CLI logging                    |
| scraper/banner.py       | Startup banner                 |
| scraper/config.py       | Configuration loader           |
| scraper/scraper.py      | Main scraper implementation    |

---

# 🛡️ Error Handling

The scraper is designed to continue running whenever possible.

Handled scenarios include:

* Network failures
* Invalid proxies
* Partial downloads
* Missing media
* Unexpected exceptions

Rather than terminating, failed challenges are skipped while preserving dataset integrity.

---

# 📈 Performance

* Local HSL solving
* Lightweight fingerprint reuse
* Sequential media downloading
* Configurable delays
* Minimal memory usage

---

# 🔒 Privacy

* No analytics
* No telemetry uploads
* Local dataset storage
* Local fingerprint generation
* Optional proxy support

---

# 🤝 Contributing

Pull requests are welcome.

Areas for contribution include:

* Additional challenge support
* Improved fingerprint generation
* Better motion simulation
* Performance optimizations
* Logging improvements
* New telemetry metrics

---

# 📜 License

This project is licensed under the **MIT License**.

---

# 👨‍💻 Author

<p align="center">

### **CodeRevised**

Python • Automation • Reverse Engineering • Security Research

</p>

---

<p align="center">
Made with ❤️ by <b>CodeRevised</b>
</p>

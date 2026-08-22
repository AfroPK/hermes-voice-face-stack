<div id="top">

<!-- HEADER STYLE: MODERN -->
<div align="left" style="position: relative; width: 100%; height: 100%; ">

# <code>⚡ HERMES Voice + Face Stack</code>

<em><em>Turn your Hermes agent into a talking, face-having assistant on one Windows machine — press-and-hold **Home** to talk; a living circuit-board face listens, thinks, and speaks in sync. No Linux homelab required.</em></em>

<!-- CREDIT AT TOP (as required by the original author's license) -->
> 🧠 **Built on the open work of [Jared Rhodenizer (@jaredrhod)](https://github.com/jaredrhod).**
> This repo **pulls [`backtalk`](https://github.com/jaredrhod/backtalk) and [`ai-visualizer`](https://github.com/jaredrhod/ai-visualizer) from his own repos** — we do not redistribute them. Those projects are AGPL-3.0; respect their terms.
> - [`backtalk`](https://github.com/jaredrhod/backtalk) — ears (Whisper STT), mouth (Kokoro TTS), push-to-talk loop. We only swap the brain; the voice code is entirely his.
> - [`ai-visualizer`](https://github.com/jaredrhod/ai-visualizer) — the animated face + the `.voice_state`/`.voice_waveform` signal-bus convention.
> - Both are part of his [`fullstack-agent`](https://github.com/jaredrhod/fullstack-agent) project (memory · voice · face · hands).
> This repo only layers in a small shim that swaps the *brain* from Claude to **Hermes**, plus this single-box setup guide.

<!-- BADGES -->
![GitHub release](https://img.shields.io/github/v/release/AfroPK/hermes-voice-face-stack?style=flat-square&color=22d3ee)
![Platform](https://img.shields.io/badge/Platform-Windows%2010%2F11-22d3ee?style=flat-square)
![License](https://img.shields.io/badge/License-MIT-22d3ee?style=flat-square)
![Upstream](https://img.shields.io/badge/Upstream-AGPL--3.0-22d3ee?style=flat-square)

<em>Built with the tools and technologies:</em>

<img src="https://img.shields.io/badge/Python-3776AB.svg?style=flat-square&logo=Python&logoColor=white" alt="Python">
<img src="https://img.shields.io/badge/Whisper-000000.svg?style=flat-square&logo=OpenAI&logoColor=white" alt="Whisper">
<img src="https://img.shields.io/badge/Kokoro-000000.svg?style=flat-square&logo=OpenAI&logoColor=white" alt="Kokoro">

</div>
</div>
<br clear="right">

---

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [How It Works](#how-it-works)
- [Getting Started](#getting-started)
    - [Prerequisites](#prerequisites)
    - [1. Enable Hermes' API](#1-enable-hermes-api)
    - [2. Install the face (ai-visualizer)](#2-install-the-face-ai-visualizer)
    - [3. Install backtalk with the Hermes brain](#3-install-backtalk-with-the-hermes-brain)
    - [4. Talk](#4-talk)
- [Troubleshooting](#troubleshooting)
- [Optional: Split machines](#optional-split-machines)
- [License](#license)

---

## Overview

**HERMES Voice + Face Stack** gives the [Hermes agent](https://github.com/NousResearch/hermes-agent) a real voice and a living face, all on a **single Windows PC**. It reuses the polish of backtalk+ai-visualizer (by [@jaredrhod](https://github.com/jaredrhod)) but routes the *brain* to Hermes' own OpenAI-compatible API instead of Claude.

**Why?**
- 🟦 **Local voice** — Whisper hears you, Kokoro speaks back; models run on your machine.
- 🟪 **Live face** — the board animates `LISTENING → THINKING → SPEAKING` in sync.
- 🟧 **One box** — no Linux, no server, no cloud; the face sync is native (files, not network).
- 🟩 **Agent-friendly** — this README doubles as an agent-followable runbook.

> **No API keys ship in this repo.** Every run step below generates its own secret locally.

---

## Features

| Feature | Details |
|---------|---------|
| **Push-to-talk** | Hold **Home**, speak; backtalk transcribes + Hermes replies aloud |
| **Live circuit-board face** | LISTENING · THINKING (full-speed "storm") · SPEAKING pulses · idle |
| **Local models** | Whisper (STT) + Kokoro (TTS), no API keys for the voice itself |
| **Single-box** | face + voice + brain all on one Windows machine |
| **Hermes-native brain** | Hermes' `/v1/chat/completions` endpoint |
| **Agent-followable** | README doubles as a step-by-step runbook an agent can execute |

---

## How It Works

```
[ you hold Home, speak ]
        |  Whisper STT
        v
   backtalk (ears + mouth)
        |  your text
        v
   Hermes brain  ->  OpenAI-compatible API (:8642)
        |
   backtalk's signals write .voice_state / .voice_waveform
        |                 (idle / listening / thinking / speaking)
        v
   ai-visualizer face  <- reads them, animates
```

Because everything is on the same machine, backtalk writes the face state
**directly** into the visualizer's `bus_dir` — no network relay needed.

---

## Getting Started

### Prerequisites

- **Windows 10/11** with a microphone and speakers
- **Hermes agent installed & working** on this machine (desktop app or `hermes` CLI)
- **uv** — [astral.sh/uv](https://astral.sh/uv)
- ~1 GB free for the local voice models (downloaded on first run)
- `git` (optional; only if cloning manually)

### 1. Enable Hermes' API

backtalk talks to Hermes over its built-in, OpenAI-compatible API server. It needs an API key to start.

```powershell
# generate a strong key (you keep this)
$k = -join ((48..57)+(65..90)+(97..122) | Get-Random -Count 32 | ForEach-Object {[char]$_})
Write-Output "YOUR_KEY: $k"
```

Set these where Hermes reads its environment (`.env` / service env / launcher — the spot varies; ask your Hermes install where it loads env), then **restart the Hermes gateway**:

```
API_SERVER_KEY=<your-32-char-key>
API_SERVER_PORT=8642
API_SERVER_HOST=127.0.0.1
```

Verify:
```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8642/v1/models" -Headers @{Authorization="Bearer $k"}
```

> Keep `API_SERVER_HOST=127.0.0.1` for the local setup. Do **not** expose it to the network unless it's intentional (see [Split Machines](#optional-split-machines)).

### 2. Install the face (ai-visualizer)

```powershell
git clone https://github.com/jaredrhod/ai-visualizer my-agent
cd my-agent
```

Create `my-agent/ai-visualizer.json` (or edit the existing one) so the face reads the bus where backtalk will write it:

```json
{
  "name": "HERMES",
  "face": "board",
  "host": "127.0.0.1",
  "port": 8790,
  "bus_dir": "C:\\my-agent"
}
```

Start the face and open the board:

```powershell
python server.py --no-open
# open http://127.0.0.1:8790/faces/board/  ->  shows "IDLE / SIGNAL BUS - ONLINE"
```

### 3. Install backtalk with the Hermes brain

```powershell
git clone https://github.com/jaredrhod/backtalk backtalk
cd backtalk
```

Copy this repo's shim into backtalk and point backtalk at it:

```powershell
copy <this-repo>\scripts\hermes_brain.py backtalk\hermes_brain.py
```

Edit `backtalk/main.py`:

```python
from backtalk.hermes_brain import WarmBrain   # was: from backtalk.brain import WarmBrain
```

Create/edit `backtalk.json` so backtalk's signals go where the face reads:

```json
{
  "name": "HERMES",
  "model": "hermes",
  "ptt_key": "home",
  "permission_mode": "ask",
  "signals_dir": "C:\\my-agent"
}
```

Set the Hermes API env for backtalk (user env vars work best):

```powershell
$env:HERMES_API_URL   = "http://127.0.0.1:8642/v1"
$env:HERMES_API_KEY   = "your-key"
```

Run backtalk (first run downloads Whisper + Kokoro models):

```powershell
uv run python -m backtalk.main
```

### 4. Talk

1. Face tab open at `http://127.0.0.1:8790/faces/board/`
2. backtalk running in a terminal
3. **Hold Home, speak, release.** The board shows **LISTENING → THINKING → SPEAKING → IDLE**.

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| `:8642` not listening | Key missing/too short (<16) or gateway not restarted |
| Board stuck on IDLE | `signals_dir` ≠ face's `bus_dir` — both must be the same folder |
| backtalk won't start / steals mic | Close ALL old backtalk windows; launch exactly one |
| No voice heard | First run downloads models; check backtalk's output; mic must be default input |

---

## Optional: Split Machines

Hermes on a server, face/voice on your PC? See [`docs/relay-option.md`](docs/relay-option.md) for the small HTTP-relay variant used in the homelab design.

---

## License

This tutorial repo (shim script + docs) is **MIT** — see [`LICENSE`](LICENSE). The upstream `backtalk` / `ai-visualizer` dependencies remain **AGPL-3.0** as in their respective repos (credited at the top).
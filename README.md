# HERMES Voice + Face Stack (single Windows box)

Turn your Hermes agent into a **talking, face-having assistant** on one Windows
machine — no Linux homelab required. Press-and-hold to talk to your agent;
a full-screen circuit-board "face" listens, thinks, and speaks in sync.

Built from the same pieces as the original fullstack-agent stack
(backtalk voice + ai-visualizer face), rewired so the *brain* is **Hermes**
instead of Claude, and everything runs locally on one Windows PC.

---

## How it works

Three pieces on one machine:

```
[ you speak ]  ->  backtalk (ears: Whisper STT, mouth: Kokoro TTS)
                      |  your text
                      v
                 Hermes brain   <- the OpenAI-compatible API server (:8642)
                      |
                      |  backtalk writes .voice_state / .voice_waveform
                      v                    (idle/listening/thinking/speaking)
                 ai-visualizer face  <- reads those files, animates
```

Because everything lives on the **same machine**, backtalk's built-in
`signals` write the face state **directly** into the visualizer's `bus_dir` —
no network relay needed. (Press-and-hold **Home** to talk.)

---

## Prerequisites

- **Windows 10/11**, with a microphone and speakers
- **Hermes agent installed and working** on this Windows box (the desktop app,
  or the `hermes` CLI). You should be able to chat with it normally.
- **uv** ([astral.sh/uv](https://astral.sh/uv)) — used to run backtalk
- **ffmpeg** (optional; only if you like it) — not required for this stack
- ~1 GB free for the local voice models (Whisper STT + Kokoro TTS), downloaded
  on first run

> **No API keys are shipped in this repo.** Every command below generates its
> own secret locally. You will not find any tokens, passwords, IPs, or personal
> data in these files.

---

## Part 1 — Enable Hermes' OpenAI-compatible API

backtalk talks to the Hermes brain over Hermes' built-in OpenAI-compatible
API server. It needs an API key to start.

1. Set an **API key** (generate a strong one yourself):
   ```powershell
   $rand = -join ((48..57)+(65..90)+(97..122) | Get-Random -Count 32 | ForEach-Object {[char]$_})
   Write-Output "Use this key: $rand"
   ```
   Copy that string somewhere safe.

2. Find where Hermes reads its environment. If you run Hermes as a service or
   via a `.env`/launcher, add these lines there (the exact env file varies by
   how Hermes was installed on your machine — ask your Hermes install / its
   agent for where `env`/service env lives, or read the Hermes docs):
   ```
   API_SERVER_KEY=<your 32-char key>
   # API_SERVER_PORT=8642   # optional, default 8642
   # API_SERVER_HOST=127.0.0.1
   ```
   > Keep `API_SERVER_HOST` bound to `127.0.0.1` — this is a LOCAL, single-box
   > setup. Do **not** expose it to the network unless you intend to.

3. **Restart the Hermes gateway** (`hermes gateway restart`, or the equivalent
   for your install) so it picks up the key.

4. Verify the API is up (it returns a model list with your key):
   ```powershell
   $k = "your-key"
   Invoke-RestMethod -Uri "http://127.0.0.1:8642/v1/models" -Headers @{Authorization="Bearer $k"}
   ```

---

## Part 2 — Install the visualizer (the face)

1. Clone the face (and check its README for Windows notes):
   ```powershell
   cd C:\
   git clone https://github.com/AfroPK/ai-visualizer my-agent
   cd my-agent
   ```
   *(Replace with the face repo — ai-visualizer by jaredrhod — if you prefer the
   upstream source; the README covers Windows setup.)*

2. Configure it to read the voice bus from your agent folder. The face reads
   tiny status files (`bus_dir`). Open `my-agent/ai-visualizer.json` (or create
   it) and set the folder that backtalk will write to. Convention:
   ```
   {
     "name": "HERMES",
     "face": "board",
     "host": "127.0.0.1",
     "port": 8790,
     "bus_dir": "C:\\my-agent"
   }
   ```
   `bus_dir` is the folder where the voice line writes `.voice_state`.
   Pick one folder and use it consistently for both backtalk and the face.

3. Start the face:
   ```powershell
   python server.py --no-open
   ```
   Open `http://127.0.0.1:8790/faces/board/` in a browser. You should see the
   board with **IDLE / SIGNAL BUS - ONLINE**. Leave it running.

---

## Part 3 — Install backtalk with the Hermes brain

backtalk is the ears + mouth. It ships a Claude brain by default; this repo
ships a drop-in `scripts/hermes_brain.py` that calls **Hermes** instead.

1. Clone backtalk:
   ```powershell
   cd C:\
   git clone https://github.com/jaredrhod/backtalk backtalk
   cd backtalk
   ```

2. **Replace its Claude brain with the Hermes shim (this repo's script):**
   ```powershell
   # Copy the shim into backtalk's package
   copy <this-repo>\scripts\hermes_brain.py backtalk\hermes_brain.py
   ```
   Then point backtalk at it by editing `backtalk/main.py` — change:
   ```python
   from backtalk.brain import WarmBrain
   ```
   to:
   ```python
   from backtalk.hermes_brain import WarmBrain
   ```
   > The shim is small and self-contained. It only changes the *brain* (Claude→Hermes API). backtalk's own voice loop and its native `signals` (which drive the face) are untouched.

3. Create/edit `backtalk.json` to point backtalk at your Hermes API **and** at
   the same `bus_dir` as the face:
   ```json
   {
     "name": "HERMES",
     "model": "hermes",
     "ptt_key": "home",
     "signals_dir": "C:\\my-agent",
     "permission_mode": "ask"
   }
   ```
   - `signals_dir` = the same folder as the face's `bus_dir` (this is where
     backtalk writes `.voice_state` for the face to read).
   - `ptt_key` = the hold-to-talk key (default `home`).

4. Set the API key in the environment backtalk runs with:
   ```powershell
   $env:HERMES_API_URL = "http://127.0.0.1:8642/v1"
   $env:HERMES_API_KEY = "your-key"
   ```
   (Or set these as permanent user env vars so backtalk always picks them up.)
   - `HERMES_API_URL` — the Hermes API base
   - `HERMES_API_KEY` — the key from Part 1

5. Launch backtalk:
   ```powershell
   uv run python -m backtalk.main
   ```
   First run downloads the Whisper STT + Kokoro TTS models (a few minutes).
   It will WARM UP with a short query to the brain.

---

## Part 4 — Talk!

1. Face is running, browser showing the board (`http://127.0.0.1:8790/faces/board/`).
2. backtalk is running in a terminal window.
3. **Hold the Home key** and speak. Release.
4. The board should show:
   - **LISTENING** while you hold the mic
   - **THINKING** while Hermes generates (full-speed "storm" + scrambling chip)
   - **SPEAKING** while the reply plays through your speakers
   - **IDLE** when done

Your spoken words are transcribed (Whisper), sent to Hermes' API, the reply is
spoken back (Kokoro), and the face follows the whole time — all local.

---

## Troubleshooting

- **API not starting (`:8642` closed)** — the key is missing/too short
  (<16 chars) or the gateway wasn't restarted. Set a long key + restart gateway.
- **Board stuck on IDLE while backtalk answers** — backtalk's `signals_dir`
  doesn't match the face's `bus_dir`, or backtalk isn't loading the shim
  (check the `main.py` import line). Both must point at the SAME folder.
- **Second backtalk steals the mic/keys** — close ALL old backtalk windows
  before launching a new one. Two instances conflict.
- **No voice heard** — first run downloads models; check the terminal output.
  Ensure your mic is the default input device.
- **Microphone list** — if backtalk can't find your mic, run
  `uv run python -m backtalk.main` and look for its device help, or check the
  backtalk README's Windows notes.

---

## Credits

This stack is built on open work by **Jared Rhodenizer** ([@jaredrhod](https://github.com/jaredrhod)):

- **backtalk** (`github.com/jaredrhod/backtalk`) — the ears (Whisper STT),
  mouth (Kokoro TTS), and push-to-talk voice loop. We only swapped its brain
  to Hermes via `scripts/hermes_brain.py`; the voice/keyboard/personality
  code is entirely his.
- **ai-visualizer** (`github.com/jaredrhod/ai-visualizer`) — the animated
  "face" (the live circuit-board), and the `.voice_state` / `.voice_waveform`
  signal-bus convention it animates from.
- These are part of his larger **fullstack-agent** project
  (`github.com/jaredrhod/fullstack-agent`), which assembles memory, voice,
  face, and hands into one agent. This repo is a rewire of that stack so the
  "brain" runs on **Hermes** instead of Claude, for a single Windows box.

backtalk and ai-visualizer carry their own licenses (AGPL-3.0; see their
repos). This tutorial repo is MIT-licensed (see `LICENSE`). Please respect
the original projects' licensing.

## What backs this up (honest engineering notes)

- The only Claude-specific part of backtalk was its `brain.py`; swapping one
  import redirects all of backtalk's voice/keyboard/personality to Hermes.
- Everything uses Hermes' standard OpenAI-compatible endpoint — no private
  hooks, no custom protocols.
- No secrets ship in this repo: the key is generated and set by the operator.
- On a single box the face state is written directly by backtalk; the network
  relay I use on a homelab split-brain setup is NOT needed here (but the
  concept is described in `docs/relay-option.md` if you ever split machines).

See `docs/relay-option.md` for the optional network-relay variant (Hermes on a
server, face/voice on a client). See `LICENSE` for terms.
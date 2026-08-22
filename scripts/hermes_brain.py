"""
hermes_brain.py — drop-in replacement for backtalk.brain.WarmBrain that drives
HERMES (your agent) via its OpenAI-compatible API instead of Claude.

SINGLE-MACHINE LAYOUT
=====================
Everything runs on the same PC (backtalk + Hermes + the face). Backtalk's
*own* signals module writes .voice_state / .voice_waveform into its
"signals_dir". Point that at the SAME folder the visualizer reads as its
"bus_dir", and the face follows the conversation with perfect timing — no
networking, no relay.

The ONLY brain change here: ask_stream talks to Hermes' /v1/chat/completions
instead of Claude's SDK. That's it.
"""
import asyncio
import json
import os
import uuid

import httpx

from backtalk.config import CFG, DISCIPLINE
from backtalk.vlog import log

API_URL = os.environ.get("HERMES_API_URL", "http://localhost:8642/v1").rstrip("/")
API_KEY = os.environ.get("HERMES_API_KEY", "")
MODEL = os.environ.get("HERMES_MODEL", "hermes")


def _repo_dir() -> str:
    here = os.path.dirname(os.path.abspath(__file__))
    return os.path.abspath(os.path.join(here, "..", ".."))


def _session_id() -> str:
    """Return a STABLE session id so every turn continues the SAME Hermes
    conversation instead of starting fresh. Persisted to a file so it survives
    backtalk restarts."""
    sid_file = os.path.join(_repo_dir(), ".hermes_session_id")
    try:
        with open(sid_file) as f:
            sid = f.read().strip()
        if sid:
            return sid
    except OSError:
        pass
    sid = f"backtalk-{uuid.uuid4().hex[:16]}"
    try:
        with open(sid_file, "w") as f:
            f.write(sid)
    except OSError as e:
        log(f"[hermes-brain] could not persist session id: {e}")
    log(f"[hermes-brain] new conversation session: {sid}")
    return sid


class WarmBrain:
    def __init__(self, model=None, can_use_tool=None, resume_id=None, **kw):
        self.model = model or MODEL
        self.session = {"turns": 0, "out_tokens": 0, "in_tokens": 0, "cost": 0.0}
        self._dirty = False
        self._client = httpx.AsyncClient(timeout=120)

    async def start(self):
        log(f"[hermes-brain] targeting Hermes at {API_URL} model={self.model}")

    @staticmethod
    def _headers():
        h = {"Content-Type": "application/json"}
        if API_KEY:
            h["Authorization"] = f"Bearer {API_KEY}"
            # Continue the SAME Hermes conversation on every turn.
            h["X-Hermes-Session-Id"] = _session_id()
        return h

    async def ask_stream(self, utterance: str):
        """Stream Hermes' reply sentence-by-sentence. The face is driven by
        backtalk's native signals (listening/thinking/speaking), which write
        straight to the shared signals_dir/bus_dir."""
        self._dirty = True
        body = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": DISCIPLINE},
                {"role": "user", "content": utterance},
            ],
            "stream": True,
        }
        buf = ""
        try:
            async with self._client.stream(
                "POST", f"{API_URL}/chat/completions",
                json=body, headers=self._headers(),
            ) as resp:
                if resp.status_code != 200:
                    detail = (await resp.aread()).decode(errors="replace")[:120]
                    log(f"[brain] HTTP {resp.status_code}: {detail}")
                    yield "Sorry, the brain is not responding right now."
                    self._dirty = False
                    return
                async for line in resp.aiter_lines():
                    if not line.startswith("data:"):
                        continue
                    payload = line[5:].strip()
                    if payload == "[DONE]":
                        break
                    try:
                        obj = json.loads(payload)
                    except Exception:
                        continue
                    delta = ((obj.get("choices") or [{}])[0]
                             .get("delta", {}).get("content") or "")
                    if delta:
                        buf += delta
                        if any(c in buf for c in ".!?\n") and len(buf) >= 8:
                            out = buf.strip()
                            if out:
                                yield out
                            buf = ""
                if buf.strip():
                    yield buf.strip()
        except Exception as e:
            log(f"[brain] error: {e}")
            yield "I could not reach the brain."
        self.session["turns"] += 1
        self._dirty = False

    async def command(self, cmd: str) -> str:
        try:
            chunks = []
            async for s in self.ask_stream(cmd):
                chunks.append(s)
            return " ".join(chunks)
        except Exception as e:
            return f"error: {e}"

    async def interrupt(self):
        self._dirty = False

    async def reset_turn(self, timeout: float = 8.0):
        self._dirty = False

    async def set_permission_mode(self, mode: str):
        return

    async def context_usage(self):
        return None

    async def stop(self):
        await self._client.aclose()
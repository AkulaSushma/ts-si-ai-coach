"""GLM extraction client (SPEC-KNW-001 §4.3).

- Provider, model and key come from config/model_routing.json + environment.
  No key or URL is ever hard-coded here (D-0005, config rules).
- The HTTP path exists for the future live run, but tests NEVER use it: they
  inject FakeClient instances. A live call with no GLM_API_KEY raises
  MissingKeyError — reported honestly, never faked.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
ROUTING_PATH = ROOT / "config" / "model_routing.json"

EXTRACTION_ROLE = "KNOWLEDGE_EXTRACTION"
DEFAULT_TIMEOUT_SECONDS = 120


class MissingKeyError(RuntimeError):
    """GLM_API_KEY is not set in the environment."""


class ExtractionTransportError(RuntimeError):
    """The model call failed at transport level after retries."""


class GlmClient:
    """Thin, injectable client. extract(processed) returns a validated
    ExtractionResult or raises."""

    def __init__(self, *, prompt_version: str | None = None,
                 timeout: int = DEFAULT_TIMEOUT_SECONDS):
        from .prompts import CURRENT_PROMPT_VERSION, get_prompt

        self.prompt_version = prompt_version or CURRENT_PROMPT_VERSION
        self._build_messages = get_prompt(self.prompt_version)
        self.timeout = timeout
        cfg = json.loads(ROUTING_PATH.read_text(encoding="utf-8"))
        role = cfg["roles"][EXTRACTION_ROLE]
        self.provider = role["provider"]
        prov = cfg["providers"][self.provider]
        self.model = prov["model"]
        self.api_key_env = prov["api_key_env"]
        self.base_url_env = prov.get("base_url_env")
        self._cache: dict[str, str] = {}   # request-hash -> response JSON

    # ---------------------------------------------------------- plumbing

    def _base_url(self) -> str:
        url = os.environ.get(self.base_url_env) if self.base_url_env else None
        return url or "https://api.z.ai/api/paas/v4"

    def _api_key(self) -> str:
        key = os.environ.get(self.api_key_env)
        if not key:
            raise MissingKeyError(
                f"{self.api_key_env} is not set; a live GLM call is impossible "
                "and will not be simulated"
            )
        return key

    def _raw_call(self, messages: list[dict]) -> str:
        payload = json.dumps({
            "model": self.model,
            "messages": messages,
            "temperature": 0.1,
        }).encode("utf-8")
        req = urllib.request.Request(
            self._base_url().rstrip("/") + "/chat/completions",
            data=payload,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self._api_key()}",
            },
            method="POST",
        )
        last: Exception | None = None
        for attempt in range(1, 4):
            try:
                with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                    body = json.loads(resp.read().decode("utf-8"))
                return body["choices"][0]["message"]["content"]
            except (urllib.error.URLError, TimeoutError, KeyError,
                    IndexError, json.JSONDecodeError) as e:
                last = e
        raise ExtractionTransportError(
            f"GLM call failed after 3 attempts: {last}"
        )

    # ------------------------------------------------------------ public

    def extract(self, processed, *, cache_dir: Path | None = None):
        """One processed record -> ExtractionResult (validated).

        `cache_dir` enables the model-call cache: the exact request is hashed
        and a prior response is reused, so identical content+prompt never
        costs a second call (SPEC-KNW-001 §9).
        """
        from .extraction_schema import validate_extraction

        messages = self._build_messages(processed)
        import hashlib
        key = hashlib.sha256(
            json.dumps([messages, self.prompt_version, self.model],
                       sort_keys=True).encode()
        ).hexdigest()

        content = self._cache.get(key)
        if content is None:
            content = self._raw_call(messages)
            self._cache[key] = content
            if cache_dir is not None:
                cache_dir.mkdir(parents=True, exist_ok=True)
                (cache_dir / f"{key}.json").write_text(
                    json.dumps({"request_hash": key,
                                "prompt_version": self.prompt_version,
                                "model": self.model,
                                "response": content}, indent=2),
                    encoding="utf-8",
                )

        try:
            parsed = json.loads(content)
        except json.JSONDecodeError as e:
            from .extraction_schema import ExtractionSchemaError
            raise ExtractionSchemaError(f"$.json: model returned invalid JSON ({e})") from None
        return validate_extraction(parsed)

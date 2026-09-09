"""Telugu-capable Whisper-class ASR adapter (SPEC-INT-014).

The Session 013 pipeline ships no ASR engine, so every asr stage is BLOCKED.
This module adds a local, offline, Whisper-class adapter. It is deliberately
fail-closed: if no backend package is installed the adapter reports itself
unavailable and the pipeline records BLOCKED instead of inventing speech.

No cloud or external processing service is used. Supported backends, in order
of preference, are `faster_whisper` (CTranslate2) and `whisper` (reference
OpenAI implementation). Both run locally against a downloaded model.

Language handling rules enforced here:
- A requested 'te' or 'en' hint is passed to the engine as that language.
- A 'mixed' or 'und' hint lets the engine auto-detect, and the detected label
  is preserved separately in `detected_language`.
- The emitted `language` label is normalised to the project vocabulary
  ('te', 'en', 'mixed', 'und'). A detected language outside that vocabulary
  becomes 'und' rather than being coerced into Telugu or English.
- Text is emitted verbatim. Nothing is translated, corrected or dropped here.
  Low-confidence segments are returned unchanged; the pipeline flags them.
"""
from __future__ import annotations

import importlib
import math
import os

try:
    from .video_pipeline import (AdapterRegistry, AsrAdapter,
                                 CapabilityUnavailable, TesseractOcrAdapter)
except ImportError:  # direct execution
    from video_pipeline import (AdapterRegistry, AsrAdapter,
                                CapabilityUnavailable, TesseractOcrAdapter)

BACKENDS = ('faster_whisper', 'whisper')
DEFAULT_MODEL = os.environ.get('SI_WHISPER_MODEL', 'small')
HINT_TO_ENGINE = {'te': 'te', 'en': 'en', 'mixed': None, 'und': None}
ENGINE_TO_LABEL = {'te': 'te', 'en': 'en'}


def _module(name):
    try:
        return importlib.import_module(name)
    except Exception:
        return None


def _confidence(avg_logprob, no_speech_prob=None):
    """Map engine log-probability to a 0..1 confidence.

    This is a monotonic transform of the engine's own score, not an
    independent accuracy estimate. It is only used to flag low-confidence
    evidence, never to discard it.
    """
    if avg_logprob is None:
        return 0.0
    try:
        value = math.exp(float(avg_logprob))
    except (OverflowError, TypeError, ValueError):
        return 0.0
    if no_speech_prob is not None:
        try:
            value *= max(0.0, 1.0 - float(no_speech_prob))
        except (TypeError, ValueError):
            pass
    return max(0.0, min(1.0, value))


class WhisperAsrAdapter(AsrAdapter):
    """Local Whisper-class ASR. Unavailable unless a backend is installed."""

    name = 'whisper'
    languages = ('te', 'en', 'mixed', 'und')

    def __init__(self, model_size=DEFAULT_MODEL, backend=None, loader=None,
                 compute_type='int8'):
        self.model_size = model_size
        self.compute_type = compute_type
        self._loader = loader
        self._model = None
        self.backend = backend if backend is not None else self._detect()
        self.version = '{}:{}'.format(self.backend or 'unavailable', model_size)

    def _detect(self):
        if self._loader is not None:
            return 'injected'
        for candidate in BACKENDS:
            if _module(candidate) is not None:
                return candidate
        return None

    def available(self, language_hint=None):
        if self.backend is None:
            return False
        return language_hint is None or language_hint in self.languages

    def load(self):
        if self._model is not None:
            return self._model
        if self._loader is not None:
            self._model = self._loader(self.model_size)
        elif self.backend == 'faster_whisper':
            module = _module('faster_whisper')
            if module is None:
                raise CapabilityUnavailable('faster_whisper is not importable')
            self._model = module.WhisperModel(self.model_size,
                                              compute_type=self.compute_type)
        elif self.backend == 'whisper':
            module = _module('whisper')
            if module is None:
                raise CapabilityUnavailable('whisper is not importable')
            self._model = module.load_model(self.model_size)
        else:
            raise CapabilityUnavailable(
                'No Whisper-class ASR backend installed; tried ' + ', '.join(BACKENDS))
        return self._model

    def _raw_segments(self, model, audio_path, engine_language):
        if self.backend == 'faster_whisper':
            segments, info = model.transcribe(str(audio_path),
                                              language=engine_language,
                                              vad_filter=False)
            detected = getattr(info, 'language', None)
            out = []
            for seg in segments:
                out.append({'start': getattr(seg, 'start', None),
                            'end': getattr(seg, 'end', None),
                            'text': getattr(seg, 'text', ''),
                            'avg_logprob': getattr(seg, 'avg_logprob', None),
                            'no_speech_prob': getattr(seg, 'no_speech_prob', None),
                            'detected': detected})
            return out
        result = model.transcribe(str(audio_path), language=engine_language,
                                  task='transcribe')
        detected = result.get('language') if isinstance(result, dict) else None
        raw = result.get('segments', []) if isinstance(result, dict) else []
        out = []
        for seg in raw:
            out.append({'start': seg.get('start'), 'end': seg.get('end'),
                        'text': seg.get('text', ''),
                        'avg_logprob': seg.get('avg_logprob'),
                        'no_speech_prob': seg.get('no_speech_prob'),
                        'detected': seg.get('language') or detected})
        return out

    def transcribe(self, audio_path, language_hint=None):
        if self.backend is None:
            raise CapabilityUnavailable(
                'No Whisper-class ASR backend installed; tried ' + ', '.join(BACKENDS))
        if language_hint is not None and language_hint not in self.languages:
            raise CapabilityUnavailable('Unsupported language hint: ' + str(language_hint))
        engine_language = HINT_TO_ENGINE.get(language_hint or 'und')
        model = self.load()
        segments = []
        for raw in self._raw_segments(model, audio_path, engine_language):
            text = (raw.get('text') or '').strip()
            if not text:
                # An empty segment is not evidence. Skip it rather than
                # emitting a span with no observable content.
                continue
            detected = raw.get('detected')
            label = ENGINE_TO_LABEL.get(detected)
            if label is None:
                label = language_hint if language_hint in ('te', 'en') else 'und'
            segments.append({
                'start': raw.get('start'),
                'end': raw.get('end'),
                'text': text,
                'language': label,
                'detected_language': detected,
                'confidence': _confidence(raw.get('avg_logprob'),
                                          raw.get('no_speech_prob')),
            })
        return segments


def local_registry(model_size=DEFAULT_MODEL, asr=None, ocr=None):
    """Registry for a real local checkout: tesseract OCR + Whisper ASR.

    Both adapters decide their own availability from the actual environment,
    so a missing engine or missing language pack still produces BLOCKED.
    """
    registry = AdapterRegistry()
    registry.register_ocr(ocr if ocr is not None else TesseractOcrAdapter())
    registry.register_asr(asr if asr is not None else WhisperAsrAdapter(model_size))
    return registry


def capability_snapshot(registry=None):
    """Describe what the environment can actually do, without guessing."""
    registry = registry or local_registry()
    snapshot = {}
    for language in ('te', 'en', 'mixed'):
        asr = registry.asr(language)
        ocr = registry.ocr(language)
        snapshot[language] = {
            'asr': None if asr is None else {'name': asr.name, 'version': asr.version},
            'ocr': None if ocr is None else {'name': ocr.name, 'version': ocr.version},
        }
    return snapshot

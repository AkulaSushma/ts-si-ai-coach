"""Versioned prompt registry. Adding a prompt version means adding a module
here and bumping CURRENT — old candidates keep their version label."""

from .knowledge_extraction_v1 import PROMPT_VERSION as V1, build_messages

PROMPT_VERSIONS = {V1: build_messages}
CURRENT_PROMPT_VERSION = V1


def get_prompt(version: str):
    try:
        return PROMPT_VERSIONS[version]
    except KeyError:
        raise ValueError(
            f"unknown prompt version {version!r}; known: {sorted(PROMPT_VERSIONS)}"
        ) from None

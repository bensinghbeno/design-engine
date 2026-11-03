#!/usr/bin/env python3
"""Ask OpenRouter (https://openrouter.ai) a question and print the assistant's reply.

The API key is read from the ``OPENROUTER_API_KEY`` environment variable so it is
never stored in this file. Example::

    export OPENROUTER_API_KEY="sk-or-v1-..."
    python3 openrouter_ask.py "What is the meaning of life?"

The script mirrors this curl request::

    curl https://openrouter.ai/api/v1/chat/completions \\
      -H "Content-Type: application/json" \\
      -H "Authorization: Bearer $OPENROUTER_API_KEY" \\
      -d '{
        "model": "openai/gpt-4o",
        "messages": [
          { "role": "user", "content": "What is the meaning of life?" }
        ]
      }'

It is useful in this actuator-angle-sensing project to ask the model to interpret
an AS5600 raw angle, e.g.::

    python3 openrouter_ask.py --angle 127.5 \
      "The AS5600 reads {angle} deg. What actuator position does that indicate?"
"""

import argparse
import json
import os
import sys
from typing import Optional

import requests

API_BASE = "https://openrouter.ai/api/v1/chat/completions"
DEFAULT_MODEL = "openai/gpt-4o"

# ⚠️ SECURITY: Your OpenRouter API key is embedded below as a convenience default.
# The OPENROUTER_API_KEY environment variable (or --api-key) takes precedence.
# Do NOT commit this file to git / share it, since the key can be used to spend
# your credits. Prefer: export OPENROUTER_API_KEY="sk-or-v1-..."
EMBEDDED_API_KEY = ""


def load_api_key(explicit_key: Optional[str]) -> str:
    """Resolve the OpenRouter API key from an argument, env var, or embedded default."""
    key = (
        explicit_key
        or os.environ.get("OPENROUTER_API_KEY", "").strip()
        or EMBEDDED_API_KEY.strip()
    )
    if not key:
        sys.stderr.write(
            "Error: OpenRouter API key not provided. Set the OPENROUTER_API_KEY "
            "environment variable or pass --api-key.\n"
        )
        raise SystemExit(2)
    return key


def ask_openrouter(
    message: str,
    model: str = DEFAULT_MODEL,
    api_key: Optional[str] = None,
    temperature: float = 0.7,
    max_tokens: int = 1000,
) -> str:
    """Send a single user message to OpenRouter and return the assistant's text."""
    key = load_api_key(api_key)
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {key}",
    }
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": message}],
        "temperature": temperature,
        "max_tokens": max_tokens,
    }

    try:
        response = requests.post(API_BASE, headers=headers, json=payload, timeout=60)
    except requests.RequestException as exc:
        raise RuntimeError(f"Network error calling OpenRouter: {exc}") from exc

    if response.status_code == 401:
        raise RuntimeError("OpenRouter returned 401 Unauthorized - check your API key.")
    if response.status_code == 402:
        raise RuntimeError(
            "OpenRouter returned 402 - this key needs more credits, or fewer "
            "max_tokens. Top up at https://openrouter.ai/settings/credits "
            "or lower --max-tokens."
        )
    if response.status_code != 200:
        raise RuntimeError(
            f"OpenRouter returned HTTP {response.status_code}: {response.text}"
        )

    data = response.json()
    try:
        return data["choices"][0]["message"]["content"].strip()
    except (KeyError, IndexError, TypeError) as exc:
        raise RuntimeError(f"Unexpected OpenRouter response: {data}") from exc


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "message",
        nargs="?",
        help="User message to send. If omitted with --angle, a default "
        "actuator-position prompt is built from the angle.",
    )
    parser.add_argument(
        "--model",
        default=DEFAULT_MODEL,
        help=f"OpenRouter model to use (default: {DEFAULT_MODEL}).",
    )
    parser.add_argument(
        "--api-key",
        default=None,
        help="OpenRouter API key (defaults to OPENROUTER_API_KEY env var).",
    )
    parser.add_argument(
        "--angle",
        type=float,
        default=None,
        help="AS5600 actuator angle in degrees to interpolate into the prompt.",
    )
    parser.add_argument(
        "--temperature",
        type=float,
        default=0.7,
        help="Sampling temperature (default: 0.7).",
    )
    parser.add_argument(
        "--max-tokens",
        type=int,
        default=1000,
        help="Maximum tokens in the reply (default: 1000).",
    )
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.message is None and args.angle is None:
        parser.error("Provide a message, or --angle to build a default prompt.")

    if args.message is None:
        args.message = (
            f"The AS5600 magnetic encoder reads {args.angle} degrees of actuator "
            "rotation. What physical actuator position does that indicate, and "
            "what should I check next?"
        )
    elif args.angle is not None:
        args.message = args.message.replace("{angle}", str(args.angle))

    try:
        reply = ask_openrouter(
            message=args.message,
            model=args.model,
            api_key=args.api_key,
            temperature=args.temperature,
            max_tokens=args.max_tokens,
        )
    except (RuntimeError, SystemExit):
        raise
    except Exception as exc:  # pragma: no cover - defensive
        sys.stderr.write(f"Error: {exc}\n")
        raise SystemExit(1)

    print(reply)


if __name__ == "__main__":
    main()

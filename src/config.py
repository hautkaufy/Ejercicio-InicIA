"""Configuración."""

import os
from dataclasses import dataclass

from dotenv import load_dotenv

# Carga .env local sin reemplazar variables definidas en el entorno de ejecución.
load_dotenv(override=False)

DEFAULT_MODEL = "gpt-4o-mini"


@dataclass(frozen=True)
class Settings:
    api_key: str
    model: str


def get_settings() -> Settings:
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError(
            "Configurar OPENAI_API_KEY."
        )

    model = os.getenv("OPENAI_MODEL", DEFAULT_MODEL).strip()
    if not model or len(model) > 100:
        raise RuntimeError("OPENAI_MODEL no tiene un valor válido.")
    return Settings(api_key=api_key, model=model)

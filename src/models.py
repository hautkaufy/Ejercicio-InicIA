"""Esquemas y validación de entradas y resultados de generación."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ProductInput(BaseModel):
    """Datos del usuario con límites para mantener las solicitudes acotadas."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    product_name: str = Field(min_length=1, max_length=120)
    category: str = Field(min_length=1, max_length=100)
    features: str = Field(min_length=1, max_length=1500)
    audience: str = Field(min_length=1, max_length=250)
    platform: Literal["Tienda en línea", "Red social"]
    tone: Literal["Profesional", "Casual", "Informativo"]

    @field_validator("product_name", "category", "features", "audience")
    @classmethod
    def reject_blank_text(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Este campo es obligatorio.")
        return value.strip()


class GeneratedContent(BaseModel):
    """Estructura que impone Structured Outputs y se vuelve a validar localmente."""

    model_config = ConfigDict(extra="forbid", strict=True)

    commercial_title: str
    short_description: str
    full_description: str
    highlighted_features: list[str]
    keywords: list[str]
    social_media_post: str
    additional_information: list[str]

    @field_validator(
        "commercial_title", "short_description", "full_description", "social_media_post"
    )
    @classmethod
    def required_text(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("El texto no puede estar vacío.")
        return value.strip()

    @field_validator("highlighted_features", "keywords", "additional_information")
    @classmethod
    def validate_text_lists(cls, values: list[str]) -> list[str]:
        if any(not isinstance(value, str) or not value.strip() for value in values):
            raise ValueError("La lista contiene un elemento inválido.")
        return [value.strip() for value in values]

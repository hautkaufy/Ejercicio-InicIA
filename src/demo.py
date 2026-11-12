"""Escenarios de demostración que no realizan llamadas externas."""

from src.content_generator import ContentGenerationError
from src.models import GeneratedContent, ProductInput

DEMO_SCENARIOS = ("Respuesta simulada", "Error de cuota (simulado)")


def generate_demo_content(product: ProductInput, scenario: str) -> GeneratedContent:
    """Devuelve contenido ficticio o simula el error de cuota mostrado por la app."""
    if scenario == "Error de cuota (simulado)":
        raise ContentGenerationError(
            "Se alcanzó un límite o la cuota disponible de OpenAI. "
            "Inténtalo más tarde o revisa tu cuenta. (Error simulado; no se llamó a OpenAI.)"
        )
    if scenario != "Respuesta simulada":
        raise ValueError("Escenario de demostración desconocido.")

    features = [
        item.strip(" .;\n\t")
        for item in product.features.replace(";", "\n").splitlines()
        if item.strip(" .;\n\t")
    ]
    if not features:
        features = [product.features]

    title = f"{product.product_name} para {product.audience}"
    return GeneratedContent(
        commercial_title=title,
        short_description=(
            f"{product.product_name} pertenece a la categoría {product.category} "
            f"y está dirigido a {product.audience}."
        ),
        full_description=(
            f"{product.product_name} es un producto de la categoría {product.category}. "
            f"Características proporcionadas: {product.features}"
        ),
        highlighted_features=features[:5],
        keywords=[product.category, product.audience],
        social_media_post=f"Conoce {product.product_name}: {product.features}",
        additional_information=[
            "Puedes añadir precio, materiales, dimensiones y disponibilidad si deseas incluirlos."
        ],
    )

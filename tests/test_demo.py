import unittest

from src.content_generator import ContentGenerationError
from src.demo import DEMO_SCENARIOS, generate_demo_content
from src.models import GeneratedContent, ProductInput


PRODUCT = ProductInput(
    product_name="Taza de Acero",
    category="Accesorios de cocina",
    features="Tapa con cierre; Mantiene la bebida caliente",
    audience="Personas que llevan cafe al trabajo",
    platform="Tienda en línea",
    tone="Profesional",
)


class DemoScenarioTests(unittest.TestCase):
    def test_success_scenario_returns_valid_structured_mock(self):
        result = generate_demo_content(PRODUCT, "Respuesta simulada")

        self.assertIsInstance(result, GeneratedContent)
        self.assertIn(PRODUCT.product_name, result.commercial_title)
        self.assertEqual(
            result.highlighted_features,
            ["Tapa con cierre", "Mantiene la bebida caliente"],
        )
        self.assertTrue(result.additional_information)

    def test_quota_scenario_raises_the_ui_quota_message_without_api_call(self):
        with self.assertRaises(ContentGenerationError) as raised:
            generate_demo_content(PRODUCT, "Error de cuota (simulado)")

        self.assertIn("cuota", str(raised.exception).lower())
        self.assertIn("no se llamó a OpenAI", str(raised.exception))

    def test_rejects_unknown_scenario(self):
        with self.assertRaises(ValueError):
            generate_demo_content(PRODUCT, "escenario desconocido")

    def test_exposes_only_the_two_requested_scenarios(self):
        self.assertEqual(
            DEMO_SCENARIOS,
            ("Respuesta simulada", "Error de cuota (simulado)"),
        )


if __name__ == "__main__":
    unittest.main()

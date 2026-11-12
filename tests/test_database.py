import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

from src.database import (
    DATABASE_PATH,
    DatabaseError,
    delete_product,
    get_all_products,
    get_product,
    init_db,
    save_product,
)


PRODUCT = {
    "product_name": "Taza AceroPro",
    "category": "Accesorios de cocina",
    "features": "Tapa con cierre; capacidad indicada por el usuario",
    "audience": "Personas que llevan café al trabajo",
    "platform": "Tienda en línea",
    "tone": "Profesional",
}
CONTENT = {
    "commercial_title": "Taza AceroPro para llevar",
    "short_description": "Una taza para tu día.",
    "full_description": "Taza con las características indicadas por el usuario.",
    "highlighted_features": ["Tapa con cierre"],
    "keywords": ["taza", "café"],
    "social_media_post": "Conoce la Taza AceroPro.",
    "additional_information": ["Puedes añadir precio si deseas incluirlo."],
}


class DatabaseTests(unittest.TestCase):
    def setUp(self):
        self.temp_directory = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_directory.name) / "test_meshio.db"
        init_db(self.db_path)

    def tearDown(self):
        self.temp_directory.cleanup()

    def test_initialization_is_repeatable(self):
        init_db(self.db_path)
        connection = sqlite3.connect(self.db_path)
        try:
            tables = connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='products'"
            ).fetchall()
        finally:
            connection.close()
        self.assertEqual(len(tables), 1)

    def test_save_and_retrieve_persists_across_connections(self):
        record_id = save_product(PRODUCT, CONTENT, generation_key="generation-1", db_path=self.db_path)

        # Las funciones abren conexiones nuevas; el registro también sobrevive una reinicialización.
        init_db(self.db_path)
        retrieved = get_product(record_id, self.db_path)
        self.assertEqual(retrieved["product_name"], PRODUCT["product_name"])
        self.assertEqual(retrieved["features"], PRODUCT["features"])
        self.assertEqual(retrieved["generated_content"], CONTENT)
        self.assertTrue(retrieved["created_at"].endswith("Z"))
        self.assertEqual(get_all_products(self.db_path)[0]["id"], record_id)

    def test_get_all_orders_newest_first(self):
        older_id = save_product(PRODUCT, CONTENT, generation_key="older", db_path=self.db_path)
        newer_product = {**PRODUCT, "product_name": "Producto reciente"}
        newer_id = save_product(newer_product, CONTENT, generation_key="newer", db_path=self.db_path)
        records = get_all_products(self.db_path)
        self.assertEqual([item["id"] for item in records], [newer_id, older_id])

    def test_duplicate_generation_key_does_not_create_duplicate(self):
        first_id = save_product(PRODUCT, CONTENT, generation_key="same", db_path=self.db_path)
        second_id = save_product(PRODUCT, CONTENT, generation_key="same", db_path=self.db_path)
        self.assertEqual(first_id, second_id)
        self.assertEqual(len(get_all_products(self.db_path)), 1)

    def test_parameterized_values_are_stored_as_data(self):
        malicious_name = "x'); DROP TABLE products; --"
        product = {**PRODUCT, "product_name": malicious_name}
        record_id = save_product(product, CONTENT, generation_key="sql-input", db_path=self.db_path)
        self.assertEqual(get_product(record_id, self.db_path)["product_name"], malicious_name)
        self.assertEqual(len(get_all_products(self.db_path)), 1)

    def test_delete_existing_and_missing_records(self):
        record_id = save_product(PRODUCT, CONTENT, generation_key="delete-me", db_path=self.db_path)
        self.assertTrue(delete_product(record_id, self.db_path))
        self.assertFalse(delete_product(record_id, self.db_path))
        self.assertIsNone(get_product(record_id, self.db_path))

    def test_invalid_record_id_is_rejected(self):
        with self.assertRaises(ValueError):
            get_product("1; DROP TABLE products", self.db_path)

    def test_sqlite_errors_are_wrapped_without_raw_details(self):
        with self.assertRaises(DatabaseError) as raised:
            get_all_products(Path(self.temp_directory.name) / "missing" / "database.db")
        self.assertIn("historial", str(raised.exception))
        self.assertNotIn("unable to open", str(raised.exception))

    def test_default_database_is_stable_and_ignored(self):
        self.assertEqual(DATABASE_PATH.name, "meshio.db")
        self.assertEqual(DATABASE_PATH.parent, Path(__file__).resolve().parents[1])


if __name__ == "__main__":
    unittest.main()



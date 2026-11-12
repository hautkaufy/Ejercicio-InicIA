"""Persistencia SQLite de generaciones comerciales."""

from contextlib import contextmanager
import json
import logging
from pathlib import Path
import sqlite3
from typing import Any, Iterator

from pydantic import ValidationError

from src.models import GeneratedContent, ProductInput

logger = logging.getLogger(__name__)
DATABASE_PATH = Path(__file__).resolve().parent.parent / "meshio.db"


class DatabaseError(Exception):
    """Error de persistencia con mensaje seguro para mostrar en la interfaz."""


@contextmanager
def _connection(db_path: str | Path = DATABASE_PATH) -> Iterator[sqlite3.Connection]:
    connection: sqlite3.Connection | None = None
    try:
        connection = sqlite3.connect(str(db_path), timeout=5.0)
        connection.row_factory = sqlite3.Row
        yield connection
        connection.commit()
    except sqlite3.Error as exc:
        if connection is not None:
            connection.rollback()
        logger.warning("SQLite operation failed (%s)", type(exc).__name__)
        raise DatabaseError("No se pudo acceder al historial. Inténtalo de nuevo.") from None
    except Exception:
        if connection is not None:
            connection.rollback()
        raise
    finally:
        if connection is not None:
            connection.close()


def _validated_record(product: ProductInput | dict[str, Any], content: GeneratedContent | dict[str, Any]):
    try:
        validated_product = (
            product if isinstance(product, ProductInput) else ProductInput.model_validate(product)
        )
        validated_content = (
            content
            if isinstance(content, GeneratedContent)
            else GeneratedContent.model_validate(content)
        )
    except ValidationError:
        raise DatabaseError("Los datos del producto o del contenido no son válidos.") from None
    return validated_product, validated_content


def _validate_id(record_id: int) -> int:
    if isinstance(record_id, bool) or not isinstance(record_id, int) or record_id < 1:
        raise ValueError("El identificador debe ser un entero positivo.")
    return record_id


def init_db(db_path: str | Path = DATABASE_PATH) -> None:
    """Crea la tabla e índice si todavía no existen."""
    with _connection(db_path) as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                generation_key TEXT NOT NULL UNIQUE,
                product_name TEXT NOT NULL,
                category TEXT NOT NULL,
                features TEXT NOT NULL,
                audience TEXT NOT NULL,
                platform TEXT NOT NULL,
                tone TEXT NOT NULL,
                generated_content_json TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
            )
            """
        )
        connection.execute(
            "CREATE INDEX IF NOT EXISTS idx_products_created_at ON products(created_at DESC, id DESC)"
        )


def save_product(
    product: ProductInput | dict[str, Any],
    content: GeneratedContent | dict[str, Any],
    *,
    generation_key: str,
    db_path: str | Path = DATABASE_PATH,
) -> int:
    """Guarda la generación una sola vez por clave idempotente y devuelve su id."""
    validated_product, validated_content = _validated_record(product, content)
    if not isinstance(generation_key, str) or not generation_key.strip() or len(generation_key) > 128:
        raise ValueError("La clave de generación no es válida.")

    product_values = validated_product.model_dump(mode="python")
    content_json = json.dumps(
        validated_content.model_dump(mode="json"), ensure_ascii=False, separators=(",", ":")
    )
    with _connection(db_path) as connection:
        connection.execute(
            """
            INSERT INTO products (
                generation_key, product_name, category, features, audience,
                platform, tone, generated_content_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(generation_key) DO NOTHING
            """,
            (
                generation_key.strip(),
                product_values["product_name"],
                product_values["category"],
                product_values["features"],
                product_values["audience"],
                product_values["platform"],
                product_values["tone"],
                content_json,
            ),
        )
        row = connection.execute(
            "SELECT id FROM products WHERE generation_key = ?", (generation_key.strip(),)
        ).fetchone()
        if row is None:
            raise DatabaseError("No se pudo confirmar el registro guardado.")
        return int(row["id"])


def _row_to_record(row: sqlite3.Row) -> dict[str, Any]:
    try:
        content = GeneratedContent.model_validate(json.loads(row["generated_content_json"]))
    except (json.JSONDecodeError, ValidationError, TypeError):
        logger.warning("SQLite contains invalid generated content")
        raise DatabaseError("Un registro del historial contiene datos inválidos.") from None

    return {
        "id": int(row["id"]),
        "product_name": row["product_name"],
        "category": row["category"],
        "features": row["features"],
        "audience": row["audience"],
        "platform": row["platform"],
        "tone": row["tone"],
        "generated_content": content.model_dump(mode="python"),
        "created_at": row["created_at"],
    }


def get_all_products(db_path: str | Path = DATABASE_PATH) -> list[dict[str, Any]]:
    """Recupera el historial, del más reciente al más antiguo."""
    with _connection(db_path) as connection:
        rows = connection.execute(
            """
            SELECT id, product_name, category, features, audience, platform, tone,
                   generated_content_json, created_at
            FROM products
            ORDER BY created_at DESC, id DESC
            """
        ).fetchall()
    return [_row_to_record(row) for row in rows]


def get_product(record_id: int, db_path: str | Path = DATABASE_PATH) -> dict[str, Any] | None:
    """Consulta un registro por identificador, o devuelve None si no existe."""
    record_id = _validate_id(record_id)
    with _connection(db_path) as connection:
        row = connection.execute(
            """
            SELECT id, product_name, category, features, audience, platform, tone,
                   generated_content_json, created_at
            FROM products WHERE id = ?
            """,
            (record_id,),
        ).fetchone()
    return _row_to_record(row) if row is not None else None


def delete_product(record_id: int, db_path: str | Path = DATABASE_PATH) -> bool:
    """Elimina el registro indicado y devuelve si existía."""
    record_id = _validate_id(record_id)
    with _connection(db_path) as connection:
        cursor = connection.execute("DELETE FROM products WHERE id = ?", (record_id,))
        return cursor.rowcount > 0

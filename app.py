import os
import uuid

import streamlit as st
from pydantic import ValidationError

from src.content_generator import (
    ContentGenerationError,
    InvalidResponseError,
    MissingAPIKeyError,
    generate_content,
)
from src.database import (
    DatabaseError,
    delete_product,
    get_all_products,
    get_product,
    init_db,
    save_product,
)
from src.demo import DEMO_SCENARIOS, generate_demo_content
from src.models import ProductInput

st.set_page_config(
    page_title="Merch.io",
    layout="centered",
)


def render_generated_sections(result):
    """Muestra texto generado como texto plano y con encabezados fijos."""
    st.markdown("#### Título comercial")
    st.text(result["commercial_title"])
    st.markdown("#### Descripción corta")
    st.text(result["short_description"])
    st.markdown("#### Descripción completa")
    st.text(result["full_description"])
    st.markdown("#### Características destacadas")
    for feature in result["highlighted_features"]:
        st.text(f"• {feature}")
    st.markdown("#### Palabras clave")
    st.text(", ".join(result["keywords"]))
    st.markdown("#### Publicación para redes sociales")
    st.text(result["social_media_post"])
    st.markdown("#### Información adicional conveniente")
    if result["additional_information"]:
        for information in result["additional_information"]:
            st.text(f"• {information}")
    else:
        st.text("No se identificó información adicional necesaria.")


st.title("Merch.io")
st.write(
    "Ingresa la información de tu producto para preparar contenido comercial "
    "adaptado a tu negocio y público."
)

try:
    init_db()
    database_ready = True
except DatabaseError as exc:
    database_ready = False
    st.error(f"El historial no está disponible: {exc}")

demo_mode = os.getenv("APP_DEMO_MODE", "false").strip().lower() in {"1", "true", "yes", "on"}
demo_scenario = None
if demo_mode:
    st.sidebar.info("Modo de demostración activo: no se realizarán llamadas a OpenAI.")
    demo_scenario = st.sidebar.selectbox("Escenario de prueba", DEMO_SCENARIOS)

with st.form("product_form"):
    st.subheader("Información del producto")

    product_name = st.text_input(
        "Nombre del producto *",
        placeholder="Ej. Taza térmica AceroPro",
        max_chars=120,
    )
    category = st.text_input(
        "Categoría *",
        placeholder="Ej. Accesorios para cocina",
        max_chars=100,
    )
    features = st.text_area(
        "Características principales *",
        placeholder="Describe las características reales del producto",
        help="Incluye solo especificaciones que conozcas y puedas confirmar.",
        max_chars=1500,
    )
    audience = st.text_input(
        "Público objetivo *",
        placeholder="Ej. Personas que llevan café al trabajo",
        max_chars=250,
    )

    st.subheader("Preferencias del contenido")
    platform = st.selectbox(
        "Plataforma *",
        options=["Tienda en línea", "Red social"],
    )
    tone = st.selectbox(
        "Tono *",
        options=["Profesional", "Casual", "Informativo"],
    )

    submitted = st.form_submit_button(
        "Generar contenido",
        type="primary",
        use_container_width=True,
    )

if submitted:
    try:
        product = ProductInput(
            product_name=product_name,
            category=category,
            features=features,
            audience=audience,
            platform=platform,
            tone=tone,
        )
    except ValidationError:
        st.error("Completa todos los campos obligatorios y revisa sus longitudes máximas.")
    else:
        try:
            with st.spinner("Generando contenido comercial…"):
                if demo_mode:
                    generated = generate_demo_content(product, demo_scenario)
                else:
                    generated = generate_content(product)
            st.session_state["generated_content"] = generated.model_dump(mode="python")
            st.session_state["generated_product"] = product.model_dump(mode="python")
            st.session_state["generation_key"] = uuid.uuid4().hex
            st.success("Contenido generado correctamente.")
        except MissingAPIKeyError as exc:
            st.error(str(exc))
        except (ContentGenerationError, InvalidResponseError) as exc:
            st.error(str(exc))

result = st.session_state.get("generated_content")
if result:
    st.subheader("Contenido generado")
    render_generated_sections(result)

    generation_key = st.session_state.get("generation_key")
    generated_product = st.session_state.get("generated_product")
    saved_generations = st.session_state.setdefault("saved_generations", {})
    is_saved = bool(generation_key and generation_key in saved_generations)
    if is_saved:
        st.success("Este resultado ya está guardado en el historial.")
    elif not database_ready:
        st.button("Guardar en historial", disabled=True, key="save_unavailable")
    elif generated_product and generation_key:
        if st.button("Guardar en historial", key=f"save_{generation_key}"):
            try:
                record_id = save_product(
                    generated_product,
                    result,
                    generation_key=generation_key,
                )
                saved_generations[generation_key] = record_id
                st.success("Producto y contenido guardados en el historial.")
            except DatabaseError as exc:
                st.error(f"No se pudo guardar el producto: {exc}")

st.divider()
st.header("Historial de productos")
if database_ready:
    try:
        history = get_all_products()
    except DatabaseError as exc:
        st.error(f"No se pudo recuperar el historial: {exc}")
    else:
        if not history:
            st.info("Todavía no hay productos guardados.")
        else:
            record_by_id = {record["id"]: record for record in history}
            selected_id = st.selectbox(
                "Selecciona un producto guardado",
                options=list(record_by_id),
                format_func=lambda record_id: (
                    f"{record_by_id[record_id]['product_name']} · "
                    f"{record_by_id[record_id]['created_at']}"
                ),
                key="history_product_id",
            )
            try:
                selected_record = get_product(selected_id)
            except DatabaseError as exc:
                selected_record = None
                st.error(f"No se pudo abrir el registro: {exc}")

            if selected_record:
                st.caption(f"Guardado: {selected_record['created_at']} (UTC)")
                st.markdown("#### Datos originales del producto")
                st.text(f"Nombre: {selected_record['product_name']}")
                st.text(f"Categoría: {selected_record['category']}")
                st.text(f"Características: {selected_record['features']}")
                st.text(f"Público objetivo: {selected_record['audience']}")
                st.text(f"Plataforma: {selected_record['platform']}")
                st.text(f"Tono: {selected_record['tone']}")
                st.markdown("#### Contenido guardado")
                render_generated_sections(selected_record["generated_content"])

                pending_delete_id = st.session_state.get("pending_delete_product_id")
                if pending_delete_id == selected_id:
                    st.warning("¿Quieres eliminar este producto del historial?")
                    confirm_col, cancel_col = st.columns(2)
                    with confirm_col:
                        confirm_delete = st.button(
                            "Confirmar eliminación",
                            type="primary",
                            key=f"confirm_delete_{selected_id}",
                        )
                    with cancel_col:
                        cancel_delete = st.button("Cancelar", key=f"cancel_delete_{selected_id}")
                    if confirm_delete:
                        try:
                            delete_product(selected_id)
                            for key, saved_id in list(saved_generations.items()):
                                if saved_id == selected_id:
                                    saved_generations.pop(key, None)
                            st.session_state.pop("pending_delete_product_id", None)
                            st.success("El producto se eliminó del historial.")
                            st.rerun()
                        except DatabaseError as exc:
                            st.error(f"No se pudo eliminar el producto: {exc}")
                    elif cancel_delete:
                        st.session_state.pop("pending_delete_product_id", None)
                        st.rerun()
                elif st.button("Eliminar del historial", key=f"delete_{selected_id}"):
                    st.session_state["pending_delete_product_id"] = selected_id
                    st.rerun()
else:
    st.info("El historial no está disponible hasta que se recupere la conexión con SQLite.")

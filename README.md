# Merch.io

Prueba InicIA - Mauricio De La Fuente Herrera
Aplicacion web para que PyMEs generen contenido comercial con IA a partir de la información de sus productos. La app usa Streamlit, el SDK de OpenAI y SQLite.

Genera título, descripciones, características destacadas, palabras clave, publicación para redes e información adicional sugerida. Puedes guardar cada resultado y consultarlo o eliminarlo desde el historial.

## Problema y solucion
El problema seleccionado es la perdida de tiempo y recursos utilizados para que una empresa cree contenido para sus productos. Esta app permite a los usuarios utilizar datos sobre sus productos, y generar informacion y contenido mediante el uso de OpenAI que el usuario puede guardar para su uso en el futuro, sin la necesidad de escribir descripciones o palabras claves manualmente.

## Uso de los agentes
El proyecto fue divido en 3 partes, donde se utilizaron 3 prompts para la creacion de la app. Donde el primer prompt describe la implementacion de la interfac de usuario y el formulario, luego el segundo prompt se enfoca en la implementacion de OpenAI API con el formulario. Por ultimo, el tercer prompt se enfoca en la implementacion de SQLite para el guardado de contenido generado y un historial de generacion.

## Correciones de agentes y manuales
Los agentes se encargaron de implementar la interfaz y la conexion entre OpenAI y SQLite, mientras que manualmente se hicieron modificaciones al formulario y su formato, medidas de seguridad y proteccion de datos del usuario, y modificacion en el prompt utilizado para la generacion de contenido en la app.

## Mitigacion de riesgo
Algunos cambios realizados para poder mitigar riesgos en la app incluyen validaciones en los campos del formulario para evitar la ejecuccion de scripts y prompts, asi como tambien la validacion de datos y campos obligatorios para evitar que la IA genere respuestas inventadas. Tambien se realizaron cambios en el manejo de la API key de OpenAI para evitar difundir las llaves del agente tanto del proyecto, como dentro de la aplicacion web. Por ultimo, se realizaron consultas en el SQLite para evitar inyecciones externas y contenido malicioso.

## Requisitos y configuración
Instala dependencias y prepara la configuración local:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

## Ejecuccion

```powershell
streamlit run app.py
```

La base `meshio.db` se crea automáticamente en la carpeta del proyecto. Tras generar contenido, pulsa **Guardar en historial** para conservarlo.

## Pruebas

```powershell
python -m unittest discover -s tests -v
```
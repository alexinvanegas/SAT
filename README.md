# Aplicación para Procesar Archivos XML

Esta aplicación web permite a los usuarios cargar archivos ZIP que contienen archivos XML, los descomprime, procesa los archivos XML y genera un archivo Excel con los resultados.

## Requisitos

*   Python 3.x
*   Flask
*   pandas

## Instalación

1.  Clona el repositorio (si está en un repositorio).
2.  Navega al directorio del proyecto.
3.  Instala las dependencias:

    ```bash
    pip install flask pandas
    ```

## Uso

1.  Ejecuta la aplicación:

    ```bash
    python ProcesoSAT.py
    ```

2.  Abre tu navegador web y ve a `http://127.0.0.1:5000/` (o la dirección que Flask te indique).
3.  Carga un archivo ZIP que contenga archivos XML.
4.  Una vez que se procesen los archivos, se mostrará un enlace para descargar el archivo Excel generado.

## Estructura de Archivos

*   `ProcesoSAT.py`:  Archivo principal de la aplicación. Contiene el código de Flask y la lógica de procesamiento de XML.
*   `templates/index.html`:  Archivo HTML que contiene el formulario para cargar el archivo ZIP.
*   `XLS/`: Carpeta donde se guarda el archivo Excel generado.
*   `XML/`: Carpeta donde se descomprimen los archivos XML.

## Autor

[Alex]
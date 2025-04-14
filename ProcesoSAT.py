import os
import re
import xml.etree.ElementTree as ET
import pandas as pd
from flask import Flask, render_template, request, redirect, url_for, send_file, flash
import zipfile
import shutil


app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Needed for flash messages
# Usa la variable de entorno PORT, o por defecto el 8080
port = int(os.environ.get("PORT", 8080))
app.run(host='0.0.0.0', port=port)

# Variables globales para almacenar información del procesamiento
ultimo_excel_generado = None
ultimo_nit_receptor = None
total_archivos_procesados = 0

# Función para limpiar caracteres no válidos en los archivos XML
def limpiar_xml(xml_path):
    try:
        with open(xml_path, 'r', encoding='utf-8') as file:
            contenido = file.read()
    except UnicodeDecodeError:
        with open(xml_path, 'r', encoding='latin-1') as file:
            contenido = file.read()

    contenido = re.sub(r'&(?!amp;|lt;|gt;|apos;|quot;)', '&amp;', contenido)

    with open(xml_path, 'w', encoding='utf-8') as file:
        file.write(contenido)

# Ruta para la página de inicio
@app.route('/')
def index():
    return render_template('index.html')

# Ruta para manejar la carga del archivo ZIP
@app.route('/upload', methods=['POST'])
def upload():
    global ultimo_excel_generado, ultimo_nit_receptor, total_archivos_procesados
    
    if 'zip_file' not in request.files:
        flash('No se seleccionó ningún archivo', 'error')
        return redirect(url_for('index'))

    zip_file = request.files['zip_file']
    if zip_file.filename == '':
        flash('No se seleccionó ningún archivo', 'error')
        return redirect(url_for('index'))

    if zip_file:
        try:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            xml_folder = os.path.join(base_dir, 'XML')
            temp_folder = os.path.join(base_dir, 'temp_zip')

            # Preparar carpetas
            os.makedirs(xml_folder, exist_ok=True)
            os.makedirs(temp_folder, exist_ok=True)

            # Limpiar carpeta temporal
            for f in os.listdir(temp_folder):
                file_path = os.path.join(temp_folder, f)
                if os.path.isfile(file_path):
                    os.unlink(file_path)

            # Descomprimir ZIP en carpeta temporal
            with zipfile.ZipFile(zip_file, 'r') as zip_ref:
                zip_ref.extractall(temp_folder)

            # Procesar archivos y obtener el Excel generado
            output_excel, total_archivos, nit_receptor = procesar_directorio(temp_folder, xml_folder)

            # Guardar en variables globales
            ultimo_excel_generado = output_excel
            ultimo_nit_receptor = nit_receptor
            total_archivos_procesados = total_archivos

            # Limpiar carpeta temporal
            shutil.rmtree(temp_folder)

            # Redirección a la página de éxito
            return redirect(url_for('success'))

        except Exception as e:
            flash(f"Error al procesar el archivo: {str(e)}", 'error')
            return redirect(url_for('index'))

    return redirect(url_for('index'))

# Nueva ruta para la página de éxito
@app.route('/success')
def success():
    return render_template('success.html', 
                          total_archivos=total_archivos_procesados, 
                          nit_receptor=ultimo_nit_receptor)

# Ruta para descargar el archivo Excel generado
@app.route('/download')
def download():
    if ultimo_excel_generado and os.path.exists(ultimo_excel_generado):
        return send_file(ultimo_excel_generado, as_attachment=True)
    else:
        flash("Archivo no encontrado.", 'error')
        return redirect(url_for('index'))

# Nueva ruta para eliminar los archivos XML y XLS generados
@app.route('/delete_files')
def delete_files():
    global ultimo_excel_generado, ultimo_nit_receptor
    
    try:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        xml_folder = os.path.join(base_dir, 'XML')
        xls_folder = os.path.join(base_dir, 'XLS')
        
        # Eliminar archivos XML del receptor específico
        if ultimo_nit_receptor and ultimo_nit_receptor != "Desconocido":
            receptor_folder = os.path.join(xml_folder, ultimo_nit_receptor)
            if os.path.exists(receptor_folder):
                shutil.rmtree(receptor_folder)
        
        # Eliminar el archivo Excel generado
        if ultimo_excel_generado and os.path.exists(ultimo_excel_generado):
            os.remove(ultimo_excel_generado)
            ultimo_excel_generado = None
        
        flash("Archivos eliminados correctamente", 'success')
    except Exception as e:
        flash(f"Error al eliminar archivos: {str(e)}", 'error')
    
    return redirect(url_for('index'))

# Función para analizar un XML y extraer encabezados y detalles
def parse_xml(file_path):
    tree = ET.parse(file_path)
    root = tree.getroot()
    namespace = {'dte': 'http://www.sat.gob.gt/dte/fel/0.2.0'}

    encabezados = []
    detalles = []
    nit_receptor = "Desconocido"

    datos_emision = root.find('.//dte:DatosEmision', namespace)
    certificacion = root.find('.//dte:Certificacion', namespace)

    if datos_emision is not None and certificacion is not None:
        numero = certificacion.find('dte:NumeroAutorizacion', namespace).attrib.get('Numero')
        serie = certificacion.find('dte:NumeroAutorizacion', namespace).attrib.get('Serie')

        datos_generales = datos_emision.find('dte:DatosGenerales', namespace)
        emisor = datos_emision.find('dte:Emisor', namespace)
        receptor = datos_emision.find('dte:Receptor', namespace)
        totales = datos_emision.find('.//dte:GranTotal', namespace)

        nit_emisor = emisor.attrib.get('NITEmisor') if emisor is not None else ''
        nit_receptor = receptor.attrib.get('IDReceptor') if receptor is not None else 'Desconocido'

        encabezado = {
            'Numero': numero,
            'Serie': serie,
            'FechaHoraEmision': datos_generales.attrib.get('FechaHoraEmision') if datos_generales is not None else '',
            'Tipo': datos_generales.attrib.get('Tipo') if datos_generales is not None else '',
            'NombreEmisor': emisor.attrib.get('NombreEmisor') if emisor is not None else '',
            'NITEmisor': nit_emisor,
            'NombreReceptor': receptor.attrib.get('NombreReceptor') if receptor is not None else '',
            'IDReceptor': nit_receptor,
            'GranTotal': totales.text if totales is not None else '',
        }
        encabezados.append(encabezado)

        for item in datos_emision.findall('.//dte:Item', namespace):
            detalle = {
                'Numero': numero,
                'Serie': serie,
                'NITEmisor': nit_emisor,
                'IDReceptor': nit_receptor,
                'NumeroLinea': item.attrib.get('NumeroLinea'),
                'Descripcion': item.find('dte:Descripcion', namespace).text if item.find('dte:Descripcion', namespace) is not None else '',
                'Cantidad': item.find('dte:Cantidad', namespace).text if item.find('dte:Cantidad', namespace) is not None else '',
                'PrecioUnitario': item.find('dte:PrecioUnitario', namespace).text if item.find('dte:PrecioUnitario', namespace) is not None else '',
                'Total': item.find('dte:Total', namespace).text if item.find('dte:Total', namespace) is not None else '',
            }
            detalles.append(detalle)

    return encabezados, detalles, nit_receptor

# Función principal para procesar directorio
def procesar_directorio(origen_folder, destino_folder):
    todos_encabezados = []
    todos_detalles = []
    nit_receptor_unico = None
    total_archivos = 0

    for archivo in os.listdir(origen_folder):
        if archivo.endswith('.xml'):
            archivo_path = os.path.join(origen_folder, archivo)
            limpiar_xml(archivo_path)
            encabezados, detalles, nit_receptor = parse_xml(archivo_path)

            if nit_receptor != 'Desconocido':
                nit_receptor_unico = nit_receptor

                # Crear subcarpeta para NIT del receptor
                receptor_folder = os.path.join(destino_folder, nit_receptor)
                os.makedirs(receptor_folder, exist_ok=True)

                # Mover archivo XML al subdirectorio
                shutil.move(archivo_path, os.path.join(receptor_folder, archivo))

            todos_encabezados.extend(encabezados)
            todos_detalles.extend(detalles)
            total_archivos += 1

    if not nit_receptor_unico:
        nit_receptor_unico = "Desconocido"

    # Crear DataFrames combinados
    df_encabezados = pd.DataFrame(todos_encabezados)
    df_detalles = pd.DataFrame(todos_detalles)
    
    if not df_encabezados.empty:
        df_proveedores = df_encabezados[['NITEmisor', 'NombreEmisor']].drop_duplicates()
    else:
        df_proveedores = pd.DataFrame(columns=['NITEmisor', 'NombreEmisor'])

    # Preparar ruta de salida para el Excel
    output_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'XLS')
    os.makedirs(output_folder, exist_ok=True)
    output_excel = os.path.join(output_folder, f'resultados_combinados_{nit_receptor_unico}.xlsx')

    # Guardar Excel
    with pd.ExcelWriter(output_excel) as writer:
        df_encabezados.to_excel(writer, sheet_name='Encabezado', index=False)
        df_detalles.to_excel(writer, sheet_name='Detalle', index=False)
        df_proveedores.to_excel(writer, sheet_name='Proveedores', index=False)

    return output_excel, total_archivos, nit_receptor_unico

if __name__ == '__main__':
    app.run(debug=True)
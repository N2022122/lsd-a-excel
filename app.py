# ==========================
# 1. Instalar librerías necesarias (solo en Colab, comentar si no hace falta)
# ==========================
# !pip install pdfplumber pandas openpyxl

# ==========================
# 2. Importar librerías
# ==========================
import pdfplumber
import pandas as pd
import re
import os

# ==========================
# 3. Subir archivo PDF
# ==========================
print("📂 Selecciona el archivo PDF del Libro de Sueldos")
uploaded = files.upload()
pdf_path = list(uploaded.keys())[0]

# ==========================
# 4. Función para limpiar espacios
# ==========================
def limpiar_linea(line):
    return re.sub(r"\s+", " ", line).strip()

# ==========================
# 5. Procesar el PDF
# ==========================
empleados = []

with pdfplumber.open(pdf_path) as pdf:
    for page in pdf.pages:
        text = page.extract_text()

        # Eliminar info irrelevante
        text = re.sub(r"\*.*\*", "", text)  # códigos de barras
        text = re.sub(r"PAGINA\s+\d+\s+de\s+\d+", "", text)
        text = re.sub(r"IDENTIFICADOR UNICO DEL LIBRO.*", "", text)
        text = re.sub(r"LIBRO ESPECIAL DE SUELDOS Y\n JORNALES DE LA PROVINCIA \n DE CATAMARCA", "", text)
        text = re.sub(r"LEGAJO\s+CUIL\s+APELLIDO Y NOMBRE.*", "", text)
        text = re.sub(r"DOCUMENTO\s+FECHA NACIMIENTO.*", "", text)
        text = re.sub(r"NACIONALIDAD\s+CATEGORIA.*", "", text)
        text = re.sub(r"MODALIDAD DE CONTRATACION.*", "", text)
        text = re.sub(r"CONCEPTOS\s+PERIODO.*", "", text)

        lines = [limpiar_linea(l) for l in text.split("\n") if l.strip()]

        i = 0
        while i < len(lines):
            linea = lines[i]

            # Buscar si la línea comienza con un legajo y CUIL
            if re.match(r"^\d+\s+\d{2}-\d{8}-\d", linea):

                # --- EXTRAER DATOS DEL PRIMER RENGLÓN ---
                match_linea1 = re.match(r"(\d+)\s+(\d{2}-\d{8}-\d)\s+(.*?)\s+(\d{2}/\d{2}/\d{4})", linea)
                if match_linea1:
                    legajo = match_linea1.group(1)
                    cuil = match_linea1.group(2)
                    apellido_nombre = match_linea1.group(3).strip()
                    fecha_ingreso = match_linea1.group(4)

                    resto_linea1 = linea[match_linea1.end():].strip()

                    # Buscar Fecha Cese, Documento y Fecha de Nacimiento
                    match_resto = re.search(r"(\S+)\s+DNI\s+(\S+)\s+(\S+)", resto_linea1)
                    if match_resto:
                        fecha_cese = match_resto.group(1)
                        doc_num = match_resto.group(2)
                        fecha_nac = match_resto.group(3)
                    else:
                        fecha_cese = None
                        doc_num = None
                        fecha_nac = None

                    # Línea 2: Nacionalidad, Categoría y Obra Social
                    i += 1
                    linea2 = lines[i]
                    partes = linea2.split(maxsplit=1)
                    nacionalidad = partes[0]
                    resto_linea2 = partes[1]

                    match_obra_social = re.search(r'\s(\d+\s-\s.+)$', resto_linea2)
                    if match_obra_social:
                        obra_social = match_obra_social.group(1).strip()
                        categoria = resto_linea2[:match_obra_social.start()].strip()
                    else:
                        categoria = resto_linea2.strip()
                        obra_social = None

                    # Línea 3: Modalidad de Contratación, Convenio Colectivo y Puesto
                    i += 1
                    linea3 = lines[i]

                    patron_campos = r'^(\d+\s-\s.+?)\s+(\d+/\d+\s-\s.+?)\s+(\d+\s-\s.+?)$'
                    match_campos = re.search(patron_campos, linea3)

                    if match_campos:
                        modalidad_contratacion = match_campos.group(1).strip()
                        convenio_colectivo = match_campos.group(2).strip()
                        puesto = match_campos.group(3).strip()
                    else:
                        modalidad_contratacion = None
                        convenio_colectivo = None
                        puesto = None

                    empleados.append({
                        "Legajo": legajo,
                        "CUIL": cuil,
                        "Apellido y Nombre": apellido_nombre,
                        "Fecha Ingreso": fecha_ingreso,
                        "Fecha Cese": fecha_cese,
                        "Documento": doc_num,
                        "Fecha Nacimiento": fecha_nac,
                        "Nacionalidad": nacionalidad,
                        "Categoria": categoria,
                        "Obra Social": obra_social,
                        "Modalidad de Contratacion": modalidad_contratacion,
                        "Convenio Colectivo": convenio_colectivo,
                        "Puesto": puesto
                    })
            i += 1

# ==========================
# 6. Exportar a Excel y validar
# ==========================
df = pd.DataFrame(empleados)

print(f"👥 Total empleados extraídos: {len(empleados)}")
print("📋 Vista previa de datos extraídos:")
print(df.head())

# Obtener nombre de salida (mismo que PDF, pero en Excel)
carpeta_pdf = os.path.dirname(pdf_path)
nombre_base = os.path.splitext(os.path.basename(pdf_path))[0]
nombre_archivo = os.path.join(carpeta_pdf, f"{nombre_base}.xlsx")

# Guardar a Excel
df.to_excel(nombre_archivo, index=False)

print(f"✅ Archivo generado: {nombre_archivo}")

# Descargar (solo en Colab)
files.download(nombre_archivo)

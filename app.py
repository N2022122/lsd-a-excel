import streamlit as st
import pdfplumber
import pandas as pd
import re
import os
import io # Necesario para leer el archivo PDF subido en memoria

# Configuración de la aplicación Streamlit
st.title("Extractor de Datos de Libro de Sueldos PDF")
st.markdown("Sube tu archivo PDF para extraer la información.")

# ==========================
# 4. Función para limpiar espacios (Definida ANTES de la condición IF para que esté siempre disponible)
# ==========================
def limpiar_linea(line):
    return re.sub(r"\s+", " ", line).strip()

# ==========================
# 3. Subir archivo PDF
# ==========================
uploaded_file = st.file_uploader("📂 Sube el archivo PDF del Libro de Sueldos", type="pdf") 

if uploaded_file is not None:
    # 🚨 CORRECCIÓN 1: Manejar el archivo en memoria y empezar la indentación
    # Todo el código de procesamiento A PARTIR de aquí debe estar indentado
    
    # Abrir el PDF usando io.BytesIO para que pdfplumber pueda leerlo
    pdf_buffer = io.BytesIO(uploaded_file.getvalue())
    nombre_archivo_original = uploaded_file.name # Guardamos el nombre para la salida

    # ==========================
    # 5. Procesar el PDF
    # ==========================
    empleados = []

    try:
        with pdfplumber.open(pdf_buffer) as pdf:
            for page in pdf.pages:
                text = page.extract_text()

                # Eliminar info irrelevante
                text = re.sub(r"\*.*\*", "", text)
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

                    # ... (el resto del código de extracción es correcto)
                    # Aquí iría el resto de tu lógica de extracción de datos...

                    if re.match(r"^\d+\s+\d{2}-\d{8}-\d", linea):
                        match_linea1 = re.match(r"(\d+)\s+(\d{2}-\d{8}-\d)\s+(.*?)\s+(\d{2}/\d{2}/\d{4})", linea)
                        if match_linea1:
                            legajo = match_linea1.group(1)
                            cuil = match_linea1.group(2)
                            apellido_nombre = match_linea1.group(3).strip()
                            fecha_ingreso = match_linea1.group(4)
                            resto_linea1 = linea[match_linea1.end():].strip()
                            match_resto = re.search(r"(\S+)\s+DNI\s+(\S+)\s+(\S+)", resto_linea1)
                            
                            # ... (resto de la lógica de extracción, omitida por brevedad) ...
                            
                            fecha_cese = match_resto.group(1) if match_resto else None
                            doc_num = match_resto.group(2) if match_resto else None
                            fecha_nac = match_resto.group(3) if match_resto else None
                            
                            i += 1
                            linea2 = lines[i] if i < len(lines) else ""
                            # ... (lógica de linea2) ...
                            partes = linea2.split(maxsplit=1)
                            nacionalidad = partes[0] if len(partes) > 0 else None
                            resto_linea2 = partes[1] if len(partes) > 1 else ""
                            match_obra_social = re.search(r'\s(\d+\s-\s.+)$', resto_linea2)
                            obra_social = match_obra_social.group(1).strip() if match_obra_social else None
                            categoria = resto_linea2[:match_obra_social.start()].strip() if match_obra_social else resto_linea2.strip()

                            i += 1
                            linea3 = lines[i] if i < len(lines) else ""
                            # ... (lógica de linea3) ...
                            patron_campos = r'^(\d+\s-\s.+?)\s+(\d+/\d+\s-\s.+?)\s+(\d+\s-\s.+?)$'
                            match_campos = re.search(patron_campos, linea3)

                            modalidad_contratacion = match_campos.group(1).strip() if match_campos else None
                            convenio_colectivo = match_campos.group(2).strip() if match_campos else None
                            puesto = match_campos.group(3).strip() if match_campos else None

                            empleados.append({
                                "Legajo": legajo, "CUIL": cuil, "Apellido y Nombre": apellido_nombre,
                                "Fecha Ingreso": fecha_ingreso, "Fecha Cese": fecha_cese, "Documento": doc_num,
                                "Fecha Nacimiento": fecha_nac, "Nacionalidad": nacionalidad, "Categoria": categoria,
                                "Obra Social": obra_social, "Modalidad de Contratacion": modalidad_contratacion,
                                "Convenio Colectivo": convenio_colectivo, "Puesto": puesto
                            })
                    i += 1

    except Exception as e:
        st.error(f"Se produjo un error al procesar el PDF: {e}")
        st.stop()


    # ==========================
    # 6. Exportar a Excel y validar
    # ==========================
    if empleados:
        df = pd.DataFrame(empleados)
        
        st.success(f"👥 Total empleados extraídos: {len(empleados)}")
        st.subheader("📋 Vista previa de datos extraídos:")
        st.dataframe(df.head())

        # Crear el archivo Excel en un buffer de memoria
        excel_buffer = io.BytesIO()
        df.to_excel(excel_buffer, index=False, engine='openpyxl')
        excel_buffer.seek(0) # Rebobinar el buffer
        
        # Nombre del archivo de salida
        nombre_base = os.path.splitext(nombre_archivo_original)[0]
        nombre_archivo_excel = f"{nombre_base}_Extraido.xlsx"

        st.info(f"✅ Archivo generado: {nombre_archivo_excel}")

        # Widget de descarga de Streamlit
        st.download_button(
            label="Descargar archivo Excel 📥",
            data=excel_buffer,
            file_name=nombre_archivo_excel,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    else:
        st.warning("⚠️ No se extrajo ningún dato. El PDF pudo estar vacío o el formato no coincide con el esperado.")

import streamlit as st
import pandas as pd
import unicodedata
import re
import requests
import io

# 🚨 NUEVO ID CORRECTO (Extraído de tu enlace)
SPREADSHEET_ID = "1s09hCW4sL9hQQbKmT793vFZKKEjDn07p" 

def tokenizar_y_limpiar(texto):
    """Filtra y extrae las palabras conceptuales puras quitando conectores y términos metodológicos"""
    if pd.isna(texto):
        return set()
    texto = str(texto).lower()
    texto = ''.join(c for c in unicodedata.normalize('NFD', texto) if unicodedata.category(c) != 'Mn')
    palabras = re.findall(r'[a-z0-9ñ]+', texto)
    
    exclusiones = {
        'en', 'de', 'y', 'la', 'el', 'con', 'para', 'del', 'los', 'las', 'un', 'una', 'al', 'por', 'sobre',
        'diplomado', 'curso', 'programa', 'gestion', 'aplicada', 'avanzado', 'especialidad',
        'revision', 'bibliografica', 'estudio', 'analisis', 'monografia', 'propuesta', 'diseno', 'revicion',
        'estrategia', 'estrategias', 'implementacion', 'evaluacion', 'caso', 'uap', 'sucre', 'bolivia', 'a', 'traves'
    }
    return {p for p in palabras if p not in exclusiones and len(p) > 2}

def calcular_similitud_semantica(set_nuevo, set_existente):
    """Mide la intersección de conceptos core sobre el tamaño del título propuesto"""
    if not set_nuevo or not set_existente:
        return 0.0
    interseccion = set_nuevo.intersection(set_existente)
    return len(interseccion) / len(set_nuevo)

st.set_page_config(page_title="Verificador de Monografías UAP", page_icon="🛡️", layout="centered")

st.title("🛡️ Sistema Antiduplicidad de Monografías - UAP")
st.write("Filtro inteligente de control académico conectado a tu Google Sheet. Si el tema central ya existe, la propuesta será rechazada.")
st.markdown("---")

nuevo_titulo = st.text_input("📝 Ingrese el TÍTULO de la nueva monografía a evaluar:")

if st.button("🔍 Validar Originalidad del Tema", type="primary") and nuevo_titulo:
    todos_los_titulos = []
    total_registros = 0
    
    with st.spinner("Conectando en tiempo real con Google Sheets y analizando pestañas..."):
        try:
            # Exportamos el archivo completo de Google Sheets a la memoria para extraer las pestañas dinámicamente
            url_export = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/export?format=xlsx"
            response = requests.get(url_export)
            
            if response.status_code == 200:
                excel_memoria = pd.ExcelFile(io.BytesIO(response.content))
                # ¡Aquí obtenemos todas las pestañas de tu documento automáticamente!
                todas_las_pestanas = excel_memoria.sheet_names
                
                for pestana in todas_las_pestanas:
                    # Ignoramos pestañas genéricas que no sean de los diplomados si existen
                    if pestana.upper() in ['DIP', 'DIP 2', 'DIP 3', 'HOJA 1']:
                        continue
                    
                    # Leemos la hoja saltando las filas superiores de títulos institucionales
                    df = pd.read_excel(excel_memoria, sheet_name=pestana, header=None)
                    
                    columna_buscar_idx = None
                    fila_datos_inicio = 0
                    
                    # Buscamos en qué columna y fila está la cabecera real de las monografías
                    for r_idx in range(min(7, len(df))):
                        for c_idx in range(len(df.columns)):
                            celda = str(df.iloc[r_idx, c_idx]).upper()
                            if "MONOGRAF" in celda or "TÍTULO" in celda or "TITULO" in celda:
                                columna_buscar_idx = c_idx
                                fila_datos_inicio = r_idx + 1
                                break
                        if columna_buscar_idx is not None:
                            break
                    
                    # Si no encuentra por texto, por el formato estándar de tus hojas usamos la columna F (Índice 5)
                    if columna_buscar_idx is None and len(df.columns) > 5:
                        columna_buscar_idx = 5
                        fila_datos_inicio = 4
                    
                    if columna_buscar_idx is not None:
                        for nombre in df.iloc[fila_datos_inicio:, columna_buscar_idx].dropna():
                            n_str = str(nombre).strip()
                            # Filtro estricto para limpiar celdas vacías o con textos de formato
                            if (n_str and len(n_str) > 12 and 
                                "TÍTULO" not in n_str.upper() and 
                                "MONOGRAFÍA" not in n_str.upper() and 
                                "UNIVERSIDAD" not in n_str.upper()):
                                
                                todos_los_titulos.append({
                                    "nombre_original": n_str,
                                    "tokens": tokenizar_y_limpiar(n_str),
                                    "pestana": pestana
                                })
                                total_registros += 1
            else:
                st.error("❌ No se pudo acceder al Google Sheet. Asegúrate de que esté compartido como 'Cualquier persona con el enlace'.")
        except Exception as e:
            st.error(f"⚠️ Ocurrió un error al procesar el archivo: {str(e)}")

    # Indicador de estado en pantalla
    st.caption(f"📊 Control de Calidad: **{total_registros}** monografías históricas analizadas en vivo.")

    if total_registros > 0:
        # Análisis de Coincidencias Críticas
        tokens_nuevos = tokenizar_y_limpiar(nuevo_titulo)
        coincidencias_peligrosas = []
        
        for item in todos_los_titulos:
            # Validación estricta 1: Copia exacta limpia
            t_nuevo_norm = re.sub(r'\s+', ' ', nuevo_titulo.strip().upper())
            t_orig_norm = re.sub(r'\s+', ' ', item["nombre_original"].strip().upper())
            
            if t_nuevo_norm == t_orig_norm:
                coincidencias_peligrosas.append({**item, "porcentaje": 100})
                continue
                
            # Validación estricta 2: Similitud conceptual core
            porcentaje = calcular_similitud_semantica(tokens_nuevos, item["tokens"])
            
            # Umbral del 45% para que sea igual de estricto que tu verificador anterior
            if porcentaje >= 0.45: 
                coincidencias_peligrosas.append({**item, "porcentaje": int(porcentaje * 100)})

        # ---- Lógica del Verificador de Proyectos (Bloqueo / Rechazo) ----
        if coincidencias_peligrosas:
            coincidencias_peligrosas = sorted(coincidencias_peligrosas, key=lambda x: x['porcentaje'], reverse=True)
            
            st.error("🚨 **RECHAZADO: TEMA DUPLICADO O YA EXISTENTE**")
            st.write("---")
            st.subheader("❌ Conflictos de Similitud Detectados:")
            
            for c in coincidencias_peligrosas[:3]:
                st.warning(
                    f"📌 **Título Registrado**: {c['nombre_original']}\n\n"
                    f"📂 **Ubicación en Base de Datos**: Pestaña *'{c['pestana']}'*\n"
                    f"📊 **Grado de Coincidencia en Conceptos**: `{c['porcentaje']}%`"
                )
                st.markdown("---")
        else:
            st.success("✅ **TEMA APROBADO**")
            st.balloons()
            st.markdown(f"> **El título propuesto:** *\"{nuevo_titulo}\"* presenta un enfoque de investigación original y no duplica el historial registrado.")

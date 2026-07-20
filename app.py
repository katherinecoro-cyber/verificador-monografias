import streamlit as st
import pandas as pd
import unicodedata
import re

# ID de tu Google Sheet centralizado (Verificado)
SPREADSHEET_ID = "1s09hCW4sL9hQQbKmT793vFZKKEjDn07p" 

# Lista de pestañas de tu documento de monografías
PESTANAS = [
    '1. DIP. EMPR. INNOV. EMP.', '2. DIP. DIAG. INT. CA. VIO. SEX', '3. DIP. RED. TEL. G-1', 
    '4. DIP. DIS. GRAF. MUL. FOT.', '5. DIP. RED. TEL. G-2', '6. DIP. EDU. GES. CEN. EDU. MAE', 
    '7. DIP. PSI. DIDC.  EDU', '8. DIP. GES. MED. INT.', '9. DIP. RED. TEL. G3', 
    '10. DIP. GES, RIS. FIN. IA.', '11. DIP. TOP. CAR. TEC. LI.', '12. DIP. EDU. ESP. LSB. G1', 
    '13. DIP. SUP. COM.TEC.G-8', '14. DIP. EDU.ESP.LE.SE.G-2', '15.DIP.RED.TEL.G-4', 
    '16.DIP.EDU.ESP.LEN.SE.G3', '17. DIP. DIS.CONS.M. SITIOS WEB', '18. DIP. ESTAD. MATE V-II G-1', 
    '19. DIP. EDU.ESP.TEA.G1 ', '20.DIP. NEFRO.D.H. G-5 ', '21. DIP. TOP.CART.G-2', 
    '22.DIP.HORMIGÓN ARMADO', '23.DIP.LENG.SEÑAS V2 G1', '24.DIP.EDU.E.M.TEA G-2', 
    '25.DIP.DISEÑO GRAFICO G-2', '26. DIP.HIDRAULICA G-1', '27.DIP.METODOLOGIA G-6', 
    '28.DIP TOPO Y CART G3', '29.DIP.PSICOTE.3RA GEN. G-1', '30.DIP. ING.ESTR.PATOLOGIA Y RE', 
    '31. DIP. CIVIL 3D G-1', '32.DIP.ABORDAJES PSICOLOGICO G-', '33.DIP.PSICOMOTRICIDAD G-2', 
    '34.DIP. METODOLOGIA DE INVES. G', '35.DIP. CIVIL 3D G-2', '36.DIP RESOLUCION DE CONFLICTOS', 
    '37.DIP. ING. HIDRAULICA G-2', '38.DIP. CIVIL 3D G-3', '39.DIP. CIENCIAS FORENSES G-1', 
    '40.DIP. GERENCIA BIM G-1', '41. DIP. PLANTAS INDUSTRIALES V', '42. DIP. BIOMEDICOS G-3', 
    '43.DIP.PSICOMOTRICIDAD V-II G-1', '44.DIP. PSICOTERAPIAS 3RA GEN. ', '45.DIP.SIG CON .TELEDETECCION  ', 
    '46.DIP.SISMORESIS G1', '47.DIP. TECNICAS PSICOMETRICAS ', '48.DIP. METODOLOGIA INV. VII G1', 
    '49.DIP EDU.SUP.B.C.TEC.VII G3', '50.DIP.ING.SANITARIA VI G1', '51.DIP. PSICOTERAPIAS G3', 
    '52.DIP. AUTOMATIZACION', '53.DIP.ESTADISTICA MAT VIII', '54.DIPL.SIST.INF.BACHILLERATO.T', 
    '55.DIP. PUENTES', '56.DIP CIVIL 3D G4', '57.DIPLOMADO EN HIDROPONIA', '58.DIPLOMADO METODOLOGIA VII G3'
]

def tokenizar_y_limpiar(texto):
    """Limpia el texto, quita acentos, conectores y extrae conceptos core de investigación"""
    if pd.isna(texto):
        return set()
    texto = str(texto).lower()
    # Quitar acentos/tildes
    texto = ''.join(c for c in unicodedata.normalize('NFD', texto) if unicodedata.category(c) != 'Mn')
    # Dejar solo letras y números
    palabras = re.findall(r'[a-z0-9ñ]+', texto)
    
    # Exclusión de conectores y términos metodológicos que se repiten en todas las monografías
    exclusiones = {
        'en', 'de', 'y', 'la', 'el', 'con', 'para', 'del', 'los', 'las', 'un', 'una', 'al', 'por', 'sobre',
        'diplomado', 'curso', 'programa', 'gestion', 'aplicada', 'avanzado', 'especialidad',
        'revision', 'bibliografica', 'estudio', 'analisis', 'monografia', 'propuesta', 'diseno',
        'estrategia', 'estrategias', 'implementacion', 'evaluacion', 'caso', 'uap', 'sucre', 'bolivia'
    }
    return {p for p in palabras if p not in exclusiones and len(p) > 2}

def calcular_similitud_semantica(set_nuevo, set_existente):
    """Calcula el porcentaje de coincidencia conceptual (Índice Jaccard)"""
    if not set_nuevo or not set_existente:
        return 0.0
    interseccion = set_nuevo.intersection(set_existente)
    union = set_nuevo.union(set_existente)
    return len(interseccion) / len(union)

# Configuración de Streamlit
st.set_page_config(page_title="Verificador de Monografías UAP", page_icon="🛡️", layout="centered")

st.title("🛡️ Verificador Inteligente de Monografías")
st.write("Conectado en vivo a Google Sheets. Si el tema central ya existe, la propuesta será rechazada.")
st.markdown("---")

nuevo_titulo = st.text_input("Escribe el nombre de la nueva monografía a evaluar:")

if st.button("Verificar Originalidad de Propuesta", type="primary") and nuevo_titulo:
    todos_los_titulos = []
    total_registros = 0
    
    with st.spinner("Leyendo datos en tiempo real desde Google Sheets..."):
        for pestana in PESTANAS:
            # Enlace de lectura en formato CSV directo por pestaña
            url = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/gviz/tq?tqx=out:csv&sheet={pestana.replace(' ', '%20')}"
            try:
                # Leemos la hoja completa sin asumir dónde están los encabezados
                df = pd.read_csv(url, header=None)
                
                columna_buscar_idx = None
                fila_datos_inicio = 0
                
                # Buscamos dinámicamente en qué columna y fila está la palabra "TÍTULO" o "MONOGRAFÍA"
                for r_idx in range(min(7, len(df))):
                    for c_idx in range(len(df.columns)):
                        celda = str(df.iloc[r_idx, c_idx]).upper()
                        if "MONOGRAF" in celda or "TÍTULO" in celda or "TITULO" in celda:
                            columna_buscar_idx = c_idx
                            fila_datos_inicio = r_idx + 1
                            break
                    if columna_buscar_idx is not None:
                        break
                
                # Si una pestaña viene desconfigurada, por defecto la columna F (índice 5) guarda las monografías
                if columna_buscar_idx is None and len(df.columns) > 5:
                    columna_buscar_idx = 5
                    fila_datos_inicio = 4
                
                # Si encontramos la columna, extraemos sus textos limpios
                if columna_buscar_idx is not None:
                    for nombre in df.iloc[fila_datos_inicio:, columna_buscar_idx].dropna():
                        n_str = str(nombre).strip()
                        # Filtro estricto para ignorar las filas de firmas, números de páginas o celdas vacías
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
            except:
                continue

    st.caption(f"📊 Control de Calidad: **{total_registros}** monografías analizadas en vivo.")

    # Analizar similitudes
    tokens_nuevos = tokenizar_y_limpiar(nuevo_titulo)
    coincidencias_peligrosas = []
    
    for item in todos_los_titulos:
        # Validación 1: Copia exacta directa (quitando espacios dobles)
        t_nuevo_norm = re.sub(r'\s+', ' ', nuevo_titulo.strip().upper())
        t_orig_norm = re.sub(r'\s+', ' ', item["nombre_original"].strip().upper())
        
        if t_nuevo_norm == t_orig_norm:
            coincidencias_peligrosas.append({**item, "porcentaje": 100})
            continue
            
        # Validación 2: Similitud por núcleo de palabras clave temáticas (Ignorando la metodología)
        porcentaje = calcular_similitud_semantica(tokens_nuevos, item["tokens"])
        
        # Umbral del 40% (idéntico a tu verificador de proyectos exitoso)
        if porcentaje >= 0.40: 
            coincidencias_peligrosas.append({**item, "porcentaje": int(porcentaje * 100)})

    # Mostrar Resultados estrictos (Rechazo / Aprobación)
    if coincidencias_peligrosas:
        coincidencias_peligrosas = sorted(coincidencias_peligrosas, key=lambda x: x['porcentaje'], reverse=True)
        
        st.error("🚨 **RECHAZADO: TEMA DUPLICADO O YA EXISTENTE**")
        st.write("---")
        st.subheader("❌ Conflictos de Similitud Detectados:")
        
        for c in coincidencias_peligrosas[:3]:
            st.warning(
                f"📌 **Título Registrado**: {c['nombre_original']}\n\n"
                f"📂 **Ubicación**: Pestaña *'{c['pestana']}'*\n"
                f"📊 **Grado de Coincidencia en Conceptos**: `{c['porcentaje']}%`"
            )
            st.markdown("---")
    else:
        st.success("✅ **TEMA APROBADO**")
        st.balloons()
        st.markdown(f"> **El título propuesto:** *\"{nuevo_titulo}\"* es original y no presenta conflictos con las investigaciones registradas en Google Sheets.")

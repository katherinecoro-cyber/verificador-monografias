import streamlit as st
import pandas as pd
import unicodedata
import re

# Tu ID de Google Sheets (Verificado)
SPREADSHEET_ID = "1s09hCW4sL9hQQbKmT793vFZKKEjDn07p" 

# Lista completa de todas las pestañas de tu documento de la UAP
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
    '55.DIP. PUENTES', '56.DIP CIVIL 3D G4', '57.DIPLOMADO EN HIDROPONIA', '58.DIPLOMADO METODOLOGIA VII G3',
    'Copia de Copia de DIP.', 'DIP', 'DIP 2', 'DIP 3'
]

def tokenizar_y_limpiar(texto):
    """Limpia el texto, elimina acentos, conectores y palabras metodológicas vacías"""
    if pd.isna(texto):
        return set()
    texto = str(texto).lower()
    # Quitar tildes
    texto = ''.join(c for c in unicodedata.normalize('NFD', texto) if unicodedata.category(c) != 'Mn')
    # Extraer solo palabras alfanuméricas
    palabras = re.findall(r'[a-z0-9ñ]+', texto)
    
    # Conectores y palabras metodológicas que inflan artificialmente los títulos de monografías
    exclusiones = {
        'en', 'de', 'y', 'la', 'el', 'con', 'para', 'del', 'los', 'las', 'un', 'una', 'al', 'por', 'sobre', 'sus',
        'diplomado', 'curso', 'programa', 'gestion', 'aplicada', 'avanzado', 'especialidad', 'v-ii', 'vii', 'viii',
        'revision', 'bibliografica', 'estudio', 'analisis', 'monografia', 'propuesta', 'diseno', 'g-1', 'g-2', 'g-3',
        'estrategia', 'estrategias', 'implementacion', 'evaluacion', 'caso', 'uap', 'sucre', 'bolivia', 'unnamed',
        'titulo', 'monografias', 'monografia', 'apellidos', 'nombres', 'celular', 'correo', 'grupo', 'universidad'
    }
    return {p for p in palabras if p not in exclusiones and len(p) > 2}

def calcular_similitud_semantica(set_nuevo, set_existente):
    """Calcula el índice de coincidencia Jaccard entre dos sets de conceptos core"""
    if not set_nuevo or not set_existente:
        return 0.0
    interseccion = set_nuevo.intersection(set_existente)
    union = set_nuevo.union(set_existente)
    return len(interseccion) / len(union)

# Configuración de interfaz de Streamlit
st.set_page_config(page_title="Verificador de Monografías UAP", page_icon="🛡️", layout="centered")

st.title("🛡️ Sistema Antiduplicidad de Monografías - UAP")
st.write("Filtro inteligente de control académico. Si el tema o núcleo de investigación ya existe, será rechazado automáticamente.")
st.markdown("---")

nuevo_titulo = st.text_input("📝 Ingrese el TÍTULO de la nueva monografía a evaluar:")

if st.button("🔍 Validar Originalidad del Tema", type="primary") and nuevo_titulo:
    todos_los_diplomados = []
    total_registros = 0
    
    with st.spinner("Escaneando exhaustivamente todas las pestañas de Google Sheets..."):
        for pestana in PESTANAS:
            url = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/gviz/tq?tqx=out:csv&sheet={pestana.replace(' ', '%20')}"
            try:
                # Cargamos todo desde la fila 0 para analizar la estructura real
                df = pd.read_csv(url, header=None)
                
                # Buscamos en qué fila y columna está el encabezado de las monografías
                columna_idx = None
                fila_inicio = 0
                
                # Escaneamos las primeras 7 filas para encontrar la columna correcta
                for r_idx in range(min(7, len(df))):
                    for c_idx in range(len(df.columns)):
                        celda_texto = str(df.iloc[r_idx, c_idx]).upper()
                        if "MONOGRAF" in celda_texto or "TÍTULO" in celda_texto or "TITULO" in celda_texto:
                            columna_idx = c_idx
                            fila_inicio = r_idx + 1
                            break
                    if columna_idx is not None:
                        break
                
                # Si no encontramos por palabra clave, por defecto en este formato suele ser la columna índice 5 (F)
                if columna_idx is None and len(df.columns) > 5:
                    columna_idx = 5
                    fila_inicio = 4

                if columna_idx is not None:
                    # Extraer los datos reales a partir de la fila detectada
                    for nombre in df.iloc[fila_inicio:, columna_idx].dropna():
                        n_str = str(nombre).strip()
                        # Evitar capturar basura del documento, firmas o líneas vacías
                        if (n_str and len(n_str) > 12 and 
                            "TÍTULO" not in n_str.upper() and 
                            "MONOGRAFÍA" not in n_str.upper() and 
                            "UNIVERSIDAD" not in n_str.upper()):
                            
                            todos_los_diplomados.append({
                                "nombre_original": n_str,
                                "tokens": tokenizar_y_limpiar(n_str),
                                "pestana": pestana
                            })
                            total_registros += 1
            except:
                continue

    st.caption(f"📊 Control de calidad: **{total_registros}** monografías históricas analizadas en tiempo real.")

    # Análisis de Coincidencias Críticas
    tokens_nuevos = tokenizar_y_limpiar(nuevo_titulo)
    coincidencias_peligrosas = []
    
    for item in todos_los_diplomados:
        # Validación estricta 1: Copia exacta (ignora espacios y mayúsculas)
        if nuevo_titulo.strip().upper() == item["nombre_original"].upper():
            coincidencias_peligrosas.append({**item, "porcentaje": 100})
            continue
            
        # Validación estricta 2: Similitud por núcleo de conceptos de investigación
        porcentaje = calcular_similitud_semantica(tokens_nuevos, item["tokens"])
        
        # Un umbral de 40% en monografías es un indicador claro de que se repite el mismo problema/objeto de estudio
        if porcentaje >= 0.40: 
            coincidencias_peligrosas.append({**item, "porcentaje": int(porcentaje * 100)})

    # ---- Lógica del Verificador de Proyectos (Aprobación / Rechazo Directo) ----
    if coincidencias_peligrosas:
        # Ordenamos poniendo el caso más idéntico arriba de todo
        coincidencias_peligrosas = sorted(coincidencias_peligrosas, key=lambda x: x['porcentaje'], reverse=True)
        
        st.error("🚨 **RECHAZADO: TEMA DUPLICADO O YA EXISTENTE**")
        st.write("---")
        st.subheader("❌ Conflictos de Similitud Detectados:")
        
        # Mostrar los cruces más críticos encontrados
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
        st.markdown(f"> **El título propuesto:** *\"{nuevo_titulo}\"* presenta una combinación única de palabras clave y variables de estudio. No tiene conflictos con el historial registrado.")

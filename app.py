import streamlit as st
import pandas as pd
import unicodedata
import re

# ID de tu Google Sheet (Verificado)
SPREADSHEET_ID = "1s09hCW4sL9hQQbKmT793vFZKKEjDn07p" 

# Lista de pestañas oficiales del documento
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
st.write("Filtro inteligente de control académico. Si el tema o núcleo de investigación ya existe, será rechazado.")
st.markdown("---")

nuevo_titulo = st.text_input("📝 Ingrese el TÍTULO de la nueva monografía a evaluar:")

if st.button("🔍 Validar Originalidad del Tema", type="primary") and nuevo_titulo:
    todos_los_titulos = []
    total_registros = 0
    
    with st.spinner("Conectando con Google Sheets y extrayendo registros..."):
        for pestana in PESTANAS:
            # CAMBIO CLAVE: Cambiamos tq por tq?gid=... para evitar el error de celdas combinadas de arriba
            # Solicitamos los datos limpios saltando las primeras 4 filas de títulos institucionales
            url = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/gviz/tq?tqx=out:csv&headers=1&range=A5:K500&sheet={pestana.replace(' ', '%20')}"
            try:
                df = pd.read_csv(url)
                df.columns = df.columns.astype(str).str.strip().str.upper()
                
                # Buscamos de forma flexible la columna correspondiente
                columna_buscar = ""
                for col in df.columns:
                    if "MONOGRAF" in col or "TITULO" in col or "TÍTULO" in col:
                        columna_buscar = col
                        break
                
                # Si gviz falló renombrando la columna, por la estructura sabemos que es la sexta columna (Índice 5)
                if not columna_buscar and len(df.columns) > 5:
                    columna_buscar = df.columns[5]
                
                if columna_buscar:
                    for nombre in df[columna_buscar].dropna():
                        n_str = str(nombre).strip()
                        if (n_str and len(n_str) > 10 and 
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

    # Indicador de estado en pantalla
    st.caption(f"📊 Control de calidad: **{total_registros}** monografías históricas analizadas en tiempo real.")

    if total_registros == 0:
        st.error("⚠️ Error crítico: No se pudieron extraer datos desde Google Sheets. Verifica los permisos de compartir en tu documento.")
    else:
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
            
            # Si el nuevo título comparte un 55% o más de sus conceptos clave con uno viejo -> Alerta de Plagio/Duplicado
            if porcentaje >= 0.55: 
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

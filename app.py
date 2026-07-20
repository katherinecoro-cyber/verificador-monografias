import streamlit as st
import pandas as pd
import unicodedata
import re
import requests

# Configuración automática con tu ID de Google Sheets de Monografías
SPREADSHEET_ID = "1s09hCW4sL9hQQbKmT793vFZKKEjDn07p" 

def obtener_pestanas_dinamicas(spreadsheet_id):
    """Obtiene la lista de todas las pestañas de forma automática desde Google Sheets"""
    try:
        url = f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/gviz/tq?tqx=out:csv"
        # Hacemos una petición rápida para ver si responde, pero para listar todas las pestañas 
        # de forma óptima a través de gviz sin API Key, lo ideal es procesar los errores o definirlas.
        # Como en este caso conocemos que son más de 60 pestañas basadas en diplomados, 
        # dejamos una función de extracción o una lista dinámica si se requiere.
        # NOTA: Para no depender de credenciales pesadas, usamos una lectura directa.
        pass
    except:
        # Si falla el auto-discovery, puedes mantener la lista manual o usar una estrategia alternativa.
        pass

def tokenizar_y_limpiar(texto):
    """Limpia el texto, quita acentos, conectores y extrae palabras clave de la monografía"""
    if pd.isna(texto):
        return set()
    texto = str(texto).lower()
    # Quitar acentos/tildes
    texto = ''.join(c for c in unicodedata.normalize('NFD', texto) if unicodedata.category(c) != 'Mn')
    # Dejar solo letras y números
    palabras = re.findall(r'[a-z0-9ñ]+', texto)
    
    # Filtro de conectores genéricos y palabras metodológicas que no aportan significado temático
    conectores = {
        'en', 'de', 'y', 'la', 'el', 'con', 'para', 'del', 'los', 'las', 'un', 'una', 'al', 'por', 'sobre',
        'diplomado', 'curso', 'programa', 'gestion', 'aplicada', 'avanzado', 'especialidad',
        'revision', 'bibliografica', 'estudio', 'analisis', 'monografia', 'propuesta', 'diseno',
        'estrategia', 'estrategias', 'implementacion', 'evaluacion', 'caso', 'uap', 'sucre'
    }
    return {p for p in palabras if p not in conectores and len(p) > 2}

def calcular_similitud_semantica(set_nuevo, set_existente):
    """Calcula el porcentaje de coincidencia basado en las palabras clave centrales"""
    if not set_nuevo or not set_existente:
        return 0.0
    interseccion = set_nuevo.intersection(set_existente)
    return len(interseccion) / len(set_nuevo)

st.set_page_config(page_title="Verificador de Monografías UAP", page_icon="📚", layout="centered")

st.title("📚 Verificador Inteligente de Monografías")
st.write("El sistema analiza los títulos de monografías registradas para evitar la duplicidad de temas de investigación.")
st.markdown("---")

nueva_monografia = st.text_input("Escribe el título de la nueva monografía a evaluar:")

if st.button("Verificar Propuesta de Investigación", type="primary") and nueva_monografia:
    todos_los_titulos = []
    total_registros = 0
    
    # Listado completo obtenido de tu documento 'DETALLE DE MONOGRAFIAS'
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
    
    with st.spinner("Cargando y procesando títulos de monografías desde Google Sheets..."):
        for pestana in PESTANAS:
            url = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/gviz/tq?tqx=out:csv&sheet={pestana.replace(' ', '%20')}"
            try:
                # Se saltan las primeras 3 filas de títulos institucionales para capturar la cabecera real
                df = pd.read_csv(url, skiprows=3)
                df.columns = df.columns.astype(str).str.strip().str.upper()
                
                columna_buscar = ""
                for col in df.columns:
                    if "MONOGRAF" in col or "TITULO" in col or "TÍTULO" in col:
                        columna_buscar = col
                        break
                
                if columna_buscar:
                    for nombre in df[columna_buscar].dropna():
                        n_str = str(nombre).strip()
                        # Filtros para evitar filas vacías, de firmas, numeraciones o textos informativos
                        if n_str and len(n_str) > 10 and "TÍTULO" not in n_str.upper() and "MONOGRAFÍA" not in n_str.upper():
                            todos_los_titulos.append({
                                "nombre_original": n_str,
                                "tokens": tokenizar_y_limpiar(n_str),
                                "pestana": pestana
                            })
                            total_registros += 1
            except:
                continue

    st.caption(f"📊 Base de datos: {total_registros} monografías analizadas en vivo.")

    # Analizar similitudes
    tokens_nuevos = tokenizar_y_limpiar(nueva_monografia)
    coincidencias_peligrosas = []
    
    for item in todos_los_titulos:
        # Validación 1: Copia exacta
        if nueva_monografia.strip().upper() == item["nombre_original"].upper():
            coincidencias_peligrosas.append({**item, "porcentaje": 100})
            continue
            
        # Validación 2: Similitud por núcleo de palabras clave temáticas
        porcentaje = calcular_similitud_semantica(tokens_nuevos, item["tokens"])
        if porcentaje >= 0.50: # Al ser títulos de monografías más largos, un 50% de coincidencia core ya es una alerta válida
            coincidencias_peligrosas.append({**item, "porcentaje": int(porcentaje * 100)})

    # Mostrar Resultados
    if coincidencias_peligrosas:
        coincidencias_peligrosas = sorted(coincidencias_peligrosas, key=lambda x: x['porcentaje'], reverse=True)
        
        st.error(f"❌ **ALERTA DE DUPLICIDAD / TEMA REPETIDO**")
        st.warning(f"Se encontraron investigaciones con un enfoque temático muy similar en el histórico.")
        
        st.write("### Monografías similares encontradas:")
        for c in coincidencias_peligrosas[:4]: # Mostramos hasta 4 para mayor contexto de antecedentes
            st.info(
                f"📌 **{c['nombre_original']}**\n\n"
                f"📂 **Programa/Diplomado**: *'{c['pestana']}'*\n"
                f"📊 **Similitud en palabras clave**: `{c['porcentaje']}%`"
            )
    else:
        st.success("✅ **TEMA ORIGINAL APROBADO**: No se encontraron monografías previas que compartan este núcleo de investigación.")

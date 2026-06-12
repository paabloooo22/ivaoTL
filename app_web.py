import streamlit as st
import requests
import re
from datetime import datetime

st.set_page_config(page_title="ATC Auto-TL", page_icon="📡")
st.title("📡 Calculadora TL, Pistas y ATIS (Versión Turbo)")
st.write("Calcula el TL, la configuración de pistas (incluyendo nocturnas) y genera los Remarks del ATIS a la velocidad del rayo.")
st.divider()

# --- 1. MEMORIA DEL PROGRAMA ---
if 'qnh_actual' not in st.session_state:
    st.session_state.qnh_actual = 1013
if 'indice_ta' not in st.session_state:
    st.session_state.indice_ta = 0 
if 'pista_sugerida' not in st.session_state:
    st.session_state.pista_sugerida = ""
if 'rmk_atis' not in st.session_state:
    st.session_state.rmk_atis = ""

# --- 2. MAGIA NUEVA: FUNCIÓN CON CACHÉ (TURBO) ---
@st.cache_data(ttl=600) # Guarda la info 10 minutos (600 segundos) para no saturar internet
def descargar_metar_rapido(codigo_icao):
    url = f"https://aviationweather.gov/api/data/metar?ids={codigo_icao}"
    try:
        respuesta = requests.get(url, timeout=5) 
        return respuesta.text.strip()
    except:
        return None

# --- 3. ZONA DE DESCARGA E INPUTS ---
col1, col2, col3 = st.columns([1.5, 1.5, 1])

with col1:
    icao = st.text_input("Código ICAO del aeropuerto:", value="LEPA", max_chars=4).upper()

with col2:
    cpdlc = st.checkbox("📟 CPDLC (Hoppie) Operativo")
    hiro = st.checkbox("🚀 HIRO Activo (Solo LEBL APP)")

with col3:
    st.write("<br>", unsafe_allow_html=True)
    buscar = st.button("📡 Auto-Calcular Todo", use_container_width=True)

if buscar:
    # Ajuste automático del TA según aeropuerto
    if icao == "LEGR": st.session_state.indice_ta = 1
    elif icao == "LESU": st.session_state.indice_ta = 2
    elif icao in ["LEMD", "LECU", "LEGT", "LETO", "LEMG"]: st.session_state.indice_ta = 3
    else: st.session_state.indice_ta = 0 

    # Llamamos a nuestra nueva función súper rápida
    metar = descargar_metar_rapido(icao)
    
    if metar:
        st.info(f"**METAR Recibido:** {metar}")
        
        # --- RELOJ Y QNH ---
        hora_zulu_actual = datetime.utcnow()
        hora_formateada = hora_zulu_actual.strftime("%H:%M Z")
        hora = hora_zulu_actual.hour
        es_noche = True if (hora >= 21 or hora < 6) else False

        busqueda_qnh = re.search(r'Q(\d{4})', metar)
        if busqueda_qnh:
            st.session_state.qnh_actual = int(busqueda_qnh.group(1))
        
        # --- VIENTO Y PISTAS (MATEMÁTICA CORREGIDA) ---
        busqueda_viento = re.search(r'(VRB|\d{3})(\d{2,3})(?:G\d{2,3})?KT', metar)
        if busqueda_viento:
            dir_viento = busqueda_viento.group(1)
            vel_viento = int(busqueda_viento.group(2))
            
            estado_dia = "🌙 HORARIO NOCTURNO" if es_noche else "☀️ Horario Diurno"
            st.session_state.pista_sugerida = f"🌪️ Viento: {dir_viento}º a {vel_viento} KT. | 🕒 Hora IVAO: {hora_formateada} - {estado_dia}"
            dir_grados = 0 if dir_viento == "VRB" else int(dir_viento)
            
            # LÓGICA DE PISTAS CORREGIDA (Arcos de Viento de Cara)
            if icao == "LEPA":
                if es_noche: 
                    st.session_state.pista_sugerida += "\n\n✅ Configuración Nocturna (Arr 24L / Dep 24R)"
                elif dir_viento == "VRB" or vel_viento <= 10 or (150 <= dir_grados <= 330): 
                    st.session_state.pista_sugerida += "\n\n✅ Configuración Oeste (24L/24R) - Preferencial / Viento favorable"
                else: 
                    st.session_state.pista_sugerida += "\n\n⚠️ Configuración Este (06L/06R) - Viento de cola > 10kt en la 24"
                    
            elif icao == "LEMD":
                if es_noche: 
                    st.session_state.pista_sugerida += "\n\n✅ Configuración Nocturna (Arr 32R / Dep 36L)"
                elif dir_viento == "VRB" or vel_viento <= 10 or (dir_grados >= 270 or dir_grados <= 90): 
                    st.session_state.pista_sugerida += "\n\n✅ Configuración Norte (Arr 32 / Dep 36) - Preferencial / Viento favorable"
                else: 
                    st.session_state.pista_sugerida += "\n\n⚠️ Configuración Sur (Arr 18 / Dep 14) - Viento de cola > 10kt en Norte"

            elif icao == "LEBL":
                if es_noche: 
                    st.session_state.pista_sugerida += "\n\n✅ Config. Cruzada Nocturna (Arr 02 / Dep 24L)"
                elif dir_viento == "VRB" or vel_viento <= 10 or (160 <= dir_grados <= 340): 
                    st.session_state.pista_sugerida += "\n\n✅ Configuración Oeste (Arr 25R / Dep 24L) - Preferencial / Viento favorable"
                else: 
                    st.session_state.pista_sugerida += "\n\n⚠️ Configuración Este (Arr 07L / Dep 07R) - Viento de cola > 10kt en Oeste"

            elif icao == "LEMG":
                if es_noche: 
                    st.session_state.pista_sugerida += "\n\n✅ Configuración Nocturna (Arr 13 / Dep 13)"
                elif dir_viento == "VRB" or vel_viento <= 10 or (40 <= dir_grados <= 220): 
                    st.session_state.pista_sugerida += "\n\n✅ Configuración 13 (Arr 13 / Dep 13) - Preferencial / Viento favorable"
                else: 
                    st.session_state.pista_sugerida += "\n\n⚠️ Configuración 31 (Arr 31 / Dep 31) - Viento de cola > 10kt en la 13"
                
            elif icao == "LEVC":
                if es_noche: 
                    st.session_state.pista_sugerida += "\n\n✅ Configuración Nocturna (Arr 30 / Dep 12)"
                elif dir_viento == "VRB" or vel_viento <= 10 or (dir_grados >= 210 or dir_grados <= 30): 
                    st.session_state.pista_sugerida += "\n\n✅ Configuración 30 (Arr 30 / Dep 30) - Preferencial / Viento favorable"
                else: 
                    st.session_state.pista_sugerida += "\n\n⚠️ Configuración 12 (Arr 12 / Dep 12) - Viento de cola > 10kt en la 30"

            elif icao == "LEAL": 
                if es_noche: 
                    st.session_state.pista_sugerida += "\n\n✅ Configuración Nocturna (Arr 28 / Dep 10)"
                elif dir_viento == "VRB" or vel_viento <= 10 or (10 <= dir_grados <= 190): 
                    st.session_state.pista_sugerida += "\n\n✅ Configuración 10 (Arr 10 / Dep 10) - Preferencial / Viento favorable"
                else: 
                    st.session_state.pista_sugerida += "\n\n⚠️ Configuración 28 (Arr 28 / Dep 28) - Viento de cola > 10kt en la 10"

            elif icao == "LEZL":
                if es_noche: 
                    st.session_state.pista_sugerida += "\n\n✅ Procedimiento Nocturno Activo (Pref. 27)"
                elif dir_viento == "VRB" or vel_viento <= 10 or (180 <= dir_grados <= 360 or dir_grados == 0): 
                    st.session_state.pista_sugerida += "\n\n✅ Configuración 27 (Arr 27 / Dep 27) - Preferencial / Viento favorable"
                else: 
                    st.session_state.pista_sugerida += "\n\n⚠️ Configuración 09 (Arr 09 / Dep 09) - Viento de cola > 10kt en la 27"

            elif icao == "LEGR":
                if es_noche: 
                    st.session_state.pista_sugerida += "\n\n✅ Aeropuerto habitualmente H24 restringido. Pref. 27"
                elif dir_viento == "VRB" or vel_viento <= 10 or (180 <= dir_grados <= 360 or dir_grados == 0): 
                    st.session_state.pista_sugerida += "\n\n✅ Configuración 27 (Arr 27 / Dep 27) - Preferencial / Viento favorable"
                else: 
                    st.session_state.pista_sugerida += "\n\n⚠️ Configuración 09 (Arr 09 / Dep 09) - Viento de cola > 10kt en la 27"

        # --- GENERADOR DE REMARKS (RMK) DEL ATIS ---
        rmk = []
        
        if icao == "LEBL":
            rmk.append("AUTOSWITCH PROC IN FORCE")
            rmk.append("NAV APP TRANSITION IN USE CHECK FMS")
            if cpdlc: rmk.append("DATALINK DEP CLR AVBL")
            if hiro: rmk.append("HIRO IN FORCE")
            if es_noche: rmk.append("ARR TFC USE TWY UB TO VACATE RWY")

        elif icao == "LEMD":
            if es_noche: rmk.append("NIGHT CONFIG")
            elif "Norte" in st.session_state.pista_sugerida: rmk.append("NORTH DAY CONFIG")
            elif "Sur" in st.session_state.pista_sugerida: rmk.append("SOUTH DAY CONFIG")
            rmk.append("EXPECT ILS APP RWY [XX]")

        elif icao == "LEMG":
            rmk.append("AUTOSWITCH PROC ON DEP IN FORCE")
            if cpdlc: rmk.append("DATA LINK DEP CLR AVBL A G P D")

        elif icao in ["LEGE", "LEMH"]:
            rmk.append("PROCEDURAL APPROACH SERVICE BELOW FL075 - NO RADAR")

        elif icao == "LEJR":
            if cpdlc: rmk.append("DATA LINK DEP CLR AVBL L E J R")
            
        elif icao in ["LECU", "LEGT", "LETO", "LEVD", "LESA"]:
            rmk.append("EXPECT ILS APP RWY [XX]")

        st.session_state.rmk_atis = " ".join(rmk)

    else:
        st.error("El aeropuerto no existe o no hay datos meteorológicos.")

st.divider()

# --- 4. MOSTRAR RESULTADOS PISTAS Y ATIS ---
if st.session_state.pista_sugerida:
    st.info(st.session_state.pista_sugerida)

if st.session_state.rmk_atis:
    st.warning(f"📝 **Copia y pega esto en el RMK de tu ATIS en Aurora:**\n\n`{st.session_state.rmk_atis}`")
elif st.session_state.pista_sugerida and not st.session_state.rmk_atis:
    st.success("📝 **ATIS:** No hay Remarks obligatorios adicionales para este aeropuerto. (Añade EXAM IN PROGRESS o STREAMING si aplica).")

st.divider()

# --- 5. CONTROLES Y CÁLCULO DE TL ---
espacio_tl = st.empty() # Hueco para pintar el TL arriba de los controles

opciones_ta = ["Aeropuertos estándar (TA 6000 FT)", "Granada (TA 7000 FT)", "La Seu D'Urgell (TA 8000 FT)", "TMA de Madrid y Málaga (TA 13000 FT)"]
qnh = st.number_input("QNH para el cálculo:", min_value=900, max_value=1100, value=st.session_state.qnh_actual, step=1)
opcion = st.selectbox("Región / TA:", opciones_ta, index=st.session_state.indice_ta)

tl = None
if opcion == "Aeropuertos estándar (TA 6000 FT)":
    if 942 <= qnh <= 959: tl = "90"
    elif 960 <= qnh <= 977: tl = "85"
    elif 978 <= qnh <= 995: tl = "80"
    elif 996 <= qnh <= 1013: tl = "75"
    elif 1014 <= qnh <= 1031: tl = "70"
    elif 1032 <= qnh <= 1050: tl = "65"
elif opcion == "Granada (TA 7000 FT)":
    if 942 <= qnh <= 959: tl = "100"
    elif 960 <= qnh <= 977: tl = "95"
    elif 978 <= qnh <= 995: tl = "90"
    elif 996 <= qnh <= 1013: tl = "85"
    elif 1014 <= qnh <= 1031: tl = "80"
    elif 1032 <= qnh <= 1050: tl = "75"
elif opcion == "La Seu D'Urgell (TA 8000 FT)":
    if 942 <= qnh <= 959: tl = "110"
    elif 960 <= qnh <= 977: tl = "105"
    elif 978 <= qnh <= 995: tl = "100"
    elif 996 <= qnh <= 1013: tl = "95"
    elif 1014 <= qnh <= 1031: tl = "90"
    elif 1032 <= qnh <= 1050: tl = "85"
elif opcion == "TMA de Madrid y Málaga (TA 13000 FT)":
    if 942 <= qnh <= 959: tl = "160"
    elif 960 <= qnh <= 977: tl = "155"
    elif 978 <= qnh <= 995: tl = "150"
    elif 996 <= qnh <= 1013: tl = "145"
    elif 1014 <= qnh <= 1031: tl = "140"
    elif 1032 <= qnh <= 1050: tl = "135"

if tl is not None:
    espacio_tl.success(f"### Nivel de Transición (TL): FL {tl}")
else:
    espacio_tl.warning("⚠️ QNH fuera de los rangos estándar.")

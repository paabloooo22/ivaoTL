import streamlit as st
import requests
import re

st.set_page_config(page_title="ATC Auto-TL", page_icon="📡")
st.title("📡 Calculadora TL - 100% Autónoma")
st.write("Descarga el METAR, detecta el aeropuerto y calcula todo sin que toques nada.")
st.divider()

# --- 1. MEMORIA DEL PROGRAMA ---
if 'qnh_actual' not in st.session_state:
    st.session_state.qnh_actual = 1013
if 'indice_ta' not in st.session_state:
    st.session_state.indice_ta = 0 

# --- 2. ZONA DE DESCARGA DE INTERNET ---
col1, col2 = st.columns([2, 1])

with col1:
    icao = st.text_input("Código ICAO del aeropuerto:", value="LEPA", max_chars=4).upper()

with col2:
    st.write("<br>", unsafe_allow_html=True)
    buscar = st.button("📡 Auto-Calcular Todo", use_container_width=True)

if buscar:
    # MAGIA NUEVA: ¡Málaga (LEMG) vuelve al club de los 13.000 FT junto con el TMA de Madrid!
    if icao == "LEGR":
        st.session_state.indice_ta = 1 # Opción 1: Granada (7000 FT)
    elif icao == "LESU":
        st.session_state.indice_ta = 2 # Opción 2: La Seu (8000 FT)
    elif icao in ["LEMD", "LECU", "LEGT", "LETO", "LEMG"]: 
        st.session_state.indice_ta = 3 # Opción 3: TMA de Madrid y Málaga (13000 FT)
    else:
        st.session_state.indice_ta = 0 # Opción 0: Resto de España (6000 FT)

    # Conexión al servidor meteorológico
    url = f"https://aviationweather.gov/api/data/metar?ids={icao}"
    try:
        respuesta = requests.get(url)
        metar = respuesta.text.strip()
        
        if metar:
            st.info(f"**METAR Recibido:** {metar}")
            
            # Buscar el QNH
            busqueda = re.search(r'Q(\d{4})', metar)
            if busqueda:
                st.session_state.qnh_actual = int(busqueda.group(1))
                st.success(f"¡QNH {st.session_state.qnh_actual} extraído con éxito!")
            else:
                st.error("No se detectó un QNH europeo en el METAR (Letra Q).")
        else:
            st.error("El aeropuerto no existe o no hay datos meteorológicos.")
    except:
        st.error("Error al conectar con los servidores meteorológicos.")

st.divider()

# --- 3. CONTROLES Y CÁLCULO ---
opciones_ta = [
    "Aeropuertos estándar (TA 6000 FT)", 
    "Granada (TA 7000 FT)", 
    "La Seu D'Urgell (TA 8000 FT)", 
    "TMA de Madrid y Málaga (TA 13000 FT)"
]

qnh = st.number_input("QNH para el cálculo:", min_value=900, max_value=1100, value=st.session_state.qnh_actual, step=1)

# El menú se pondrá solito en "Madrid y Málaga" si escribes LEMG
opcion = st.selectbox("Región / TA detectada automáticamente:", opciones_ta, index=st.session_state.indice_ta)

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

# --- 4. MOSTRAR RESULTADO ---
if tl is not None:
    st.success(f"### Nivel de Transición (TL): FL {tl}")
else:
    st.warning("⚠️ QNH fuera de los rangos estándar.")
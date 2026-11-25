"""
Solo Habla — espacio anónimo para compartir lo que sientes.

Ejecutar:
    pip install streamlit
    streamlit run solo_habla.py

Notas de diseño:
- Los datos de cada persona (apodo, avatar, género, edad, pantalla actual)
viven en st.session_state.
- Para que una persona pueda leer a otra y abrir un chat privado, los mensajes,
solicitudes y chats se guardan en un almacén en MEMORIA compartido por todas
las sesiones (st.cache_resource). No hay base de datos externa: si se reinicia
el servidor, todo se borra.
- Nunca se piden ni guardan nombres reales, correos, teléfonos ni fotos.
"""

import threading
import uuid
from datetime import datetime
from zoneinfo import ZoneInfo

import streamlit as st

# ---------------------------------------------------------------------------
# CONFIGURACIÓN GENERAL
# ---------------------------------------------------------------------------
st.set_page_config(page_title="Solo Habla", page_icon="🗣️", layout="centered")

ZONA_HORARIA = ZoneInfo("America/Guayaquil")  # Hora local de Ecuador

# Avatares predefinidos: nombre -> emoji
AVATARES = {
    "Sol": "☀️",
    "Luna": "🌙",
    "Árbol": "🌳",
    "Estrella": "⭐",
    "Gato": "🐱",
    "Perro": "🐶",
    "Flor": "🌸",
    "Nube": "☁️",
    "Fuego": "🔥",
    "Montaña": "⛰️",
    "Mar": "🌊",
    "Arcoíris": "🌈",
}

OPCIONES_GENERO = ["Mujer", "Hombre", "Prefiero no decirlo"]
OPCIONES_EDAD = ["Menos de 18", "18-25", "26-40", "Más de 40", "Prefiero no decirlo"]
NO_DECIR = "Prefiero no decirlo"

# Las dos secciones del muro: clave interna -> título visible
SECCIONES = {
    "sentimos": "Cómo nos sentimos hoy",
    "ayudamos": "Nos ayudamos",
}


# ---------------------------------------------------------------------------
# ALMACÉN EN MEMORIA (compartido entre sesiones, sin base de datos)
# ---------------------------------------------------------------------------
@st.cache_resource
def obtener_almacen() -> dict:
    """Crea (una sola vez) el almacén en memoria del servidor."""
    return {
        "mensajes": [],      # publicaciones del muro (las nuevas van al inicio)
        "solicitudes": [],   # solicitudes "Quiero hablar contigo"
        "chats": {},         # chats privados: id -> datos del chat
        "lock": threading.Lock(),
    }


def ahora() -> str:
    """Fecha y hora actual en formato legible."""
    return datetime.now(ZONA_HORARIA).strftime("%d/%m/%Y %H:%M")


# ---------------------------------------------------------------------------
# ESTADO DE LA SESIÓN
# ---------------------------------------------------------------------------
def iniciar_estado():
    """Define valores por defecto en st.session_state."""
    defaults = {
        "pantalla": "bienvenida",
        "user_id": uuid.uuid4().hex,   # identificador anónimo, no es un dato personal
        "apodo": "",
        "avatar": None,                # nombre del avatar elegido
        "genero": NO_DECIR,
        "edad": NO_DECIR,
        "solicitudes_enviadas": set(),  # ids de publicaciones a las que ya pedí hablar
        "ignoradas": set(),             # solicitudes recibidas que decidí ignorar
        "chat_activo": None,
    }
    for clave, valor in defaults.items():
        st.session_state.setdefault(clave, valor)

    # Los mensajes del muro se exponen también vía st.session_state
    # (es una referencia a la misma lista compartida en memoria).
    st.session_state["mensajes"] = obtener_almacen()["mensajes"]


def ir_a(pantalla: str):
    """Cambia de pantalla y vuelve a ejecutar la app."""
    st.session_state["pantalla"] = pantalla
    st.rerun()


# ---------------------------------------------------------------------------
# PANTALLA 1 — BIENVENIDA
# ---------------------------------------------------------------------------
def pantalla_bienvenida():
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown("<h1 style='text-align:center'>🗣️ Solo Habla</h1>", unsafe_allow_html=True)
    st.markdown(
        "<h4 style='text-align:center; font-weight:400'>"
        "Bienvenido a Solo Habla. Un espacio donde nadie sabrá quién eres, "
        "pero alguien te escuchará."
        "</h4>",
        unsafe_allow_html=True,
    )
    st.markdown("<br>", unsafe_allow_html=True)
    _, centro, _ = st.columns([1, 1, 1])
    if centro.button("Comenzar", type="primary", use_container_width=True):
        ir_a("perfil")


# ---------------------------------------------------------------------------
# PANTALLA 2 — APODO Y AVATAR
# ---------------------------------------------------------------------------
def pantalla_perfil():
    st.header("Tu identidad anónima")
    st.write("Elige un apodo y un avatar que te represente. Nadie sabrá tu nombre real.")

    apodo = st.text_input(
        "Apodo",
        value=st.session_state["apodo"],
        max_chars=20,
        placeholder="Ej: Viajero silencioso",
    )

    st.markdown("**Elige tu avatar**")
    # Cuadrícula de 4 columnas; cada avatar es un botón-tarjeta.
    # El seleccionado se resalta con type="primary" (solo uno a la vez).
    items = list(AVATARES.items())
    for fila in range(0, len(items), 4):
        columnas = st.columns(4)
        for col, (nombre, emoji) in zip(columnas, items[fila:fila + 4]):
            seleccionado = st.session_state["avatar"] == nombre
            if col.button(
                f"{emoji}\n\n{nombre}",
                key=f"avatar_{nombre}",
                type="primary" if seleccionado else "secondary",
                use_container_width=True,
            ):
                st.session_state["avatar"] = nombre
                st.session_state["apodo"] = apodo.strip()  # conserva lo escrito
                st.rerun()

    if st.session_state["avatar"]:
        st.caption(f"Avatar elegido: {AVATARES[st.session_state['avatar']]} {st.session_state['avatar']}")

    if st.button("Continuar", type="primary"):
        # Validaciones: apodo y avatar obligatorios
        if not apodo.strip():
            st.error("Escribe un apodo para continuar.")
        elif not st.session_state["avatar"]:
            st.error("Selecciona un avatar para continuar.")
        else:
            st.session_state["apodo"] = apodo.strip()
            ir_a("opcional")


# ---------------------------------------------------------------------------
# PANTALLA 3 — INFORMACIÓN OPCIONAL
# ---------------------------------------------------------------------------
def pantalla_opcional():
    st.header("Ayúdanos a entendernos mejor")
    st.write("Todo es opcional.")

    genero = st.radio(
        "Soy",
        OPCIONES_GENERO,
        index=OPCIONES_GENERO.index(st.session_state["genero"]),
    )
    edad = st.radio(
        "Edad",
        OPCIONES_EDAD,
        index=OPCIONES_EDAD.index(st.session_state["edad"]),
    )

    if st.button("Ir al muro", type="primary"):
        st.session_state["genero"] = genero
        st.session_state["edad"] = edad
        ir_a("muro")


# ---------------------------------------------------------------------------
# PANTALLA 4 — EL MURO
# ---------------------------------------------------------------------------
def datos_opcionales(genero: str, edad: str) -> str:
    """Devuelve el texto de género/edad solo si la persona los compartió."""
    partes = [d for d in (genero, edad) if d and d != NO_DECIR]
    return " · ".join(partes)


def publicar(seccion: str, texto: str):
    """Agrega una publicación nueva al inicio del muro."""
    almacen = obtener_almacen()
    publicacion = {
        "id": uuid.uuid4().hex,
        "autor_id": st.session_state["user_id"],
        "apodo": st.session_state["apodo"],
        "avatar": AVATARES[st.session_state["avatar"]],
        "genero": st.session_state["genero"],
        "edad": st.session_state["edad"],
        "texto": texto,
        "fecha": ahora(),
        "seccion": seccion,
        "escuchan": set(),  # ids de quienes pulsaron "Te escucho"
    }
    with almacen["lock"]:
        almacen["mensajes"].insert(0, publicacion)  # los nuevos arriba


def enviar_solicitud(pub: dict):
    """
    Pantalla 5 (lógica): registra una solicitud de conversación.
    Si la otra persona ya había pedido hablar conmigo, se abre el chat al instante.
    """
    almacen = obtener_almacen()
    yo = st.session_state["user_id"]

    with almacen["lock"]:
        # ¿La otra persona ya me había enviado una solicitud pendiente?
        inversa = next(
            (
                s for s in almacen["solicitudes"]
                if s["de_id"] == pub["autor_id"] and s["para_id"] == yo
                and s["estado"] == "pendiente"
            ),
            None,
        )
        if inversa:
            abrir_chat(almacen, inversa)
        else:
            almacen["solicitudes"].append({
                "id": uuid.uuid4().hex,
                "de_id": yo,
                "de_apodo": st.session_state["apodo"],
                "de_avatar": AVATARES[st.session_state["avatar"]],
                "para_id": pub["autor_id"],
                "para_apodo": pub["apodo"],
                "para_avatar": pub["avatar"],
                "estado": "pendiente",
            })
    st.session_state["solicitudes_enviadas"].add(pub["id"])


def abrir_chat(almacen: dict, solicitud: dict):
    """Marca la solicitud como aceptada y crea el chat privado (llamar con lock tomado)."""
    solicitud["estado"] = "aceptada"
    almacen["chats"][solicitud["id"]] = {
        "id": solicitud["id"],
        "miembros": {
            solicitud["de_id"]: (solicitud["de_avatar"], solicitud["de_apodo"]),
            solicitud["para_id"]: (solicitud["para_avatar"], solicitud["para_apodo"]),
        },
        "mensajes": [],
    }


def tarjeta_publicacion(pub: dict, seccion: str):
    """Dibuja un mensaje del muro con sus botones."""
    yo = st.session_state["user_id"]
    es_mio = pub["autor_id"] == yo

    with st.container(border=True):
        col_av, col_info = st.columns([1, 7])
        col_av.markdown(f"<div style='font-size:2.5rem'>{pub['avatar']}</div>", unsafe_allow_html=True)
        with col_info:
            st.markdown(f"**{pub['apodo']}**" + (" _(tú)_" if es_mio else ""))
            extra = datos_opcionales(pub["genero"], pub["edad"])
            if extra:
                st.caption(extra)
        st.write(pub["texto"])
        st.caption(f"🕒 {pub['fecha']}")

        b1, b2 = st.columns(2)
        # Botón "Te escucho": alterna mi apoyo y muestra cuántas personas escuchan
        total = len(pub["escuchan"])
        if b1.button(f"👂 Te escucho ({total})", key=f"escucho_{seccion}_{pub['id']}", use_container_width=True):
            if yo in pub["escuchan"]:
                pub["escuchan"].discard(yo)
            else:
                pub["escuchan"].add(yo)
            st.rerun()

        # Botón "Quiero hablar contigo": no tiene sentido con mis propios mensajes
        if b2.button(
            "💬 Quiero hablar contigo",
            key=f"hablar_{seccion}_{pub['id']}",
            use_container_width=True,
            disabled=es_mio or pub["id"] in st.session_state["solicitudes_enviadas"],
        ):
            enviar_solicitud(pub)
            st.rerun()

        # PANTALLA 5 — mensaje tras enviar la solicitud
        if pub["id"] in st.session_state["solicitudes_enviadas"]:
            st.info("Solicitud enviada. Si la otra persona también quiere, se abrirá un espacio privado.")


def seccion_muro(seccion: str):
    """Formulario para publicar + lista de mensajes de una sección."""
    with st.form(f"form_{seccion}", clear_on_submit=True):
        texto = st.text_area("¿Qué necesitas compartir hoy?", max_chars=1000, height=120)
        enviar = st.form_submit_button("Publicar", type="primary")
    if enviar:
        if texto.strip():
            publicar(seccion, texto.strip())
            st.rerun()
        else:
            st.warning("Escribe algo antes de publicar.")

    publicaciones = [p for p in st.session_state["mensajes"] if p["seccion"] == seccion]
    if not publicaciones:
        st.caption("Aún no hay mensajes aquí. Sé la primera persona en compartir.")
    for pub in publicaciones:
        tarjeta_publicacion(pub, seccion)


@st.fragment(run_every=4)
def panel_notificaciones():
    """
    Se refresca solo cada 4 segundos. Muestra:
    - solicitudes recibidas (aceptar o ignorar en silencio)
    - chats privados abiertos
    """
    almacen = obtener_almacen()
    yo = st.session_state["user_id"]

    recibidas = [
        s for s in almacen["solicitudes"]
        if s["para_id"] == yo and s["estado"] == "pendiente"
        and s["id"] not in st.session_state["ignoradas"]
    ]
    mis_chats = [c for c in almacen["chats"].values() if yo in c["miembros"]]

    if not recibidas and not mis_chats:
        return

    with st.container(border=True):
        for s in recibidas:
            st.write(f"{s['de_avatar']} **{s['de_apodo']}** quiere hablar contigo.")
            c1, c2 = st.columns(2)
            if c1.button("Aceptar", key=f"acepta_{s['id']}", type="primary", use_container_width=True):
                with almacen["lock"]:
                    abrir_chat(almacen, s)
                st.session_state["chat_activo"] = s["id"]
                st.session_state["pantalla"] = "chat"
                st.rerun(scope="app")
            # "Ignorar" solo oculta la solicitud para mí; la otra persona no recibe ningún aviso
            if c2.button("Ignorar", key=f"ignora_{s['id']}", use_container_width=True):
                st.session_state["ignoradas"].add(s["id"])
                st.rerun(scope="app")

        for c in mis_chats:
            otro_id = next(m for m in c["miembros"] if m != yo)
            avatar, apodo = c["miembros"][otro_id]
            if st.button(f"💬 Abrir chat privado con {avatar} {apodo}", key=f"abrir_{c['id']}", use_container_width=True):
                st.session_state["chat_activo"] = c["id"]
                st.session_state["pantalla"] = "chat"
                st.rerun(scope="app")


def pantalla_muro():
    st.title("🗣️ El muro")
    st.caption("Si estás en peligro o en una emergencia, llama al 911 (Ecuador). Este espacio no reemplaza ayuda profesional.")

    panel_notificaciones()

    if st.button("🔄 Actualizar muro"):
        st.rerun()

    pestañas = st.tabs(list(SECCIONES.values()))
    for pestaña, seccion in zip(pestañas, SECCIONES):
        with pestaña:
            seccion_muro(seccion)


# ---------------------------------------------------------------------------
# PANTALLA 5 (continuación) — CHAT PRIVADO ANÓNIMO
# ---------------------------------------------------------------------------
@st.fragment(run_every=3)
def mensajes_chat(chat_id: str):
    """Muestra los mensajes del chat y se refresca solo cada 3 segundos."""
    chat = obtener_almacen()["chats"].get(chat_id)
    if not chat:
        return
    yo = st.session_state["user_id"]
    if not chat["mensajes"]:
        st.caption("El espacio es tuyo. Puedes empezar cuando quieras.")
    for m in chat["mensajes"]:
        autor = "user" if m["autor_id"] == yo else "assistant"
        avatar = chat["miembros"][m["autor_id"]][0]
        with st.chat_message(autor, avatar=avatar):
            st.write(m["texto"])
            st.caption(m["fecha"])


def pantalla_chat():
    almacen = obtener_almacen()
    chat = almacen["chats"].get(st.session_state["chat_activo"])
    yo = st.session_state["user_id"]

    if not chat or yo not in chat["miembros"]:
        ir_a("muro")
        return

    otro_id = next(m for m in chat["miembros"] if m != yo)
    avatar, apodo = chat["miembros"][otro_id]

    st.header(f"{avatar} {apodo}")
    st.caption("Chat privado y anónimo. No compartas datos personales si no quieres.")
    if st.button("← Volver al muro"):
        ir_a("muro")

    mensajes_chat(chat["id"])

    texto = st.chat_input("Escribe un mensaje")
    if texto and texto.strip():
        with almacen["lock"]:
            chat["mensajes"].append({"autor_id": yo, "texto": texto.strip(), "fecha": ahora()})
        st.rerun()


# ---------------------------------------------------------------------------
# BARRA LATERAL Y ENRUTADOR PRINCIPAL
# ---------------------------------------------------------------------------
def barra_lateral():
    """Muestra quién eres (solo apodo y avatar) y permite salir borrando tus datos."""
    if st.session_state["pantalla"] in ("bienvenida", "perfil"):
        return
    with st.sidebar:
        st.markdown(f"### {AVATARES[st.session_state['avatar']]} {st.session_state['apodo']}")
        st.caption("Tu identidad anónima")
        if st.button("Salir y borrar mis datos"):
            st.session_state.clear()
            st.rerun()


def main():
    iniciar_estado()
    barra_lateral()

    pantalla = st.session_state["pantalla"]
    # Protección: no se puede entrar al muro/chat sin apodo y avatar
    if pantalla in ("opcional", "muro", "chat") and not (st.session_state["apodo"] and st.session_state["avatar"]):
        pantalla = "perfil"
        st.session_state["pantalla"] = pantalla

    if pantalla == "bienvenida":
        pantalla_bienvenida()
    elif pantalla == "perfil":
        pantalla_perfil()
    elif pantalla == "opcional":
        pantalla_opcional()
    elif pantalla == "muro":
        pantalla_muro()
    elif pantalla == "chat":
        pantalla_chat()


main()
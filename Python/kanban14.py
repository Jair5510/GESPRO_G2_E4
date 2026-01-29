# -*- coding: utf-8 -*-
"""
Created on Tue Jan 27 13:39:32 2026

@author: batir
"""

import streamlit as st
import json
import hashlib
import os
import shutil
import matplotlib.pyplot as plt

st.set_page_config(layout="wide")

COLUMNS = ["Backlog", "Ready", "Ongoing", "Deploy", "Live"]

AVATAR_DIR = "avatars"
USERS_FILE = "users3.json"

os.makedirs(AVATAR_DIR, exist_ok=True)

# -------------------------
# TEMA
# -------------------------
if "theme" not in st.session_state:
    st.session_state.theme = "dark"

if st.session_state.theme == "dark":
    st.markdown(
        """
        <style>
        body, .stApp {
            background-color: #0e1117;
            color: #fafafa;
        }
        </style>
        """,
        unsafe_allow_html=True
    )
else:
    st.markdown(
        """
        <style>
        body, .stApp {
            background-color: #ffffff;
            color: #000000;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

# -------------------------
# AUTENTICACIÓN
# -------------------------
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

with open(USERS_FILE, "r", encoding="utf-8") as f:
    USERS = json.load(f)["users"]

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
    st.session_state.username = None
    st.session_state.role = None

if not st.session_state.authenticated:
    st.title("🔐 Login")

    user = st.text_input("Usuario")
    pwd = st.text_input("Contraseña", type="password")

    if st.button("Entrar"):
        if user in USERS and USERS[user]["password"] == hash_password(pwd):
            st.session_state.authenticated = True
            st.session_state.username = user
            st.session_state.role = USERS[user]["role"]
            st.rerun()
        else:
            st.error("Usuario o contraseña incorrectos")

    st.stop()

# -------------------------
# ESTADO
# -------------------------
if "board" not in st.session_state:
    st.session_state.board = {c: [] for c in COLUMNS}
    st.session_state.next_id = 1
    st.session_state.wip_limits = {c: 5 for c in COLUMNS}

if "editing_task" not in st.session_state:
    st.session_state.editing_task = None

if "board_loaded" not in st.session_state:
    st.session_state.board_loaded = False

# -------------------------
# FUNCIONES
# -------------------------
def add_task(title, owner, bg, text, estimated_time):
    st.session_state.board["Backlog"].append({
        "id": st.session_state.next_id,
        "title": title,
        "owner": owner,
        "bg": bg,
        "text": text,
        "created_by": st.session_state.username,
        "estimated_time": estimated_time,
        "real_time": 0.0
    })
    st.session_state.next_id += 1


def move_task(task, from_col, direction):
    idx = COLUMNS.index(from_col)
    new_idx = idx + direction

    if new_idx < 0 or new_idx >= len(COLUMNS):
        return

    target_col = COLUMNS[new_idx]

    if len(st.session_state.board[target_col]) >= st.session_state.wip_limits[target_col]:
        st.warning(f"🚦 Límite WIP alcanzado en {target_col}")
        return

    st.session_state.board[from_col].remove(task)
    st.session_state.board[target_col].append(task)


def delete_task(task, col):
    st.session_state.board[col].remove(task)


def save_board():
    st.download_button(
        "💾 Descargar tablero",
        json.dumps(
            {
                "board": st.session_state.board,
                "next_id": st.session_state.next_id,
                "wip_limits": st.session_state.wip_limits
            },
            indent=2
        ),
        file_name="kanban_board.json"
    )


def load_board_once(file):
    data = json.load(file)
    st.session_state.board = data["board"]
    st.session_state.next_id = data["next_id"]
    st.session_state.wip_limits = data.get("wip_limits", st.session_state.wip_limits)
    st.session_state.board_loaded = True
    st.session_state.editing_task = None


def can_edit(task):
    if st.session_state.role == "admin":
        return True
    if st.session_state.role == "edit" and task["created_by"] == st.session_state.username:
        return True
    return False


def can_move(task):
    return can_edit(task)

# -------------------------
# SIDEBAR
# -------------------------
st.sidebar.title("🛠️ Kanban")
st.sidebar.markdown(f"👤 **{st.session_state.username}**")
st.sidebar.markdown(f"🔑 Rol: `{st.session_state.role}`")

avatar_path = USERS[st.session_state.username].get("avatar", "")
if avatar_path and os.path.exists(avatar_path):
    st.sidebar.image(avatar_path, width=120)

uploaded_avatar = st.sidebar.file_uploader(
    "🖼️ Cambiar avatar (usa la ❌ para continuar)",
    type=["png", "jpg", "jpeg"]
)

if uploaded_avatar:
    ext = uploaded_avatar.name.split(".")[-1]
    new_path = os.path.join(AVATAR_DIR, f"{st.session_state.username}.{ext}")

    with open(new_path, "wb") as f:
        f.write(uploaded_avatar.getbuffer())

    USERS[st.session_state.username]["avatar"] = new_path
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump({"users": USERS}, f, indent=2)

    st.rerun()

theme_choice = st.sidebar.radio(
    "🎨 Tema",
    ["dark", "light"],
    index=0 if st.session_state.theme == "dark" else 1
)

if theme_choice != st.session_state.theme:
    st.session_state.theme = theme_choice
    st.rerun()

if st.sidebar.button("🚪 Logout"):
    st.session_state.authenticated = False
    st.session_state.username = None
    st.session_state.role = None
    st.session_state.editing_task = None
    st.rerun()

if st.session_state.role in ("admin", "edit"):
    title = st.sidebar.text_input("Título")
    owner = st.sidebar.text_input("Responsable")
    estimated_time = st.sidebar.number_input(
        "⏱️ Tiempo estimado (horas)",
        min_value=0.0,
        step=0.5
    )
    bg_color = st.sidebar.color_picker("Color tarjeta", "#fff9a6")
    text_color = st.sidebar.color_picker("Color texto", "#000000")

    if st.sidebar.button("➕ Crear tarea"):
        if title.strip():
            add_task(title, owner, bg_color, text_color, estimated_time)

st.sidebar.markdown("---")
st.sidebar.subheader("🚦 WIP Limits")

if st.session_state.role == "admin":
    for col in COLUMNS:
        st.session_state.wip_limits[col] = st.sidebar.number_input(
            col,
            min_value=1,
            value=st.session_state.wip_limits[col],
            key=f"wip-{col}"
        )

st.sidebar.markdown("---")
save_board()

uploaded = st.sidebar.file_uploader("📂 Abrir tablero", type="json")
if uploaded and not st.session_state.board_loaded:
    load_board_once(uploaded)

# -------------------------
# TABLERO
# -------------------------
cols = st.columns(len(COLUMNS))

for col_idx, col_name in enumerate(COLUMNS):
    with cols[col_idx]:
        st.markdown(
            f"### {col_name} "
            f"({len(st.session_state.board[col_name])}/"
            f"{st.session_state.wip_limits[col_name]})"
        )

        for task in list(st.session_state.board[col_name]):
            st.markdown(
                f"""
                <div style="
                    background:{task['bg']};
                    color:{task['text']};
                    padding:10px;
                    border-radius:8px;
                    margin-bottom:6px;
                ">
                <strong>#{task['id']}</strong> {task['title']}<br>
                👤 {task['owner']}<br>
                🧑‍💻 {task['created_by']}<br>
                ⏱️ Estimado: {task['estimated_time']} h
                </div>
                """,
                unsafe_allow_html=True
            )

            if col_name == "Live" and can_edit(task):
                task["real_time"] = st.number_input(
                    "⏱️ Tiempo real (horas)",
                    min_value=0.0,
                    step=0.5,
                    value=task.get("real_time", 0.0),
                    key=f"real-{task['id']}"
                )

            c1, c2, c3, c4, _ = st.columns([1, 1, 1, 1, 4])

            if c1.button("⬅️", key=f"l-{task['id']}", disabled=not can_move(task)):
                move_task(task, col_name, -1)
                st.rerun()

            if c2.button("➡️", key=f"r-{task['id']}", disabled=not can_move(task)):
                move_task(task, col_name, 1)
                st.rerun()

            if c3.button("✏️", key=f"e-{task['id']}", disabled=not can_edit(task)):
                st.session_state.editing_task = task["id"]
                st.rerun()

            if c4.button("🗑️", key=f"d-{task['id']}", disabled=not can_edit(task)):
                delete_task(task, col_name)
                st.session_state.editing_task = None
                st.rerun()

            if st.session_state.editing_task == task["id"] and can_edit(task):
                new_title = st.text_input("Título", task["title"], key=f"title-{task['id']}")
                new_owner = st.text_input("Responsable", task["owner"], key=f"owner-{task['id']}")
                new_estimated = st.number_input(
                    "⏱️ Tiempo estimado (horas)",
                    min_value=0.0,
                    step=0.5,
                    value=task["estimated_time"],
                    key=f"est-{task['id']}"
                )
                new_bg = st.color_picker("Color tarjeta", task["bg"], key=f"bg-{task['id']}")
                new_text = st.color_picker("Color texto", task["text"], key=f"text-{task['id']}")

                if st.button("💾 Guardar", key=f"save-{task['id']}"):
                    task.update({
                        "title": new_title,
                        "owner": new_owner,
                        "estimated_time": new_estimated,
                        "bg": new_bg,
                        "text": new_text
                    })
                    st.session_state.editing_task = None
                    st.rerun()

# -------------------------
# GRÁFICA
# -------------------------
column_estimated = [sum(t["estimated_time"] for t in st.session_state.board[c]) for c in COLUMNS]
column_real = [sum(t["real_time"] for t in st.session_state.board[c]) for c in COLUMNS]

blue = "#1f77b4" if st.session_state.theme == "dark" else "#003f88"
orange = "#ff7f0e"

fig, ax = plt.subplots(figsize=(10, 4))
ax.bar(COLUMNS, column_estimated, color=blue, alpha=0.8, label="Horas previstas")

live_idx = COLUMNS.index("Live")
ax.bar("Live", column_real[live_idx], color=orange, alpha=0.6, label="Horas reales")

ax.set_title("Horas previstas")
ax.set_ylabel("Horas")
ax.legend()

st.markdown("---")
st.pyplot(fig)

st.markdown(
    f"<div style='text-align:right;font-size:18px'><strong>Total horas previstas:</strong> {sum(column_estimated):.1f} h</div>",
    unsafe_allow_html=True
)

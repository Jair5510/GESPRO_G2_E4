# -*- coding: utf-8 -*-
"""
Created on Tue Jan 27 13:39:32 2026

@author: batir
"""

import streamlit as st
import json
import hashlib

st.set_page_config(layout="wide")

COLUMNS = ["Backlog", "Ready", "Ongoing", "Deploy", "Live"]

# -------------------------
# AUTENTICACIÓN
# -------------------------
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def load_users():
    with open("users.json", "r", encoding="utf-8") as f:
        return json.load(f)["users"]

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
    st.session_state.user = None
    st.session_state.role = None

if not st.session_state.authenticated:
    st.title("🔐 Login Kanban")

    username = st.text_input("Usuario")
    password = st.text_input("Contraseña", type="password")

    if st.button("Ingresar"):
        users = load_users()
        if username in users:
            if hash_password(password) == users[username]["password"]:
                st.session_state.authenticated = True
                st.session_state.user = username
                st.session_state.role = users[username]["role"]
                st.rerun()
            else:
                st.error("❌ Contraseña incorrecta")
        else:
            st.error("❌ Usuario no existe")

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

ROLE = st.session_state.role

# -------------------------
# FUNCIONES
# -------------------------
def can_edit():
    return ROLE in ["admin", "edit"]

def can_admin():
    return ROLE == "admin"

def add_task(title, owner, bg, text):
    st.session_state.board["Backlog"].append({
        "id": st.session_state.next_id,
        "title": title,
        "owner": owner,
        "bg": bg,
        "text": text
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

# -------------------------
# SIDEBAR
# -------------------------
st.sidebar.title("🛠️ Kanban")
st.sidebar.markdown(f"👤 **Usuario:** {st.session_state.user}")
st.sidebar.markdown(f"🔑 **Rol:** {ROLE}")

if can_edit():
    title = st.sidebar.text_input("Título")
    owner = st.sidebar.text_input("Responsable")
    bg_color = st.sidebar.color_picker("Color tarjeta", "#fff9a6")
    text_color = st.sidebar.color_picker("Color texto", "#000000")

    if st.sidebar.button("➕ Crear tarea"):
        if title.strip():
            add_task(title, owner, bg_color, text_color)

st.sidebar.markdown("---")
st.sidebar.subheader("🚦 WIP Limits")

for col in COLUMNS:
    st.session_state.wip_limits[col] = st.sidebar.number_input(
        col,
        min_value=1,
        value=st.session_state.wip_limits[col],
        disabled=not can_admin(),
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
                👤 {task['owner']}
                </div>
                """,
                unsafe_allow_html=True
            )

            if can_edit():
                c1, c2, c3, c4, _ = st.columns([1, 1, 1, 1, 4])

                if c1.button("⬅️", key=f"l-{task['id']}", disabled=col_idx == 0):
                    move_task(task, col_name, -1)
                    st.rerun()

                if c2.button("➡️", key=f"r-{task['id']}", disabled=col_idx == len(COLUMNS) - 1):
                    move_task(task, col_name, 1)
                    st.rerun()

                if c3.button("✏️", key=f"e-{task['id']}"):
                    st.session_state.editing_task = task["id"]
                    st.rerun()

                if c4.button("🗑️", key=f"d-{task['id']}"):
                    delete_task(task, col_name)
                    st.session_state.editing_task = None
                    st.rerun()

            if can_edit() and st.session_state.editing_task == task["id"]:
                new_title = st.text_input("Título", task["title"], key=f"title-{task['id']}")
                new_owner = st.text_input("Responsable", task["owner"], key=f"owner-{task['id']}")
                new_bg = st.color_picker("Color tarjeta", task["bg"], key=f"bg-{task['id']}")
                new_text = st.color_picker("Color texto", task["text"], key=f"text-{task['id']}")

                if st.button("💾 Guardar", key=f"save-{task['id']}"):
                    task.update({
                        "title": new_title,
                        "owner": new_owner,
                        "bg": new_bg,
                        "text": new_text
                    })
                    st.session_state.editing_task = None
                    st.rerun()

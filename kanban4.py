import streamlit as st
import json

st.set_page_config(layout="wide")

COLUMNS = ["Backlog", "Ready", "Ongoing", "Deploy", "Live"]

# -------------------------
# ESTADO
# -------------------------
if "board" not in st.session_state:
    st.session_state.board = {c: [] for c in COLUMNS}
    st.session_state.next_id = 1


# -------------------------
# FUNCIONES
# -------------------------
def add_task(title):
    st.session_state.board["Backlog"].append({
        "id": st.session_state.next_id,
        "title": title
    })
    st.session_state.next_id += 1


def move_task(task, from_col, direction):
    idx = COLUMNS.index(from_col)
    new_idx = idx + direction

    if new_idx < 0 or new_idx >= len(COLUMNS):
        return  # no se mueve

    st.session_state.board[from_col].remove(task)
    st.session_state.board[COLUMNS[new_idx]].append(task)


def save_board():
    st.download_button(
        "💾 Descargar tablero",
        json.dumps(
            {
                "board": st.session_state.board,
                "next_id": st.session_state.next_id
            },
            indent=2
        ),
        file_name="kanban_board.json"
    )


def load_board(file):
    data = json.load(file)
    st.session_state.board = data["board"]
    st.session_state.next_id = data["next_id"]


# -------------------------
# SIDEBAR
# -------------------------
st.sidebar.title("🛠️ Kanban")

title = st.sidebar.text_input("Nueva tarea")

if st.sidebar.button("➕ Crear tarea"):
    if title.strip():
        add_task(title)

st.sidebar.markdown("---")
save_board()

uploaded = st.sidebar.file_uploader("📂 Abrir tablero", type="json")
if uploaded:
    load_board(uploaded)


# -------------------------
# TABLERO KANBAN
# -------------------------
cols = st.columns(len(COLUMNS))

for col_idx, col_name in enumerate(COLUMNS):
    with cols[col_idx]:
        st.markdown(f"### {col_name}")

        for task in st.session_state.board[col_name]:
            st.markdown(
                f"""
                <div style="
                    background:#fff9a6;
                    padding:10px;
                    border-radius:6px;
                    margin-bottom:8px;
                ">
                <strong>#{task['id']}</strong> {task['title']}
                </div>
                """,
                unsafe_allow_html=True
            )

            btn_cols = st.columns([1, 1, 6])

            with btn_cols[0]:
                if st.button(
                    "⬅️",
                    key=f"left-{task['id']}",
                    disabled=col_idx == 0
                ):
                    move_task(task, col_name, -1)
                    st.rerun()

            with btn_cols[1]:
                if st.button(
                    "➡️",
                    key=f"right-{task['id']}",
                    disabled=col_idx == len(COLUMNS) - 1
                ):
                    move_task(task, col_name, 1)
                    st.rerun()

import streamlit as st
import json
import streamlit.components.v1 as components

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
# HTML + DRAG & DROP
# -------------------------
def kanban_html(board):
    return f"""
    <html>
    <head>
      <script src="https://cdn.jsdelivr.net/npm/sortablejs@1.15.0/Sortable.min.js"></script>
      <style>
        body {{ font-family: sans-serif; }}
        .board {{ display: flex; gap: 16px; }}
        .column {{
          background: #f4f4f4;
          padding: 10px;
          width: 220px;
          border-radius: 10px;
        }}
        .card {{
          background: #fff9a6;
          padding: 10px;
          margin-bottom: 8px;
          border-radius: 6px;
          cursor: grab;
        }}
      </style>
    </head>
    <body>
      <div class="board">
        {''.join(
            f'''
            <div class="column">
              <h4>{col}</h4>
              <div id="{col}">
                {''.join(
                    f'<div class="card" data-id="{t["id"]}">#{t["id"]} {t["title"]}</div>'
                    for t in board[col]
                )}
              </div>
            </div>
            '''
            for col in COLUMNS
        )}
      </div>

      <script>
        const columns = {COLUMNS};
        columns.forEach(col => {{
          new Sortable(document.getElementById(col), {{
            group: "kanban",
            animation: 150
          }});
        }});
      </script>
    </body>
    </html>
    """


components.html(
    kanban_html(st.session_state.board),
    height=600,
    scrolling=True
)

st.info("🔁 Drag & drop visual (el estado se mantiene en memoria).")

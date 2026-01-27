import pandas as pd


class KanbanBoard:
    def __init__(self):
        self.columns = ["backlog", "ready", "ongoing", "deploy", "live"]
        self.board = pd.DataFrame(columns=self.columns)
        self.next_id = 1  # ID único autoincremental

    def show_board(self):
        print("\n=========== KANBAN BOARD ===========")
        if self.board.empty:
            print("Tablero vacío")
        else:
            display = self.board.copy()

            for col in self.columns:
                display[col] = display[col].apply(
                    lambda x: f"[{x['id']}] {x['title']}" if isinstance(x, dict) else ""
                )

            print(display.fillna(""))
        print("===================================\n")

    def add_task(self, title):
        task = {
            "id": self.next_id,
            "title": title
        }
        self.next_id += 1

        # crear fila vacía
        new_index = len(self.board)
        self.board.loc[new_index] = [None] * len(self.columns)

        # asignar tarea de forma segura
        self.board.at[new_index, "backlog"] = task

        print(f"Tarea creada con ID {task['id']} en backlog")

    def move_task(self, task_id, from_column, to_column):
        if from_column not in self.columns or to_column not in self.columns:
            print("Columna inválida")
            return

        for idx, row in self.board.iterrows():
            cell = row[from_column]
            if isinstance(cell, dict) and cell["id"] == task_id:
                self.board.at[idx, from_column] = None
                self.board.at[idx, to_column] = cell

                # limpiar filas vacías
                self.board.dropna(how="all", inplace=True)
                self.board.reset_index(drop=True, inplace=True)

                print(f"Tarea {task_id} movida de {from_column} a {to_column}")
                return

        print(f"No se encontró la tarea {task_id} en {from_column}")


def menu():
    print("""
1. Ver tablero
2. Crear nueva tarea
3. Mover tarea
4. Salir
""")


if __name__ == "__main__":
    kanban = KanbanBoard()

    while True:
        menu()
        option = input("Selecciona una opción: ").strip()

        if option == "1":
            kanban.show_board()

        elif option == "2":
            title = input("Título de la tarea: ").strip()
            kanban.add_task(title)

        elif option == "3":
            try:
                task_id = int(input("ID de la tarea: "))
                from_col = input("Columna origen: ").strip().lower()
                to_col = input("Columna destino: ").strip().lower()
                kanban.move_task(task_id, from_col, to_col)
            except ValueError:
                print("ID inválido")

        elif option == "4":
            print("Saliendo del Kanban 👋")
            break

        else:
            print("Opción inválida")

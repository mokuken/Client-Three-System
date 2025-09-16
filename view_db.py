import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox
import ttkbootstrap as tb

DB_PATH = "instance/app.db"

class DatabaseManager:
    def __init__(self, db_path):
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()

    def get_tables(self):
        self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        return [t[0] for t in self.cursor.fetchall()]

    def get_table_columns(self, table):
        self.cursor.execute(f"PRAGMA table_info({table});")
        return self.cursor.fetchall()

    def get_all_rows(self, table):
        self.cursor.execute(f"SELECT * FROM {table};")
        return self.cursor.fetchall()

    def insert_row(self, table, columns, values):
        placeholders = ','.join(['?'] * len(columns))
        col_names = ','.join(columns)
        self.cursor.execute(f"INSERT INTO {table} ({col_names}) VALUES ({placeholders})", values)
        self.conn.commit()

    def update_row(self, table, columns, values, pk_col, pk_value):
        set_clause = ', '.join([f'{col}=?' for col in columns])
        self.cursor.execute(
            f"UPDATE {table} SET {set_clause} WHERE {pk_col}=?",
            values + [pk_value]
        )
        self.conn.commit()

    def delete_row(self, table, pk_col, pk_value):
        self.cursor.execute(f"DELETE FROM {table} WHERE {pk_col}=?", (pk_value,))
        self.conn.commit()

class SQLiteApp:
    def __init__(self, root, db_manager):
        self.db = db_manager
        self.root = root
        self.root.title("FarmHub Database")
        self.root.geometry("1100x700")
        self.root.configure(padx=20, pady=20)

        style = tb.Style("cosmo")

        # Top frame for selector and buttons
        top_frame = ttk.Frame(root)
        top_frame.pack(fill="x", pady=10)

        # Table selector (top left)
        self.table_combo = ttk.Combobox(top_frame, state="readonly")
        self.table_combo.pack(side="left", padx=(0, 10))
        self.table_combo.bind("<<ComboboxSelected>>", self.load_table)

        # Button frame (top right)
        btn_frame = ttk.Frame(top_frame)
        btn_frame.pack(side="right")
        ttk.Button(btn_frame, text="Add Row", command=self.add_row).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Update Row", command=self.update_row).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Delete Row", command=self.delete_row).pack(side="left", padx=5)

        self.tree = ttk.Treeview(root, show="headings")
        self.tree.pack(expand=True, fill="both")

        self.load_tables()

    def load_tables(self):
        tables = self.db.get_tables()
        self.table_combo['values'] = tables
        if tables:
            self.table_combo.current(0)
            self.load_table()

    def load_table(self, event=None):
        table = self.table_combo.get()
        cols_info = self.db.get_table_columns(table)
        cols = [c[1] for c in cols_info]

        self.tree.delete(*self.tree.get_children())
        self.tree["columns"] = cols
        for col in cols:
            self.tree.heading(col, text=col, anchor="center")
            self.tree.column(col, width=120, anchor="center")

        for idx, row in enumerate(self.db.get_all_rows(table)):
            tag = 'evenrow' if idx % 2 == 0 else 'oddrow'
            self.tree.insert("", "end", values=row, tags=(tag,))

    def add_row(self):
        table = self.table_combo.get()
        cols_info = self.db.get_table_columns(table)
        cols = [c[1] for c in cols_info]

        form = tk.Toplevel(self.root)
        form.title(f"Add Row to {table}")
        form.configure(padx=20, pady=20)
        entries = {}
        row_num = 0
        for idx, col in enumerate(cols):
            if cols_info[idx][5] == 1 and cols_info[idx][3] == 1:
                continue
            tk.Label(form, text=col).grid(row=row_num, column=0, padx=8, pady=8, sticky="w")
            entry = tk.Entry(form)
            entry.grid(row=row_num, column=1, padx=8, pady=8)
            entries[col] = entry
            row_num += 1

        form.update_idletasks()
        root_x = self.root.winfo_x()
        root_y = self.root.winfo_y()
        root_w = self.root.winfo_width()
        root_h = self.root.winfo_height()
        form_w = form.winfo_width()
        form_h = form.winfo_height()
        x = root_x + (root_w // 2) - (form_w // 2)
        y = root_y + (root_h // 2) - (form_h // 2)
        form.geometry(f"+{x}+{y}")

        def submit():
            values = []
            insert_cols = []
            for idx, col in enumerate(cols):
                if cols_info[idx][5] == 1 and cols_info[idx][3] == 1:
                    continue
                insert_cols.append(col)
                values.append(entries[col].get())
            try:
                self.db.insert_row(table, insert_cols, values)
                self.load_table()
                form.destroy()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to add row: {e}")

        tk.Button(form, text="Submit", command=submit).grid(row=row_num, column=0, columnspan=2, pady=12)

    def update_row(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Error", "No row selected.")
            return
        row_values = self.tree.item(selected[0], "values")
        table = self.table_combo.get()
        cols_info = self.db.get_table_columns(table)
        cols = [c[1] for c in cols_info]

        form = tk.Toplevel(self.root)
        form.title(f"Update Row in {table}")
        form.configure(padx=20, pady=20)
        entries = {}
        row_num = 0
        for idx, col in enumerate(cols):
            tk.Label(form, text=col).grid(row=row_num, column=0, padx=8, pady=8, sticky="w")
            entry = tk.Entry(form)
            entry.grid(row=row_num, column=1, padx=8, pady=8)
            entry.insert(0, row_values[idx])
            entries[col] = entry
            row_num += 1

        form.update_idletasks()
        root_x = self.root.winfo_x()
        root_y = self.root.winfo_y()
        root_w = self.root.winfo_width()
        root_h = self.root.winfo_height()
        form_w = form.winfo_width()
        form_h = form.winfo_height()
        x = root_x + (root_w // 2) - (form_w // 2)
        y = root_y + (root_h // 2) - (form_h // 2)
        form.geometry(f"+{x}+{y}")

        def has_changes():
            for idx, col in enumerate(cols):
                if entries[col].get() != str(row_values[idx]):
                    return True
            return False

        def on_entry_change(event=None):
            if has_changes():
                update_btn.config(state="normal")
            else:
                update_btn.config(state="disabled")

        for entry in entries.values():
            entry.bind("<KeyRelease>", on_entry_change)

        def update():
            if not has_changes():
                return
            new_values = [entries[col].get() for col in cols[1:]]
            pk_col = cols[0]
            pk_value = row_values[0]
            try:
                self.db.update_row(table, cols[1:], new_values, pk_col, pk_value)
                self.load_table()
                form.destroy()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to update row: {e}")

        update_btn = tk.Button(form, text="Update", command=update, state="disabled")
        update_btn.grid(row=row_num, column=0, columnspan=2, pady=12)

    def delete_row(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Error", "No row selected.")
            return
        row_values = self.tree.item(selected[0], "values")
        table = self.table_combo.get()
        pk_col = self.tree["columns"][0]
        pk_value = row_values[0]
        self.db.delete_row(table, pk_col, pk_value)
        self.load_table()

if __name__ == "__main__":
    root = tb.Window(themename="flatly")
    db_manager = DatabaseManager(DB_PATH)
    app = SQLiteApp(root, db_manager)
    root.mainloop()

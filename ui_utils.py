import state
import csv
import os
from datetime import datetime
from log_utils import log_message
import tkinter as tk
from PIL import Image, ImageTk
from tkinter import scrolledtext, filedialog, messagebox

def load_image(path, size=(100, 50)):
    try:
        full_path = os.path.join(state.BASE_DIR, path)
        img = Image.open(full_path)
        img = img.resize(size, Image.LANCZOS)
        return ImageTk.PhotoImage(img)
    except Exception as e:
        log_message(f"Warning: Failed to load image {path} - {e}")
        return None

def preview_readme():
    try:
        readme_path = os.path.join(state.BASE_DIR,"resources", "READ_ME.txt")
        with open(readme_path, "r", encoding="utf-8") as file:
            readme_content = file.read()

        readme_window = tk.Toplevel()
        readme_window.title("README")
        readme_window.geometry("850x550")  # Set default size
        readme_window.resizable(True, True)  # Allow resizing

        readme_window.transient()
        readme_window.grab_set()
        readme_window.focus_set()  #

        text_area = scrolledtext.ScrolledText(readme_window, wrap=tk.WORD)
        text_area.pack(expand=True, fill="both", padx=10, pady=10)
        text_area.insert(tk.END, readme_content)
        text_area.config(state="disabled")  # Make it read-only

    except FileNotFoundError:
        messagebox.showerror("Error", "READ_ME.txt not found!")

def sort_by_column(col, reverse=None):
    if reverse is None:
        reverse = state.sort_orders.get(col, False)
    state.sort_orders[col] = not reverse

    if col == "Created Date":
        state.file_data = sorted(
            state.file_data,
            key=lambda x: datetime.strptime(x.get("createdDate", "1970-01-01T00:00:00Z"), "%Y-%m-%dT%H:%M:%SZ"),
            reverse=reverse
        )
    elif col == "Modified Date":
        state.file_data = sorted(
            state.file_data,
            key=lambda x: datetime.strptime(x.get("modifiedDate", "1970-01-01T00:00:00Z"), "%Y-%m-%dT%H:%M:%SZ"),
            reverse=reverse
        )
    elif col == "Size":
        state.file_data = sorted(
            state.file_data,
            key=lambda x: int(x.get("size", 0)),
            reverse=reverse
        )
    else:
        state.file_data = sorted(
            state.file_data,
            key=lambda x: x.get("name", "").lower(),
            reverse=reverse
        )

    state.file_tree.delete(*state.file_tree.get_children())

    for file in state.file_data:
        state.file_tree.insert(
            "",
            "end",
            values=(
                file.get("name", "N/A"),
                file.get("size", 0),
                file.get("createdDate", "N/A"),
                file.get("modifiedDate", "N/A"),
                file.get("scanStatus", "N/A"),
            ),
        )

    state.file_tree.heading(col, command=lambda _col=col: sort_by_column(_col, state.sort_orders[col]))

def apply_filter(*args):

    filter_text = state.filter_entry.get().lower()
    state.file_tree.delete(*state.file_tree.get_children())

    for file in state.file_data:
        file_name = file.get("name", "").lower()
        if filter_text in file_name:
            state.file_tree.insert(
                "",
                "end",
                values=(
                    file.get("name", "N/A"),
                    file.get("size", 0),
                    file.get("createdDate", "N/A"),
                    file.get("modifiedDate", "N/A"),
                    file.get("scanStatus", "N/A"),
                ),
            )

def export_to_csv():
    if not state.file_data:
        log_message("Error: No data available to export.")
        messagebox.showerror("Export Error", "No data available to export.")
        return

    file_path = filedialog.asksaveasfilename(
        defaultextension=".csv",
        filetypes=[("CSV files", "*.csv"), ("All Files", "*.*")],
        title="Save As"
    )

    if not file_path:
        return

    try:
        with open(file_path, mode="w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow(["Name", "Size", "Created Date", "Modified Date", "Scan Status"])  # Header
            for file in state.file_data:
                writer.writerow([
                    file.get("name", "N/A"),
                    file.get("size", 0),
                    file.get("createdDate", "N/A"),
                    file.get("modifiedDate", "N/A"),
                    file.get("scanStatus", "N/A"),
                ])

        log_message(f"Data successfully exported to {file_path}")
        messagebox.showinfo("Success", f"Data successfully exported to:\n{file_path}")
    except Exception as e:
        log_message(f"ERROR! - exporting CSV: {e}")
        messagebox.showerror("Export Error", f"Failed to export data: {e}")

def reset_app():

    state.prefix_dropdown.set("")
    state.prefix_dropdown["values"] = []
    state.token_cache.clear()
    state.customer_config.clear()

    state.fts_host_name = None
    state.oci_iam_base_url = None
    state.oci_iam_scope = None
    state.client_id = None
    state.client_secret = None

    state.customer_dropdown.set("")

    state.filter_entry.delete(0, tk.END)
    state.file_tree.delete(*state.file_tree.get_children())
    state.log_window.delete("1.0", tk.END)
    log_message("Application reset successfully.")

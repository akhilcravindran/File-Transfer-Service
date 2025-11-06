import tkinter as tk
import os
from tkinter import ttk, scrolledtext, messagebox
from encryption_utils import initialize_encryption
#from log_utils import setup_logging
from file_operations import (
    upload_files, download_files, delete_selected_files, move_file,list_prefixes,list_files
)
from ui_utils import (
     load_image,apply_filter,sort_by_column,export_to_csv,preview_readme,reset_app
)
import state
from config_utils import load_config,set_customer_config,add_customer_keys

def launch_main_ui():
    root = tk.Tk()
    root.withdraw()
    initialize_encryption(root)

    root.title("File Transfer Service")
    root.geometry("950x630")
    logo_frame = tk.Frame(root)
    logo_frame.pack(pady=5, padx=10, anchor="w")

    company_logo_path = os.path.join(state.BASE_DIR, "resources", "company_logo.PNG")
    fts_logo_path = os.path.join(state.BASE_DIR, "resources", "fts_logo.PNG")

    olr_logo = load_image(company_logo_path, size=(115, 70))
    fts_logo = load_image(fts_logo_path, size=(120, 70))



    if olr_logo:
        tk.Label(logo_frame, image=olr_logo).pack(side="left", padx=5)
    if fts_logo:
        tk.Label(logo_frame, image=fts_logo).pack(side="left", padx=5)

    state.customer_frame = tk.Frame(root)
    state.customer_frame.pack(pady=5, padx=10, fill="x")

    state.prefix_frame = tk.Frame(root)
    state.prefix_frame.pack(pady=5, padx=10, fill="x")

    tk.Label(state.customer_frame, text="Select Customer:").pack(side="left", padx=5)
    state.customer_dropdown = ttk.Combobox(state.customer_frame, width=state.dropdown_width, state="readonly")
    state.customer_dropdown.pack(side="left", padx=16)
    load_config()
    state.customer_dropdown["values"] = [s for s in state.config.sections() if s != "encryption"]
    state.customer_dropdown.pack(side="left", padx=16)
    state.customer_dropdown.bind("<<ComboboxSelected>>", set_customer_config)

    tk.Label(state.prefix_frame, text="Select Prefix:").pack(side="left", padx=5)
    state.prefix_dropdown = ttk.Combobox(state.prefix_frame, width=state.dropdown_width, state="readonly")
    state.prefix_dropdown.pack(side="left", padx=38)

    tk.Button(state.prefix_frame, text="List Prefixes", command=list_prefixes).pack(side="left", padx=5)
    tk.Button(state.prefix_frame, text="List Files", command=list_files).pack(side="left", padx=5)
    tk.Button(state.prefix_frame, text="Upload", command=upload_files).pack(side="left", padx=5)
    tk.Button(state.prefix_frame, text="Download", command=download_files).pack(side="left", padx=5)
    tk.Button(state.prefix_frame, text="Delete", command=delete_selected_files).pack(side="left", padx=5)
    tk.Button(state.prefix_frame, text="Move", command=move_file).pack(side="left", padx=5)
    tk.Button(state.prefix_frame, text="⚙️", command=lambda: add_customer_keys(root)).pack(side="left", padx=5)
    tk.Button(state.prefix_frame, text="❓", command=preview_readme).pack(side="left", padx=5)

    tk.Button(state.prefix_frame, text="Reset", command=reset_app, bg="red", fg="white").pack(side="left", padx=20)
    tk.Button(state.prefix_frame, text="💾", command=export_to_csv,font=("Arial", 12, "bold")).pack(side="right", padx=5)

    filter_frame = tk.Frame(root)
    filter_frame.pack(pady=5, padx=10, fill="x")

    tk.Label(filter_frame, text="Filter by File Name:").pack(side="left", padx=5)
    state.filter_entry = tk.Entry(filter_frame, width=state.dropdown_width + 3)
    state.filter_entry.pack(side="left", padx=5)

    frame = tk.Frame(root)
    frame.pack(padx=10, pady=10, fill="both", expand=True)

    columns = ("Name", "Size", "Created Date", "Modified Date", "Scan Status")
    state.file_tree = ttk.Treeview(frame, columns=columns, show="headings", selectmode="extended")
    scroll_y = ttk.Scrollbar(frame, orient="vertical", command=state.file_tree.yview)
    state.file_tree.configure(yscroll=scroll_y.set)
    scroll_y.pack(side="right", fill="y")

    for col in columns:
        state.sort_orders[col] = False  # Default order is ascending
        state.file_tree.heading(col, text=col, command=lambda _col=col: sort_by_column(_col))
        state.file_tree.column(col, anchor="w")

    state.file_tree.pack(fill="both", expand=True)

    tk.Label(root, text="Log Messages:").pack(anchor="w", padx=10)
    state.log_window = scrolledtext.ScrolledText(root, height=15, wrap=tk.WORD)
    state.log_window.pack(padx=10, pady=5, fill="both", expand=False)

    state.filter_entry.bind("<KeyRelease>", apply_filter)  # Apply filter on key release

    def select_all(event):
        state.file_tree.selection_set(state.file_tree.get_children())

    state.file_tree.bind("<Control-a>", select_all)

    #setup_logging()

    root.deiconify()
    root.mainloop()

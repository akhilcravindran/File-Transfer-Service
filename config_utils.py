
import tkinter as tk
import os
from tkinter import ttk, messagebox
from configparser import ConfigParser
from encryption_utils import (encrypt_secret,decrypt_secret)
from log_utils import log_message
import state

def load_config():
    state.config = ConfigParser()
    state.config.read(state.CONFIG_FILE)

def set_customer_config(event=None):

    load_config()
    state.selected_customer = state.customer_dropdown.get()
    if state.selected_customer in state.config:
        state.customer_config = {key: value for key, value in state.config[state.selected_customer].items()}
        log_message(f"Customer '{state.selected_customer}' selected. Credentials updated.")

        state.fts_host_name = state.customer_config.get("fts_host_name")
        state.oci_iam_base_url = state.customer_config.get("oci_iam_base_url")
        state.oci_iam_scope = state.customer_config.get("oci_iam_scope")
        state.client_id = state.customer_config.get("client_id")
        state.client_secret = state.customer_config.get("client_secret")

        if state.client_secret:
            state.client_secret = decrypt_secret(state.client_secret)

        if not state.fts_host_name:
            log_message("ERROR! - FTS_HOST_NAME is missing in the configuration.")
            return

        if not state.oci_iam_base_url:
            log_message("ERROR! - OCI_IAM_BASE_URL is missing in the configuration.")
            return

        if not state.oci_iam_scope:
            log_message("ERROR! - OCI_IAM_SCOPE is missing in the configuration.")
            return

        if not state.client_id:
            log_message("ERROR! - CLIENT_ID is missing in the configuration.")
            return

        if not state.client_secret:
            log_message("ERROR! - CLIENT_SECRET is missing in the configuration.")
            return

        state.prefix_dropdown.set('')
        state.prefix_dropdown['values'] = ()

        log_message(f"FTS_HOST_NAME {state.fts_host_name}")
        log_message(f"OCI IAM Base URL: {state.oci_iam_base_url}")
        log_message(f"OCI IAM Scope: {state.oci_iam_scope}")
        log_message(f"Client ID: {state.client_id}")
        log_message(f"Client Secret: {state.client_secret}")
    else:
        log_message("Error: Selected customer not found in config.")

def add_customer_keys(root):

    top = tk.Toplevel(root)  #
    top.title("Manage Customer Config")
    top.geometry("550x250")

    top.transient(root)
    top.grab_set()
    top.focus_set()  #
    keys = ["FTS_HOST_NAME", "OCI_IAM_BASE_URL", "OCI_IAM_SCOPE", "CLIENT_ID", "CLIENT_SECRET"]
    labels = ["FTS Host Name", "OCI IAM Base URL", "OCI IAM Scope", "Client ID", "Client Secret"]
    entries = {}

    config_file = state.CONFIG_FILE

    def fetch_config(include_encryption=False):
        cfg = ConfigParser()
        if os.path.exists(config_file):
           cfg.read(config_file)
           if not include_encryption and "encryption" in cfg:
              cfg.remove_section("encryption")
        return cfg

    def save_config(cfg):
        if os.path.exists(config_file):

            existing_cfg = ConfigParser()
            existing_cfg.read(config_file)

            for section in existing_cfg.sections():
                if  cfg.has_section(section):
                    existing_cfg.remove_section(section)

                for section in cfg.sections():
                   if not existing_cfg.has_section(section):
                          existing_cfg.add_section(section)
                   for key, value in cfg.items(section):
                       existing_cfg.set(section, key, value)
        else:
            existing_cfg = cfg

        with open(config_file, 'w') as f:
            existing_cfg.write(f)


    def clear_entries():
        for entry in entries.values():
            entry.delete(0, tk.END)
        env_dropdown.set("")
        refresh_env_list()

    def load_env_data(event=None):
        env = env_var.get()
        cfg = fetch_config()
        if cfg.has_section(env):
            for key in keys:
                val = cfg.get(env, key, fallback="")
                if key == "CLIENT_SECRET":
                    val = decrypt_secret(val)
                entries[key].delete(0, tk.END)
                entries[key].insert(0, val)
        else:
            clear_entries()

    def show_missing_key_popup(parent_window, missing_keys):
        msg = f"The following keys are missing:\n\n{', '.join(missing_keys)}"
        messagebox.showwarning("Missing Keys", msg, parent=parent_window)

    def show_popup_msg(parent_window, type, key, msg):
        if type == "Info":
            messagebox.showinfo(f"{key}", msg, parent=parent_window)
        else:
            messagebox.showwarning(f"{key}", msg, parent=parent_window)

    def save_env():
        missing_keys = []
        env = env_var.get().strip()
        if not env:
            missing_keys.append("CUSTOMER_NAME")

        cfg = fetch_config()
        if not cfg.has_section(env):
            cfg.add_section(env)

        for key in keys:
            value = entries[key].get()
            if not value:
                missing_keys.append(key)
                continue
            if key == "CLIENT_SECRET":
                value = encrypt_secret(value)
            cfg.set(env, key, value)

        if missing_keys:
            show_missing_key_popup(top, missing_keys)
        else:
            save_config(cfg)
            refresh_env_list()
            show_popup_msg(top, "Info", "Saved", f"[{env}] configuration saved.")

    def delete_env():

        if state.selected_customer == env_var.get():
            state.fts_host_name = None
            state.oci_iam_base_url = None
            state.oci_iam_scope = None
            state. client_id = None
            state.client_secret = None

            state.customer_dropdown.set("")
            state.customer_config.clear()

            state.prefix_dropdown.set('')
            state.prefix_dropdown['values'] = ()

        env = env_var.get()
        cfg = fetch_config(True)

        if cfg.has_section(env):
            cfg.remove_section(env)
            #save_config(cfg)
            with open(config_file, 'w') as f:
                cfg.write(f)
            refresh_env_list()
            env_var.set("")
            clear_entries()
            show_popup_msg(top, "Info", "Deleted", f"[{env}] removed.")
        else:
            show_popup_msg(top, "Warning", "Not Found", f"No environment named [{env}]")

    def refresh_env_list():
        cfg = fetch_config()
        env_dropdown['values'] = cfg.sections()
        state.customer_dropdown['values'] = cfg.sections()

    tk.Label(top, text="Environment").grid(row=0, column=0, padx=5, pady=5, sticky='e')
    env_var = tk.StringVar()
    env_dropdown = ttk.Combobox(top, textvariable=env_var, width=50)
    env_dropdown.grid(row=0, column=1, padx=5, pady=5, sticky='w')
    env_dropdown.bind("<<ComboboxSelected>>", load_env_data)

    show_secret_var = tk.BooleanVar(value=False)

    def toggle_client_secret():
        if show_secret_var.get():
            entries["CLIENT_SECRET"].config(show="")
        else:
            entries["CLIENT_SECRET"].config(show="*")

    for i, label in enumerate(labels):
        tk.Label(top, text=label).grid(row=i + 1, column=0, padx=5, pady=5, sticky='e')

        show_char = "*" if keys[i] == "CLIENT_SECRET" else ""
        entry = tk.Entry(top, width=60, show=show_char)
        entry.grid(row=i + 1, column=1, padx=5, pady=5)
        entries[keys[i]] = entry

        if keys[i] == "CLIENT_SECRET":
            show_secret_cb = tk.Checkbutton(
                top, text="Show", variable=show_secret_var, command=toggle_client_secret
            )
            show_secret_cb.grid(row=i + 1, column=2, padx=5, pady=5, sticky='w')

    button_frame = tk.Frame(top)
    button_frame.grid(row=7, column=0, columnspan=2, pady=15)

    save_btn = tk.Button(button_frame, text="💾 Save", command=save_env, bg="lightgreen", width=12)
    delete_btn = tk.Button(button_frame, text="🗑️ Delete", command=delete_env, bg="tomato", width=12)
    clear_btn = tk.Button(button_frame, text="🧹 Clear", command=clear_entries, bg="lightgray", width=12)

    save_btn.pack(side="left", padx=10)
    delete_btn.pack(side="left", padx=10)
    clear_btn.pack(side="left", padx=10)

    refresh_env_list()
import os
import state
import threading
import requests
import json
import tkinter as tk
import concurrent.futures
from tkinter import filedialog, messagebox,ttk
from ui_utils import apply_filter
from api import get_access_token
from log_utils import log_message

def list_prefixes():

    if not state.customer_config:
        log_message("ERROR! - No customer selected. Please select a customer first.")
        return

    log_message(f"Using fts_host_name in list_prefixes: {state.fts_host_name}")

    access_token = get_access_token()
    if not access_token:
        return

    log_message("Fetching prefixes...")
    url = f"{state.fts_host_name}/listprefixes"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json",
        "Accept-Language": "en-US",
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        response_data = response.json()

        if isinstance(response_data, list):

            sorted_data = sorted(response_data, key=str.lower)
            state.prefix_dropdown["values"] = sorted_data
            state.prefix_dropdown.current(0)
            log_message(f"Prefixes loaded (sorted): {sorted_data}")

        else:

            log_message("ERROR! - Unexpected API response format.")
            messagebox.showerror("ERROR", "Unexpected API response format.")

    except requests.exceptions.RequestException as e:
        log_message(f"ERROR! - Failed to fetch prefixes - {e}")
        messagebox.showerror("ERROR!", f"Failed to fetch prefixes: {e}")


def list_files():
    selected_prefix = state.prefix_dropdown.get()

    if not state.customer_config:
        log_message("ERROR! - No customer selected. Please select a customer first.")
        return

    log_message(f"Using fts_host_name in list_files: {state.fts_host_name}")

    access_token = get_access_token()
    if not access_token:
        return

    log_message(f"Fetching files for prefix: {selected_prefix}...")
    url = f"{state.fts_host_name}/listfiles?prefix={selected_prefix}"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json",
        "Accept-Language": "en-US",
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        response_data = response.json()

        state.file_tree.delete(*state.file_tree.get_children())

        if "resultSet" in response_data and isinstance(response_data["resultSet"], list):

            state.file_data = response_data["resultSet"]
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
            log_message(f"Files loaded: {len(state.file_data)} items found.")
            apply_filter()
        else:
            log_message("ERROR! - Unexpected API response format.")
            messagebox.showerror("ERROR!", "Unexpected API response format.")
    except requests.exceptions.RequestException as e:
        log_message(f"ERROR! - Failed to fetch files - {e}")
        messagebox.showerror("ERROR!", f"Failed to fetch files: {e}")


def upload_files():
    selected_files = filedialog.askopenfilenames()
    if not selected_files:
        messagebox.showerror("ERROR!", "No files selected for upload.")
        return

    storage_prefix = state.prefix_dropdown.get()  # Get selected prefix from dropdown
    if not storage_prefix:
        messagebox.showerror("ERROR!", "No storage prefix selected.")
        return

    access_token = get_access_token()
    if not access_token:
        return

    api_url = f"{state.fts_host_name}/upload"

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json",
        "Accept-Language": "en-US",
        "Content-Type": "application/json",
    }

    payload = {
        "listOfFiles": [
            {
                "storagePrefix": storage_prefix,
                "fileName": os.path.basename(file_path)
            }
            for file_path in selected_files
        ]
    }

    log_message(f"Target prefix: {storage_prefix}")
    log_message(f"API Used: {api_url}")
    log_message(f"Upload Request: {payload}")

    def upload_worker():

        try:
            response = requests.post(api_url, headers=headers, json=payload)
            response.raise_for_status()
            response_data = response.json()

            if len(response_data.get("parList", [])) != len(selected_files):
                log_message("Number of files in the response does not match the number of selected files.")
                return

            def upload_file(file_path, access_uri):
                """Function to upload a single file"""
                file_name = os.path.basename(file_path)
                try:
                    if os.path.getsize(
                            file_path) == 0:
                        put_response = requests.put(access_uri, data=b'', headers={"Content-Length": "0"})
                    else:
                        with open(file_path, "rb") as file:
                            put_response = requests.put(access_uri, data=file)

                    if put_response.status_code == 200:
                        log_message(f"✅ File {file_name} uploaded successfully.")
                    else:
                        log_message(f"Failed to upload {file_name}. Error: {put_response.text}")
                except Exception as e:
                    log_message(f"ERROR! - uploading file {file_name}: {str(e)}")

            with concurrent.futures.ThreadPoolExecutor(max_workers=state.MAX_THREADS) as executor:
                futures = []
                for file_path in selected_files:
                    file_name = os.path.basename(file_path)
                    matching_entry = next(
                        (file_data for file_data in response_data["parList"] if file_data["name"] == file_name), None)

                    if not matching_entry:
                        log_message(f"No matching entry found for {file_name} in the response.")
                        continue

                    access_uri = matching_entry.get("accessUri")
                    if not access_uri:
                        log_message(f"ERROR! - Failed to get accessUri for {file_name}")
                        continue

                    future = executor.submit(upload_file, file_path, access_uri)
                    futures.append(future)

                concurrent.futures.wait(futures)

            messagebox.showinfo("Success", "All files uploaded successfully.")

        except requests.exceptions.RequestException as e:
            log_message(f"ERROR! - uploading files: {e}")
            messagebox.showerror("Upload Error", f"Error uploading files: {e}")

    threading.Thread(target=upload_worker, daemon=True).start()


def download_files():
    selected_items = state.file_tree.selection()
    if not selected_items:
        messagebox.showerror("ERROR!", "Please select at least one file to download.")
        return

    selected_files = []
    for item in selected_items:
        file_details = state.file_tree.item(item, "values")
        if file_details:
            selected_files.append(file_details[0])

    prefix_name = state.prefix_dropdown.get()
    if not prefix_name:
        messagebox.showerror("ERROR!", "No prefix selected.")
        return

    save_directory = filedialog.askdirectory()
    if not save_directory:
        return

    access_token = get_access_token()
    if not access_token:
        return

    url = f"{state.fts_host_name}/download"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json",
        "Accept-Language": "en-US",
        "Content-Type": "application/json",
    }

    payload = {
        "listOfFiles": [{"storagePrefix": prefix_name, "fileName": os.path.basename(file_name)} for file_name in
                        selected_files]
    }

    log_message(f"Selected Prefix: {prefix_name}")
    log_message(f"API Endpoint: {url}")

    def download_worker(file_info):

        file_name = file_info.get("name")
        access_uri = file_info.get("accessUri")

        if not access_uri:
            log_message(f"No access URI for {file_name}, skipping download.")
            return

        try:
            file_response = requests.get(access_uri, stream=True)
            file_response.raise_for_status()

            file_path = os.path.join(save_directory, file_name)
            with open(file_path, "wb") as file:
                for chunk in file_response.iter_content(chunk_size=8192):
                    file.write(chunk)

            log_message(f"✅ {file_name} downloaded successfully.")
        except requests.exceptions.RequestException as e:
            log_message(f"ERROR! - Failed to download {file_name}: {e}")

    def process_download():

        try:
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
            response_data = response.json()

            if "parList" in response_data and response_data["parList"]:

                with concurrent.futures.ThreadPoolExecutor(max_workers=state.MAX_THREADS) as executor:
                    executor.map(download_worker, response_data["parList"])

                messagebox.showinfo("Success", f"Files downloaded successfully to:\n{save_directory}")
                log_message(f"All files downloaded successfully to: {save_directory}")
            else:
                log_message(f"Unexpected API response format: {response_data}")
                messagebox.showerror("ERROR!", f"Unexpected API response format\n{response_data}")

        except requests.exceptions.RequestException as e:
            log_message(f"ERROR! - {e}")
            messagebox.showerror("ERROR!", f"Failed to download files: {e}")

    threading.Thread(target=process_download, daemon=True).start()

def delete_selected_files():
    parent = state.file_tree.winfo_toplevel()
    def custom_confirm_deletion(title, file_list, prefix_name):
        result = {"value": False}

        def on_yes():
            result["value"] = True
            win.destroy()

        def on_no():
            win.destroy()

        win = tk.Toplevel(parent)
        win.title(title)
        win.geometry("500x300")
        win.transient(parent)
        win.grab_set()

        tk.Label(win, text=f"Are you sure you want to delete the following files from '{prefix_name}'?").pack(pady=5, padx=5)

        text_frame = tk.Frame(win)
        text_frame.pack(fill="both", expand=True, padx=10, pady=5)

        scrollbar = tk.Scrollbar(text_frame)
        scrollbar.pack(side="right", fill="y")

        text = tk.Text(text_frame, wrap="none", height=10, yscrollcommand=scrollbar.set)
        text.pack(fill="both", expand=True)
        scrollbar.config(command=text.yview)

        text.insert("1.0", "\n".join(file_list))
        text.config(state="disabled")

        button_frame = tk.Frame(win)
        button_frame.pack(pady=10)

        tk.Button(button_frame, text="Yes", width=10, command=on_yes).pack(side="left", padx=10)
        tk.Button(button_frame, text="No", width=10, command=on_no).pack(side="right", padx=10)

        win.wait_window()
        return result["value"]

    selected_items = state.file_tree.selection()
    if not selected_items:
        messagebox.showwarning("Warning", "Please select one or more files to delete!")
        return

    prefix_name = state.prefix_dropdown.get()
    if not prefix_name:
        messagebox.showerror("ERROR!", "No prefix selected.")
        return

    files_to_delete = []
    for item in selected_items:
        values = state.file_tree.item(item)['values']
        if values:
            file_name =  values[0].split("/")[-1]
            files_to_delete.append({
                "tree_item": item,
                "storagePrefix": prefix_name,
                "fileName": file_name
            })

    file_names = [f["fileName"] for f in files_to_delete]

    confirm = custom_confirm_deletion("Confirm Deletion", file_names, prefix_name)

    if not confirm:
        return

    access_token = get_access_token()
    if not access_token:
        log_message("ERROR! - Failed to retrieve access token.")
        return

    api_url = f"{state.fts_host_name}/delete"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "Accept-Language": "en-US"
    }

    def delete_tree_item_by_filename(filename: str):

        for item in state.file_tree.get_children():
            values = state.file_tree.item(item, "values")
            if values and filename in values[0]:
                state.file_tree.delete(item)
                return
        log_message(f"⚠️ Could not find item to delete in grid: {filename}")

    def delete_worker(file_info):

        file_name = file_info["fileName"]
        storagePrefix = file_info["storagePrefix"]

        payload = {
            "listOfFiles": [
                {
                    "storagePrefix": storagePrefix,
                    "fileName": file_name
                }
            ]
        }

        try:
            response = requests.delete(api_url, headers=headers, data=json.dumps(payload))
            if response.status_code == 200:
                log_message(f"✅ File '{file_name}' deleted successfully from '{storagePrefix}'")
                parent.after(0, lambda: delete_tree_item_by_filename(file_name))
            else:
                log_message(f"❌ Failed to delete '{file_name}': {response.text}")
        except requests.exceptions.RequestException as e:
            log_message(f"❌ Request error deleting '{file_name}': {e}")

    def run_deletion():
        with concurrent.futures.ThreadPoolExecutor(max_workers=state.MAX_THREADS) as executor:
            executor.map(delete_worker, files_to_delete)

        messagebox.showinfo("Deletion Completed", "Selected files processed for deletion.")

    threading.Thread(target=run_deletion, daemon=True).start()


def move_file():
    current_prefix = state.prefix_dropdown.get()
    if not current_prefix:
        messagebox.showerror("Error", "No storage prefix selected.")
        return

    selected_file = get_selected_file()

    if not selected_file:
        return

    def open_move_popup():

        move_popup = tk.Toplevel()
        move_popup.title("Move File")

        tk.Label(move_popup, text=f"Move File: {selected_file}").grid(row=0, column=0, padx=10, pady=5)
        tk.Label(move_popup, text="Select Target Prefix:").grid(row=1, column=0, padx=10, pady=5)

        new_prefix_dropdown = ttk.Combobox(move_popup, values=get_available_prefixes(), state="readonly", width=30)
        new_prefix_dropdown.grid(row=1, column=1, padx=10, pady=5)

        tk.Label(move_popup, text="Enter New File Name:").grid(row=2, column=0, padx=10, pady=5)

        new_filename_entry = tk.Entry(move_popup, width=32)
        new_filename_entry.insert(0, selected_file)
        new_filename_entry.grid(row=2, column=1, padx=50, pady=5)

        def move_action():

            new_prefix = new_prefix_dropdown.get()
            new_filename = new_filename_entry.get()

            if new_prefix == current_prefix:
                messagebox.showerror("Error",
                                     "Target prefix cannot be the current one, please select a different prefix")
                return

            if not new_prefix or not new_filename:
                messagebox.showerror("Error",
                                     "Please select a new prefix and enter a new file name [new file_name is optional].")
                return

            payload = {
                "listOfFiles": [
                    {
                        "currentPath": {
                            "storagePrefix": current_prefix,
                            "fileName": selected_file
                        },
                        "newPath": {
                            "storagePrefix": new_prefix,
                            "fileName": new_filename
                        }
                    }
                ]
            }

            try:

                api_url = f"{state.fts_host_name}/movefiles"
                headers = {
                    "Authorization": f"Bearer {get_access_token()}",
                    "Content-Type": "application/json",
                    "Accept-Language": "en-US"
                }

                log_message(f"API used for file move : {api_url}")
                response = requests.post(api_url, json=payload, headers=headers)
                response.raise_for_status()

                log_message(f"Success {selected_file} successfully moved to {new_prefix}/{new_filename}")
                messagebox.showinfo("Success",
                                    f"File {selected_file} successfully moved to {new_prefix}/{new_filename}")
                move_popup.destroy()

            except requests.exceptions.RequestException as e:
                log_message(f"Failed to move file {selected_file} {str(e)}")
                messagebox.showerror("ERROR!", f"Failed to move file: {e}")
                move_popup.destroy()

        move_button = tk.Button(move_popup, text="Move File", command=move_action)
        move_button.grid(row=3, column=0, columnspan=2, padx=10, pady=10)

    open_move_popup()


def get_available_prefixes():
    return state.prefix_dropdown["values"]


def get_selected_file():
    selected_items = state.file_tree.selection()
    if not selected_items:
        messagebox.showerror("ERROR!", "Please select the file to move.")
        return
    for item in selected_items:
        file_details = state.file_tree.item(item, "values")
        file_name = file_details[0]

    return os.path.basename(file_name)
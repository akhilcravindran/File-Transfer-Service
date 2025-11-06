
import os
import sys
import base64
import configparser
import tkinter as tk
from tkinter import messagebox
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
import state
import string,random

config = configparser.ConfigParser()

def generate_random_string(length=10):
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(length))

def get_encryption_password(root):
    result = None

    def on_submit():
        nonlocal result
        result = entry.get()
        dialog.destroy()

    dialog = tk.Toplevel(root)
    dialog.title("Encryption Login")
    dialog.geometry("350x120")
    dialog.resizable(False, False)
    dialog.grab_set()

    tk.Label(dialog, text="Enter encryption password:").pack(pady=(15, 5))
    entry = tk.Entry(dialog, show="*", width=35)
    entry.pack(pady=5)
    entry.focus()

    tk.Button(dialog, text="Submit", command=on_submit).pack(pady=(5, 10))
    dialog.wait_window()
    return result

def initialize_encryption(root):

    if not os.path.exists(state.CONFIG_FILE):
        with open(state.CONFIG_FILE, "w") as f:
            pass

    config.read(state.CONFIG_FILE)
    root.withdraw()

    if "encryption" not in config or "salt" not in config["encryption"]:
        config.add_section("encryption")
        salt_bytes = os.urandom(16)
        encoded_salt = base64.b64encode(salt_bytes).decode("utf-8")
        config.set("encryption", "salt", encoded_salt)

    salt = base64.b64decode(config["encryption"]["salt"])

    password_input = get_encryption_password(root)
    if not password_input:
        messagebox.showerror("Login Failed", "Password is required to continue.")
        sys.exit(1)

    password = password_input.encode()

    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
        backend=default_backend()
    )
    key = base64.urlsafe_b64encode(kdf.derive(password))
    state.fernet = Fernet(key)

    if "key_check" not in config["encryption"]:
        enc_key_test_str=encrypt_secret(generate_random_string())
        config.set("encryption", "key_check", enc_key_test_str)

    with open(state.CONFIG_FILE, "w") as configfile:
        config.write(configfile)

    if "key_check" in config["encryption"]:
        if decrypt_secret(config["encryption"]["key_check"]) == "[Decryption Failed]":
            messagebox.showerror("Wrong Encryption Key", "Please enter the correct encryption key to continue")
            sys.exit(1)

def encrypt_secret(secret):

    try:
        return state.fernet.encrypt(secret.encode()).decode()
    except Exception:
        return "[Encryption Failed]"

def decrypt_secret(encrypted_secret):
    global fernet
    try:
        return state.fernet.decrypt(encrypted_secret.encode()).decode()
    except Exception:
        return "[Decryption Failed]"

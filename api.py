
import requests
import state
from datetime import datetime, timedelta
from log_utils import log_message


def get_access_token():
    if not all([state.oci_iam_base_url, state.oci_iam_scope, state.client_id, state.client_secret]):
        log_message("ERROR! - Missing credentials in config file.")
        return None

    customer_key = state.customer_config.get("CUSTOMER_NAME", state.customer_dropdown.get())

    if (
        customer_key in state.token_cache and
        "access_token" in state.token_cache[customer_key] and
        "expires_at" in state.token_cache[customer_key] and
        datetime.now() < state.token_cache[customer_key]["expires_at"]
    ):
        log_message(f"Using cached access token for {customer_key}.")
        return state.token_cache[customer_key]["access_token"]

    log_message(f"Fetching new access token for {customer_key}...")

    url = f"{state.oci_iam_base_url}/oauth2/v1/token"
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    data = {
        "grant_type": "client_credentials",
        "scope": state.oci_iam_scope,
        "client_id": state.client_id,
        "client_secret": state.client_secret,
    }

    try:
        response = requests.post(url, headers=headers, data=data)
        response.raise_for_status()
        token_data = response.json()

        state.token_cache[customer_key] = {
            "access_token": token_data.get("access_token"),
            "expires_at": datetime.now() + timedelta(seconds=token_data.get("expires_in", 3600))
        }

        log_message(f"New access token retrieved for {customer_key}.")
        return state.token_cache[customer_key]["access_token"]
    except requests.exceptions.RequestException as e:
        log_message(f"ERROR! - Failed to get access token for {customer_key} - {e}")
        return None

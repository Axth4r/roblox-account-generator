from time import sleep

# Our self-hosted FUNCAPTCHAV3 solver on Railway
API_BASE = "https://web-production-a4d98.up.railway.app"
max_attempts = 60  # seconds

# Roblox signup sitekey (from FUNCAPTCHAV3's constants)
ROBLOX_SITEKEY = "A2A14B1D-1AF3-C791-9BBC-EE33CC7A0A6F"

def rs_get_token(session, blob, proxy, api_key, timeout=30):
    """
    Drop-in replacement for the rosolve.pro solver.
    Hits our self-hosted FUNCAPTCHAV3 API instead.
    Signature kept identical so no other file needs editing.
    """
    # normalize proxy format — FUNCAPTCHAV3 wants full URL
    if proxy:
        proxy_url = proxy if proxy.startswith("http") else f"http://{proxy}"
    else:
        proxy_url = None

    # ---- Step 1: create the solve task ----
    create_payload = {
        "sitekey": ROBLOX_SITEKEY,
        "blob": blob,
        "has_suppressed": False,
        "has_pow": True,
        "proxy": proxy_url,
    }

    try:
        response = session.post(f"{API_BASE}/solve/create", json=create_payload, timeout=timeout)
    except Exception as e:
        return None, f"Network error during task creation: {e}"

    if response.status_code != 200:
        try:
            err = response.json()
            msg = err.get("error", "Unknown error")
        except Exception:
            msg = response.text[:100]
        return None, f"HTTP {response.status_code}: {msg}"

    try:
        data = response.json()
    except Exception as ve:
        return None, f"Invalid JSON from solver (createTask): {ve}"

    task_id = data.get("task_id")
    if not task_id:
        err = data.get("error", "Unknown error")
        return None, f"Failed to get task_id, reason: {err}"

    # ---- Step 2: poll for result ----
    for _ in range(max_attempts):
        try:
            status_resp = session.get(f"{API_BASE}/solve/status/{task_id}", timeout=timeout)
        except Exception as e:
            return None, f"Network error during status check: {e}"

        if status_resp.status_code != 200:
            try:
                err = status_resp.json()
                msg = err.get("error", "Unknown error")
            except Exception:
                msg = status_resp.text[:100]
            return None, f"Status check failed: HTTP {status_resp.status_code}: {msg}"

        try:
            status_data = status_resp.json()
        except Exception as ve:
            return None, f"Invalid JSON from solver (taskResult): {ve}"

        status = status_data.get("status")

        if status == "completed":
            token = status_data.get("token")
            if token:
                return token, None
            return None, f"Completed but no token in response: {status_data}"

        if status == "error":
            err_msg = status_data.get("error", "Unknown error")
            return None, err_msg

        sleep(1)

    return None, f"Captcha solving did not complete in time. Timed out after {max_attempts} seconds."

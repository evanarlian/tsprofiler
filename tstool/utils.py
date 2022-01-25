import requests
import re

import subprocess



def registered_mars(management_url: str) -> dict:
    """
    View all registered mar files

    Parameters:
        management_url (str): TorchServe management url
    Return:
        registered_mars (dict)
    """
    management_url = management_url.rstrip("/")
    registered_mars_url = f"{management_url}/models"
    res = requests.get(registered_mars_url)
    return res.json()


def registered_mar_details(management_url: str, mar_name: str) -> list:
    """
    View one registered mar file details.
    The details contains 

    Parameters:
        management_url (str): TorchServe management url
        mar_name (str): target mar name (do not include `.mar` in the end)
    Return:
        ver TODO
    """
    management_url = management_url.rstrip("/")
    mar_detail_url = f"{management_url}/models/{mar_name}"
    res = requests.get(mar_detail_url)
    return res.json()

# TODO this is bad fix with xmltodict
def gpu_processes() -> list:

    # regular `nvidia-smi` command
    nvidia_smi_output = subprocess.check_output(["nvidia-smi"]).decode()
    lines = nvidia_smi_output.splitlines()

    # find line before processes
    for i, line in enumerate(lines):
        if re.match(r"^\|=+\|$", line):
            start_line = i

    # programmatically generate processes
    raw_processes = lines[start_line+1 : -1]
    processes = []
    for raw_process in raw_processes:
        try:
            gpu_id, gi_id, ci_id, pid, type, name, usage_mib = raw_process.split()[1:-1]
        except ValueError:
            # happened when the GPU has no running processes
            return []
        processes.append({
            "gpu_id": int(gpu_id),
            "gi_id": gi_id,
            "ci_id": ci_id,
            "pid": int(pid),
            "type": type,
            "name": name,
            "usage_mib": int(usage_mib[:-3]),  # remove `MiB`
        })

    return processes


def gpu_process_by_pid(pid: int) -> dict:
    processes = gpu_processes()
    for process in processes:
        if process["pid"] == pid:
            return process
    raise ValueError(f"No GPU process with pid = {pid}. See `nvidia-smi`")

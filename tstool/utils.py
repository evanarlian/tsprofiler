import subprocess

import requests
import xmltodict



def registered_mars(management_url: str) -> dict:
    """
    View all registered mar files.

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
    The details contains TODO

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


def gpu_processes() -> list:
    """
    Get current running processes from all GPUs.

    Return:
        result_processes (list)
    """
    # extended `nvidia-smi -q --xml-format` command
    nvidia_smi_output = subprocess.check_output(["nvidia-smi", "-q", "--xml-format"]).decode()
    parsed = xmltodict.parse(nvidia_smi_output)

    # find gpus
    gpus = parsed["nvidia_smi_log"]["gpu"]
    if not isinstance(gpus, list):
        gpus = [gpus]

    # parse info
    result_processes = []
    for gpu in gpus:
        curr_gpu_id = int(gpu["minor_number"])
        processes = gpu["processes"]["process_info"]
        if not isinstance(processes, list):
            processes = [processes]
        for process in processes:
            result_processes.append({
                "gpu_id": curr_gpu_id,
                "pid": int(process["pid"]),
                "process_name": process["process_name"],
                "usage_mib": int(process["used_memory"][:-4])  # remove ` MiB`
            })

    return result_processes


def gpu_process_by_pid(pid: int) -> dict:
    """
    Get GPU process info by pid.

    Return:
        process (dist): Selected process info
    """
    processes = gpu_processes()
    for process in processes:
        if process["pid"] == pid:
            return process
    raise ValueError(f"No GPU process with pid = {pid}. See `nvidia-smi`")

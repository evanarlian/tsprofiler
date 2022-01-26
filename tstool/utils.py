import subprocess
from io import StringIO

import pandas as pd
import requests
# import xmltodict



def get_registered_mars(management_url: str) -> dict:
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


def get_registered_mar_details(management_url: str, mar_name: str) -> list:
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


# def gpu_processes() -> list:
#     """
#     Get current running processes from all GPUs.

#     Return:
#         result_processes (list)
#     """
#     # extended `nvidia-smi -q --xml-format` command
#     nvidia_smi_output = subprocess.check_output(["nvidia-smi", "-q", "--xml-format"]).decode()
#     parsed = xmltodict.parse(nvidia_smi_output)

#     # find gpus
#     gpus = parsed["nvidia_smi_log"]["gpu"]
#     if not isinstance(gpus, list):
#         gpus = [gpus]

#     # parse info
#     result_processes = []
#     for gpu in gpus:
#         curr_gpu_id = int(gpu["minor_number"])
#         processes = gpu["processes"]["process_info"]
#         if not isinstance(processes, list):
#             processes = [processes]
#         for process in processes:
#             result_processes.append({
#                 "gpu_id": curr_gpu_id,
#                 "pid": int(process["pid"]),
#                 "process_name": process["process_name"],
#                 "usage_mib": int(process["used_memory"][:-4])  # remove ` MiB`
#             })

#     return result_processes


def get_gpu_processes(filter_pid=None, filter_name=None):
    """
    Get current running processes from all GPUs.

    Parameters:
        filter_pid (str): What to filter based on pid
        filter_name (str): What to filter based on name (substring)
    Return:
        result_processes (list): can be empty list
    """
    nvidia_smi_output = subprocess.check_output(["nvidia-smi",  "--query-compute-apps=timestamp,gpu_name,gpu_bus_id,gpu_serial,gpu_uuid,pid,process_name,used_gpu_memory",  "--format=csv"]).decode()
    stringio = StringIO(nvidia_smi_output)
    df = pd.read_csv(stringio, sep=", ", engine="python")
    df["used_gpu_memory [MiB]"] = df["used_gpu_memory [MiB]"].str[:-4]
    df["used_gpu_memory [MiB]"] = pd.to_numeric(df["used_gpu_memory [MiB]"], errors="coerce")
    if filter_pid is not None:
        df = df[df["pid"] == filter_pid]
    if filter_name is not None:
        df = df[df["process_name"].str.contains(filter_name)]
    return df.to_dict(orient="records")

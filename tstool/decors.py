from asyncio import transports
import time
import multiprocessing as mp

from .monitor import MultiMonitor
from .utils import get_gpu_processes



def _transpose_ld_to_dl(list_of_dict: list) -> dict:
    keys = list_of_dict[0].keys()
    dict_of_list = {k: [d[k] for d in list_of_dict] for k in keys}
    return dict_of_list


def _avg(ls: list) -> float:
    return sum(ls) / len(ls)


def resource_monitor(pid, timer=True, ram=True, cpu=True, gpu=True, return_all_data=False):
    
    # assert
    assert isinstance(pid, int), "pid must be integer"
    
    # building queries
    queries = []
    if ram:
        # TODO memory percent is not used because you cannot get uss memory from list-of-string API
        queries += ["memory_full_info"]
    if cpu:
        queries += ["cpu_percent"]

    def decorator(func):
        
        def wrapper(*args, **kwargs):
            
            # only create monitor if ram or cpu or both are requested
            if ram or cpu:
                # run monitor in another process 
                start_event = mp.Event()
                list_proxy = mp.Manager().list()
                multi_monitor = MultiMonitor(pid, start_event, list_proxy, queries)
                # wait for ram monitor to start
                multi_monitor.start()
                start_event.wait()
            
            # run original func and make sure to terminate ram monitor if exception happened
            start_time = time.perf_counter()
            try:
                original_result = func(*args, **kwargs)
            except Exception as e:
                if ram or cpu:
                    multi_monitor.terminate()
                raise e
            end_time = time.perf_counter()
            
            # stop monitor
            if ram or cpu:
                multi_monitor.terminate()
                list_monitor = list(list_proxy)

            # only keep uss from full memory info
            if ram:
                temp = []
                for m in list_monitor:
                    mem_full_info = m.pop("memory_full_info")
                    m["ram_uss_bytes_all"] = mem_full_info.uss
                    temp.append(m)
                list_monitor = temp
            
            # transpose-ish list-of-dict to dict-of-list and insert ram and cpu monitor data
            dict_monitor = {}
            if ram or cpu:
                transposed = _transpose_ld_to_dl(list_monitor)
                dict_monitor.update(transposed)

            # insert gpu monitor data
            if gpu:
                gpu_processes = get_gpu_processes(filter_pid=pid)
                if len(gpu_processes) == 0:
                    raise ValueError(f"pid = {pid} does not match any running GPU processes. See `nvidia-smi`")
                elif len(gpu_processes) >= 2:
                    raise ValueError(f"pid = {pid} returns ambiguous (more than one) processes. See `nvidia-smi`")
                else:
                    dict_monitor["gpu_mem_mib"] = gpu_processes[0]["used_gpu_memory [MiB]"]
            
            # insert timer monitor data
            if timer:
                dict_monitor["time_ms"] = (end_time - start_time) * 1000

            # rename and aggregate cpu monitor data
            if cpu:
                dict_monitor["cpu_percent_all"] = dict_monitor.pop("cpu_percent")
                dict_monitor["cpu_percent_min"] = min(dict_monitor["cpu_percent_all"])
                dict_monitor["cpu_percent_max"] = max(dict_monitor["cpu_percent_all"])
                dict_monitor["cpu_percent_avg"] = _avg(dict_monitor["cpu_percent_all"])
            
            # aggregate ram monitor data
            if ram:
                dict_monitor["ram_uss_bytes_min"] = min(dict_monitor["ram_uss_bytes_all"])
                dict_monitor["ram_uss_bytes_max"] = max(dict_monitor["ram_uss_bytes_all"])
                dict_monitor["ram_uss_bytes_avg"] = _avg(dict_monitor["ram_uss_bytes_all"])

            # remove all data if user does not want
            if not return_all_data:
                dict_monitor.pop("ram_uss_bytes_all")
                dict_monitor.pop("cpu_percent_all")

            return original_result, dict_monitor

        return wrapper
    return decorator

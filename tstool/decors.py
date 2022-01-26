import time
import multiprocessing as mp

from .monitor import RAMMonitor
from .utils import get_gpu_processes


def resource_monitor(pid, timer=True, ram=True, gpu=True):
    assert isinstance(pid, int), "pid must be integer"
    def decorator(func):
        def wrapper(*args, **kwargs):
            
            if ram:
                # run monitor in another process 
                start_event = mp.Event()
                uss_list_proxy = mp.Manager().list()
                ram_monitor = RAMMonitor(pid, start_event, uss_list_proxy)
                # wait for ram monitor to start
                ram_monitor.start()
                start_event.wait()
            
            # run original func and make sure to terminate ram monitor if exception happened
            start_time = time.perf_counter()
            try:
                original_result = func(*args, **kwargs)
            except Exception as e:
                if ram:
                    ram_monitor.terminate()
                raise e
            end_time = time.perf_counter()
            
            if ram:
                ram_monitor.terminate()
                uss_list = list(uss_list_proxy)
            
            if gpu:
                gpu_processes = get_gpu_processes(filter_pid=pid)
                if len(gpu_processes) == 0:
                    raise ValueError(f"pid = {pid} does not match any running GPU processes. See `nvidia-smi`")
                elif len(gpu_processes) >= 2:
                    raise ValueError(f"pid = {pid} returns ambiguous (more than one) processes. See `nvidia-smi`")
                else:
                    gpu_mem_mib = gpu_processes[0]["used_gpu_memory [MiB]"]
            
            # fill monitor result
            monitor_result = {}
            if timer:
                monitor_result["time_ms"] = (end_time - start_time) * 1000
            if ram:
                # return -1 if the func runs too fast
                monitor_result["ram_uss_byte"] = -1 if uss_list == [] else max(uss_list)
            if gpu:
                monitor_result["gpu_mem_mib"] = gpu_mem_mib
            return original_result, monitor_result
        return wrapper
    return decorator

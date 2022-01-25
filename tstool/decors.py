import time
import multiprocessing as mp

from .monitor import RAMMonitor
from .utils import gpu_process_by_pid


def resource_monitor(pid, timer=True, ram=True, gpu=True):
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
            start_time = time.perf_counter()
            result = func(*args, **kwargs)
            end_time = time.perf_counter()
            if ram:
                ram_monitor.terminate()
                uss_list = list(uss_list_proxy)
            if gpu:
                gpu_mib = gpu_process_by_pid(pid)["usage_mib"]
            # fill result
            monitor_result = {}
            if timer:
                monitor_result["time_ms"] = (end_time - start_time) * 1000
            if ram:
                # return -1 if the func runs too fast
                monitor_result["ram_uss_byte"] = -1 if uss_list == [] else max(uss_list)
            if gpu:
                monitor_result["gpu_mib"] = gpu_mib
            return result, monitor_result
        return wrapper
    return decorator

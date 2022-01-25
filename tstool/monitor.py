from multiprocessing import Process
import psutil


class RAMMonitor(Process):

    def __init__(self, target_pid: int, start_event, uss_list_proxy) -> None:
        """
        Creates a new RAM monitor process

        Parameters:
            target_pid (int): target pid to monitor
            start_event (Event): Event object to signal process start between processes
            uss_list_proxy (ListProxy): List proxy object to share results between processes
        """
        super().__init__(daemon=True)  # should kill itself when parent dies
        self.target_pid = target_pid
        self.start_event = start_event
        self.uss_list_proxy = uss_list_proxy

    def run(self):
        """Infinite loop append uss memory usage"""
        self.start_event.set()
        monitored_process = psutil.Process(self.target_pid)
        while True:
            self.uss_list_proxy.append(monitored_process.memory_full_info().uss)

from multiprocessing import Process
import psutil



class MultiMonitor(Process):

    def __init__(self, target_pid: int, start_event, list_proxy, queries=None) -> None:
        """
        Creates a new process monitor

        Parameters:
            target_pid (int): target pid to monitor
            start_event (Event): Event object to signal process start between processes
            list_proxy (ListProxy): List proxy object to share results between processes
            queries (list): list of query to be passed to psutil Process as_dict. Default None will output everything (slow)
        """
        super().__init__(daemon=True)  # should kill itself when parent dies
        self.target_pid = target_pid
        self.start_event = start_event
        self.list_proxy = list_proxy
        self.queries = queries

    def run(self):
        """Infinite loop append uss memory usage"""
        p = psutil.Process(self.target_pid)

        # add just once to make sure at least 1 item appended
        result_dict = p.as_dict(self.queries)
        self.list_proxy.append(result_dict)
        self.start_event.set()

        # do the same but indefinitely
        while True:
            result_dict = p.as_dict(self.queries)
            self.list_proxy.append(result_dict)

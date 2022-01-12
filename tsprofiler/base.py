import traceback
import time
from pathlib import Path
from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor

import requests
from tqdm.auto import tqdm



class TSProfiler(ABC):
    """
    Base TorchServe benchmarker.
    Subclass this class and implement the abstract method.
    `prepare_single_hit()` should prepare dict suitable for requests.post' `files` param.
    `handle_results()` should evaluate when to stop the benchmark iteration.

    Methods to override:
    * prepare_single_hit
    * handle_results
    """
    def __init__(
        self,
        inference_url: str,
        management_url: str,
        mar_name: str,
        hit_size: int,
        max_hit_delay: int,
        starting_batch_size: int,
        batch_size_increments: int,
        initial_workers: int = 1,
        report_folder: str = ".",
        report_filename: str = None,
    ) -> None:
        
        self.inference_url = inference_url.rstrip("/")
        self.management_url = management_url.rstrip("/")
        self.mar_name = mar_name
        self.hit_size = hit_size
        self.max_hit_delay = max_hit_delay
        self.starting_batch_size = starting_batch_size
        self.batch_size_increments = batch_size_increments
        self.initial_workers = initial_workers

        if report_filename is None:
            self.report_filename = f"{self.mar_name}_report_{time.asctime().replace(' ', '-').replace(':', '-')}.csv"
        
        self.report_folder = Path(report_folder).expanduser()
        self.report_filename = Path(self.report_filename)

        self.report_folder.mkdir(parents=True, exist_ok=True)


    def register_model(self) -> bool:
        
        if not self.is_torchserve_running():
            print("TorchServe is not running. Check inputted inference and management url.")
            return False

        params = {
            "url": f"{self.mar_name}.mar",
            "batch_size": self.hit_size,
            "max_batch_delay": self.max_hit_delay,
            "initial_workers": self.initial_workers,
        }

        print(f"Registering {self.mar_name}...")
        register_url = f"{self.management_url}/models"
        register_response = requests.post(register_url, params=params)
        time.sleep(5)

        if register_response.status_code == 200:
            print(f"{self.mar_name} registered successfully.")
        elif register_response.status_code == 409:
            print(f"{self.mar_name} was already registered.")
        else:
            print(f"Unknown error when registering {self.mar_name}")
            print(register_response.text)
            return False
        
        return True


    def unregister_model(self) -> bool:

        if not self.is_torchserve_running():
            print("TorchServe is not running. Check inputted inference and management url.")
            return False

        print(f"Unregistering {self.mar_name}...")
        unregister_url = f"{self.management_url}/models/{self.mar_name}"
        unregister_response = requests.delete(unregister_url)
        time.sleep(5)

        if unregister_response.status_code == 200:
            print(f"{self.mar_name} unregistered successfully.")
        elif unregister_response.status_code == 404:
            print(f"{self.mar_name} might already be unregistered.")
        else:
            print(f"Unknown error when unregistering {self.mar_name}")
            print(unregister_response.text)
            return False
        
        return True


    def is_torchserve_running(self) -> bool:
        
        # check inference api
        health_url = f"{self.inference_url}/ping"
        try:
            health_response = requests.get(health_url)
        except Exception:
            traceback.print_exc()
            return False
        if health_response.status_code != 200:
            return False

        # check management api
        models_url = f"{self.management_url}/models"
        try:
            models_response = requests.get(models_url)
        except Exception:
            traceback.print_exc()
            return False
        if models_response.status_code != 200:
            return False

        return True


    def write_report(self, reports: dict) -> None:
        """
        Writes reports to csv.
        Automatically creates file with columns according to `reports`.

        reports = {
            "column_1": "value_1",
            "column_2": "value_2",
            ...
        }
        """
        csv_path = self.report_folder / self.report_filename

        reports = {k: str(v).replace("\n", "").replace(",", "") for k, v in reports.items()}

        # create new file and fill columns
        if not csv_path.exists():
            with open(csv_path, "a") as f:
                f.write(",".join(reports.keys()) + "\n")

        # fill entries
        with open(csv_path, "a") as f:
            f.write(",".join(reports.values()) + "\n")


    def benchmark(self, **kwargs) -> None:
        """
        Start benchmarking now.
        Every iteration will send `hit_size` hit each with incrementing `batch_size`.
        """

        if not self.register_model():
            print(f"Benchmark for {self.mar_name} stopped.")
            return

        batch_size = self.starting_batch_size
        
        with tqdm() as pbar:
            while True:
                
                extra_info = {
                    "batch_size": batch_size,
                    "hit_size": self.hit_size,
                }

                pbar.set_postfix(**extra_info)
                
                # how long the client have to wait
                start_time = time.perf_counter()
                results = self.multi_hit(**extra_info, **kwargs)
                end_time = time.perf_counter()
                
                extra_info["full_operation_time"] = end_time - start_time

                # determine stop or not
                # user can write csv in handle_result
                should_continue = self.handle_results(results, **extra_info, **kwargs)
                if not should_continue:
                    break

                batch_size += self.batch_size_increments
                pbar.update(1)
        
        if not self.unregister_model():
            print(f"{self.mar_name} cannot be unregistered. Check the management API.")

    
    def multi_hit(self, **kwargs) -> list:
        
        # simulate sending at the same time
        with ThreadPoolExecutor() as executor:
            futures = [executor.submit(self.send_single_hit, **kwargs) for _ in range(self.hit_size)]        

        return [future.result() for future in futures]


    def send_single_hit(self, **kwargs) -> requests.Response:
        inference_model_url = f"{self.inference_url}/predictions/{self.mar_name}"
        files, metadata = self.prepare_single_hit(**kwargs)
        start_time = time.perf_counter()
        r = requests.post(inference_model_url, files=files)
        end_time = time.perf_counter()
        metadata["response_waiting_time"] = end_time - start_time
        return r, metadata


    @abstractmethod
    def prepare_single_hit(self, batch_size: int, **kwargs) -> tuple:
        """
        Prepare dict suitable for requests.post' `files` param.
        Also prepare additional information found using dict.
        Use batch_size given to control how much data.
        Returns a tuple, (files, additional_info)

        Example:
        * get batch_size number of images
        * calculate total_size and total time
        * files = {"cat1": <cat1.jpg>, "cat2": <cat2.jpg>}
        * metadata = {"total_size": 12312, "imread_time": 4}
        * return files, metadata
        """
        pass


    @abstractmethod
    def handle_results(self, results: list, **kwargs) -> bool:
        """
        `results` contains hit_size number of whatever you send on prepare_single_hit.
        Return True to continue loop.
        Return False to stop benchmark loop.
        You can write csv file in the provided method `self.write_report()`
        """
        pass

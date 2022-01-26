import shutil



ERROR = "\033[91m" + "[ERROR]" + "\033[0m"
WARN = "\033[93m" + "[WARN ]" + "\033[0m"
OK = "\033[92m" + "[OK   ]" + "\033[0m"
NOTE = "\033[94m" + "[NOTE ]" + "\033[0m"


def _check_torchserve():

    # torchserve server
    torchserve_bin = shutil.which("torchserve")
    if torchserve_bin is None:
        print(ERROR, "torchserve (server) is not installed")
    else:
        print(OK, f"torchserve bin location: {torchserve_bin}")

    # ts module
    try:
        import ts
    except ImportError:
        print(WARN, "ts (module) is not installed, some handler may require it for the BaseHandler class")
    else:
        print(OK, f"ts version: {ts.__version__}")


def _check_torch_model_archiver():
    torch_model_archiver_bin = shutil.which("torch-model-archiver")
    if torch_model_archiver_bin is None:
        print(ERROR, "torch-model-archiver is not installed")
    else:
        print(OK, f"torch-model-archiver bin location: {torch_model_archiver_bin}")


def _check_pytorch_and_cuda():

    # import torch
    torch_imported = False
    try:
        import torch
        torch_imported = True
    except ImportError:
        print(ERROR, "PyTorch is not installed")
    else:
        print(OK, f"PyTorch version: {torch.__version__}")

    # check cuda availability
    if not torch_imported:
        print(ERROR, "Cannot check CUDA availability because PyTorch is not installed")
    else:
        cuda_available = torch.cuda.is_available()
        if cuda_available:
            print(OK, f"CUDA is available, CUDA version {torch.version.cuda}")
        else:
            print(WARN, "CUDA is not available, models cannot use GPU.")

    # check compute capabilities
    if not torch_imported:
        print(ERROR, "Cannot check CUDA compute capabilities because PyTorch is not installed")
    elif not cuda_available:
        print(WARN, "Cannot check CUDA compute capabilities because CUDA is not available")
    else:
        arch_list = torch.cuda.get_arch_list()
        gpu_count = torch.cuda.device_count()
        for gpu_id in range(gpu_count):
            gpu_props = torch.cuda.get_device_properties(gpu_id)
            gpu_name = gpu_props.name
            gpu_major = gpu_props.major
            gpu_minor = gpu_props.minor
            gpu_compute_capability = f"sm_{gpu_major}{gpu_minor}"
            if gpu_compute_capability in arch_list:
                print(OK, f"cuda:{gpu_id} {gpu_name} with compute capabilities {gpu_compute_capability}, is supported by current PyTorch")
            else:
                print(WARN, f"cuda:{gpu_id} {gpu_name} with compute capabilities {gpu_compute_capability}, is not supported by current PyTorch and some features may break. Supported: {arch_list}")


def _final_warning():
    print(NOTE, "If the .mar file contains `requirements.txt`, it may change installed PyTorch version")


def environment_check():
    """Prints to stdout information about TorchServe environment"""
    _check_torchserve()
    _check_torch_model_archiver()
    _check_pytorch_and_cuda()
    _final_warning()

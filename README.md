# tstool
TorchServe helper tools.

# Installation
This package is not on PyPI yet.
```
pip install -U git+https://github.com/evanarlian/tstool.git 
```

# Check TorchServe environment
Quick check to know whether the Python virtual environment can run TorchServe correctly.
```python
import tstool
tstool.environment_check()
```
If everything is right, will output:
```diff
[OK   ] torchserve bin location: /home/user/miniconda3/envs/torchserve/bin/torchserve
[OK   ] ts version: 0.5.0
[OK   ] torch-model-archiver bin location: /home/user/miniconda3/envs/torchserve/bin/torch-model-archiver
[OK   ] PyTorch version: 1.9.0+cu111
[OK   ] CUDA is available, CUDA version 11.1
[OK   ] cuda:0 NVIDIA GeForce RTX 3070 Ti with compute capabilities sm_86, is supported by current PyTorch
[NOTE ] If the .mar file contains `requirements.txt`, it may change installed PyTorch version
```
If not, will output:
```
[ERROR] torchserve (server) is not installed
[WARN ] ts (module) is not installed, some handler may require it for the BaseHandler class
[ERROR] torch-model-archiver is not installed
[ERROR] PyTorch is not installed
[ERROR] Cannot check CUDA availability because PyTorch is not installed
[ERROR] Cannot check CUDA compute capabilities because PyTorch is not installed
[NOTE ] If the .mar file contains `requirements.txt`, it may change installed PyTorch version
```

# Minimal working example
```python
import os
import torch
import tstool

# get current pid
pid = os.getpid()

# dummy function
@tstool.resource_monitor(pid=pid)
def say_hello():
    # fake cuda tensor allocation
    my_tensor = torch.randn(1000, device="cuda")
    # do some hard cpu work
    my_list = [i ** 0.42 for i in range(1000000)]
    return "hello"

# original function returns will always be on the left
word, monitored = say_hello()

print(word)
print(monitored)
```
Outputs:
```
hello
{
    'gpu_mem_mib': 1521,
    'time_ms': 8091.83809813112,
    'cpu_percent_min': 0.0,
    'cpu_percent_max': 182.9,
    'cpu_percent_avg': 34.807936507936496,
    'ram_uss_bytes_min': 762208256,
    'ram_uss_bytes_max': 4760518656,
    'ram_uss_bytes_avg': 2773923339.3777776
}
```

# Limitations
GPU memory cannot be monitored in Windows, `nvidia-smi` does not even show per-process memory usage.
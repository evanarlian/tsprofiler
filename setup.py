from setuptools import setup


def readme():
    with open("README.md") as f:
        return f.read()

setup(
    name="tsprofiler",
    version="0.1.0",
    description="Helper tool to profile running TorchServe model",
    long_description=readme(),
    url="https://github.com/evanarlian/tsprofiler",
    author="Evan Arlian",
    author_email="evanarlian2000@gmail.com",
    license="MIT",
    packages=["tsprofiler"],
    install_requires=[
        "requests",
        "pandas",
        "tqdm",
    ],
)



# setup(

# name = tsprofiler
# version = 0.0.1
# author = Evan Arlian
# author_email = evanarlian2000@gmail.com
# description = Helper tool to profile running TorchServe model
# long_description = file: README.md
# long_description_content_type = text/markdown
# url = https://github.com/evanarlian/tsprofiler
# classifiers =
#     Programming Language :: Python :: 3
#     License :: OSI Approved :: MIT License
#     Operating System :: OS Independent

# [options]
# packages = find:
# python_requires = >=3.7
# include_package_data = True

# )
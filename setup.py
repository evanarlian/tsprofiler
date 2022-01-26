from setuptools import setup


def readme():
    with open("README.md") as f:
        return f.read()


setup(
    name="tstool",
    version="0.1.1",
    description="TorchServe helper tools",
    long_description=readme(),
    url="https://github.com/evanarlian/tstool",
    author="Evan Arlian",
    author_email="evanarlian2000@gmail.com",
    license="MIT",
    include_package_data=True,
    packages=["tstool"],
    install_requires=[
        # "xmltodict",
        "requests",
        "pandas",
    ],
)

# NOTE
# https://python-packaging.readthedocs.io/en/latest/everything.html
# pip install git+https://github.com/evanarlian/tstool.git

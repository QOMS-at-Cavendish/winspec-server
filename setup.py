from setuptools import setup, find_packages

setup(
    name="winspec",
    version="0.1",
    packages=find_packages(),
    scripts=["start_winspec_server.py"],

    author="John Jarman",
    author_email="jcj27@cam.ac.uk",
    description="Websockets server for remotely operating Winspec32"
)
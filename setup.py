"""setup.py for winspec

Installs winspec package.

Example::
    $ python setup.py install
"""

from setuptools import setup, find_packages

setup(
    name="winspec",
    version="0.1",
    packages=find_packages(),
    scripts=["start_server.py"],
    install_requires=[
          'websockets',
          'pyjwt',
      ],

    author="John Jarman",
    author_email="jcj27@cam.ac.uk",
    description="Websockets server for remotely operating Winspec32"
)
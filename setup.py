import os

from codecs import open
from setuptools import setup, find_packages


here = os.path.abspath(os.path.dirname(__file__))

with open(os.path.join(here, 'requirements.txt'), encoding='utf-8') as fp:
    requirements = fp.read().splitlines()

setup(
    name='pyswagger',
    version='0.1.0',
    description=(
        'A Python client that reads a JSON formatted Swagger schema ' +
        'generates methods to interface directly with the HTTP API'
    ),
    url='https://cto-github.cisco.com/rightlag/pyswagger',
    author='Jason Walsh',
    author_email='jaswalsh@cisco.com',
    license='MIT',
    classifiers=[
        'Development Status :: 3 - Alpha',
    ],
    keywords='swagger client sdk',
    packages=find_packages(exclude=['test*']),
    install_requires=requirements
)

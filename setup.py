from setuptools import setup, find_packages

# Read the contents of your README file
from os import path
this_directory = path.abspath(path.dirname(__file__))

with open('README.md', encoding='utf-8') as f:
    long_description = f.read()


with open('MercurySQL/VERSION', 'r') as f:
    version = f.read().strip()

setup(
    name='MercurySQL',
    version=version,
    description='Operate sql in a more pythonic way.',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='Bernie J. Huang',
    author_email='berniehuang2008@163.com',
    url='https://github.com/BernieHuang2008/MercurySQL',
    packages=find_packages(),
    package_data={
        'MercurySQL': ['VERSION'],
    },
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
    ],
    install_requires=[
        "mysql-connector-python",
    ],
)

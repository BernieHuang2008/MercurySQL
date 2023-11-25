from setuptools import setup, find_packages

# Read the contents of your README file
from os import path
this_directory = path.abspath(path.dirname(__file__))
with open(path.join(this_directory, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='MercurySQLite',
    version='0.1.1.2',
    description='Use built-in sqlite3 library to operate sql in a more pythonic way.',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='Bernie J. Huang',
    author_email='berniehuang2008@163.com',
    url='https://github.com/BernieHuang2008/MercurySQLite',
    packages=find_packages(),
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
    install_requires=[],
)
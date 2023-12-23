# replace '__!VERSION!__' with the version number in the file 'MercurySQL/VERSION'
# and write the result to 'setup.py'

import os

def get_version():
    with open('MercurySQL/VERSION', 'r') as f:
        return f.read().strip()
    
def get_setup_py():
    with open('setup.py', 'r') as f:
        return f.read()
    
def write_setup_py(content):
    with open('setup.py', 'w') as f:
        f.write(content)

def main():
    version = get_version()
    setup_py = get_setup_py()
    setup_py = setup_py.replace('__!VERSION!__', version)
    write_setup_py(setup_py)

if __name__ == '__main__':
    main()

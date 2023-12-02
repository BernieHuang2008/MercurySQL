import re

version = re.search(
    r'^\s*version\s*=\s*[\'\"]([^\'\"]*)[\'\"]',
    open('setup.py').read(),
    re.MULTILINE
).group(1)

print(version)

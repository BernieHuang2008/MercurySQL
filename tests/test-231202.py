import re

pattern = r"^\s*version\s*=\s*['\"]([^'\"]*)['\"]"
string = """
    name='MercurySQLite',
    version='0.1.1.2',
    description='Use built-in sqlite3 library to operate sql in a more pythonic way.',
    """

match = re.search(pattern, string, re.MULTILINE)
if match:
    version = match.group(1)
    print(version)

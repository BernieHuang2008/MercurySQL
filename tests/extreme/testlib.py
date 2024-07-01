import difflib
import io
import sys
import re

def set_path():
    """
    Set the path to the root directory of the project.
    """
    sys.path.insert(0, '../../')
    sys.path.insert(0, './')

def set_io():
    """
    Set the output to a StringIO object.
    """
    global SCREEN_OUTPUT, TEST_OUTPUT
    SCREEN_OUTPUT = sys.stdout
    TEST_OUTPUT = io.StringIO()
    sys.stdout = TEST_OUTPUT

def reset_io():
    """
    Reset the output to the screen.
    """
    global SCREEN_OUTPUT
    sys.stdout = SCREEN_OUTPUT


def color_diff(expected, actual):
    """
    Highlight the differences between two strings.
    """
    diff = difflib.unified_diff(
        expected.splitlines(), actual.splitlines(), lineterm='')
    diff_str = '\n'.join(diff)
    for line in diff_str.splitlines():
        if line.startswith('+'):
            # Green for added lines
            print('\033[32m(excess )' + line + '\033[0m')
        elif line.startswith('-'):
            # Red for removed lines
            print('\033[31m(missing)' + line + '\033[0m')
        else:
            print(line)


def process_output(s):
    """
    Process the output string, remove some random things.
    """
    s = s.strip()

    # Remove the object address
    pattern = r' object at 0x[0-9A-Fa-f]+>'
    s = re.sub(pattern, ' object at 0xPYTHON_ADDRESS>', s)

    return s


def check_answer(EXPECTED_OUTPUT):
    """
    Check the answer between `TEST_OUTPUT` and `EXPECTED_OUTPUT`.
    """
    reset_io()

    global TEST_OUTPUT
    raw_output = TEST_OUTPUT.getvalue()
    TEST_OUTPUT = process_output(raw_output)
    EXPECTED_OUTPUT = process_output(EXPECTED_OUTPUT)

    if TEST_OUTPUT == EXPECTED_OUTPUT:
        print("\033[32mTest Passed!\033[0m")
    else:
        print("\033[31mTest Failed!\033[0m")
        print("Expected Output:")
        print(EXPECTED_OUTPUT)
        print('='*30+'\n')
        print("Raw Output:")
        print(raw_output)

        color_diff(EXPECTED_OUTPUT, TEST_OUTPUT)

        raise Exception("Test Failed!")


### Testlib ###
def pre_do():
    """
    Pre do before test starts:
    - Set the path.
    - Set the output.
    """
    set_path()
    set_io()

def check(EXPECTED_OUTPUT):
    """
    Check the answer between `TEST_OUTPUT` and `EXPECTED_OUTPUT`.
    """
    check_answer(EXPECTED_OUTPUT)


if __name__:
    pre_do()

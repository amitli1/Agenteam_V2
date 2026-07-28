"""
Tester for LlmCommandParser.split_user_command.

Run from the `project_code` directory (so the relative
"llm/prompt_split_command.txt" path resolves correctly):

    cd project_code
    python -m llm.llm_command_parser_tester
"""

from project_code.llm.llm_command_parser import LlmCommandParser


def _check(actual, expected, test_name):
    """Compare parsed output against expected list of dicts."""
    ok = actual == expected
    status = "PASS" if ok else "FAIL"
    print(f"[{status}] {test_name}")
    if not ok:
        print(f"    expected: {expected}")
        print(f"    actual  : {actual}")
    return ok


def test_1(parser, text):
    result = parser.split_user_command(text)
    expected = [
        {
            "team_member": "buddy",
            "fly_command": "",
            "vision_command": "describe",
        }
    ]
    return _check(result, expected, text)


def test_2(parser, text):
    result = parser.split_user_command(text)
    expected = [
        {
            "team_member": "team",
            "fly_command": "go to junction number five",
            "vision_command": "",
        }
    ]
    return _check(result, expected, text)



def test_3(parser, text):

    # hey team, go to junction number 2 and hold it

    result = parser.split_user_command(text)
    expected = [
        {
            "team_member": "team",
            "fly_command": "go to junction number 2",
            "vision_command": "hold it",
        },

    ]
    return _check(result, expected, text)

def test_4(parser, text):
    result = parser.split_user_command(text)
    expected = [
        {
            "team_member": "jarvis",
            "fly_command": "go home",
            "vision_command": "",
        }
    ]
    return _check(result, expected, text)

def test_5(parser, text):

    # hey jarvis, surround the building and tell me what you see

    result = parser.split_user_command(text)
    expected = [
        {
            "team_member": "jarvis",
            "fly_command": "surround the building",
            "vision_command": "tell me what you see",
        }
    ]
    return _check(result, expected, text)

def test_6(parser, text):

    # "hey team, hold the building and look for man with blue shirt"

    result = parser.split_user_command(text)
    expected = [
        {
            "team_member": "team",
            "fly_command": "",
            "vision_command": "hold the building and look for man with blue shirt",
        }
    ]
    return _check(result, expected, text)


def test_7(parser, text):

    # hey jarvis, point to the car or cow

    result = parser.split_user_command(text)
    expected = [
        {
            "team_member": "jarvis",
            "fly_command": "",
            "vision_command": "point to the car or cow",
        }
    ]
    return _check(result, expected, text)



def test_8(parser, text):

    # hey jarvis, describe the person near the car

    result = parser.split_user_command(text)
    expected = [
        {
            "team_member": "jarvis",
            "fly_command": "",
            "vision_command": "describe the person near the car",
        }
    ]
    return _check(result, expected, text)

def run_all_tests():
    parser = LlmCommandParser()

    tests = [
        (test_1, "Buddy describe"),
        (test_2, "hey team, go to junction number five"),
        (test_3, "hey team, go to junction number 2 and hold it"),
        (test_4, "hey jarvis, go home"),
        (test_5, "hey jarvis, surround the building and tell me what you see"),
        (test_6, "hey team, hold the building and look for man with blue shirt"),
        (test_7, "hey jarvis, point to the car or cow"),
        (test_8, "hey jarvis, describe the person near the car"),
    ]

    results = []
    for test, text in tests:
        try:
            results.append(test(parser, text))
        except Exception as e:
            print(f"[ERROR] {test.__name__} raised an exception: {e}")
            results.append(False)

    passed = sum(results)
    total = len(results)
    print(f"\n{passed}/{total} tests passed.")


if __name__ == '__main__':
    run_all_tests()
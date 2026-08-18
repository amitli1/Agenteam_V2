"""
Tester for LlmCommandParser_V2.split_user_command.

Run from the `project_code` directory (so the relative
"llm/mission_command_parser_v2.txt" path resolves correctly):

    cd project_code
    python -m llm.llm_command_parser_v2_tester
"""

from project_code.llm.llm_command_parser_v2 import LlmCommandParser_V2
import time


def _run(parser, text):
    """Run split_user_command and measure elapsed time."""
    start_time = time.time()
    result = parser.split_user_command(text)
    elapsed = time.time() - start_time
    return result, elapsed


def _check(actual, expected, test_name, elapsed):
    """Compare parsed output against expected dict."""
    ok = actual == expected
    status = "PASS" if ok else "FAIL"
    print(f"[{status}] [{elapsed:.1f} sec] {test_name}")
    if not ok:
        print(f"    expected: {expected}")
        print(f"    actual  : {actual}")
    return ok


def test_1(parser, text):
    # hey buddy fly to building number two
    result, elapsed = _run(parser, text)
    expected = {
        "fly_command": {"fly_cmd_type": "fly", "location": "building number two"},
        "vision_command": {"vision_cmd_type": "", "objects": ""},
        "team_member": "buddy",
        "need_more_data": False,
    }
    return _check(result, expected, text, elapsed)


def test_2(parser, text):
    # hey team fly home
    result, elapsed = _run(parser, text)
    expected = {
        "fly_command": {"fly_cmd_type": "fly", "location": "home"},
        "vision_command": {"vision_cmd_type": "", "objects": ""},
        "team_member": "team",
        "need_more_data": False,
    }
    return _check(result, expected, text, elapsed)


def test_3(parser, text):
    # hey jarvis surround the junction
    result, elapsed = _run(parser, text)
    expected = {
        "fly_command": {"fly_cmd_type": "surround", "location": "junction"},
        "vision_command": {"vision_cmd_type": "", "objects": ""},
        "team_member": "jarvis",
        "need_more_data": False,
    }
    return _check(result, expected, text, elapsed)


def test_4(parser, text):
    # hey jarvis surround the building and look for people and vehicles
    result, elapsed = _run(parser, text)
    expected = {
        "fly_command": {"fly_cmd_type": "surround", "location": "building"},
        "vision_command": {"vision_cmd_type": "summary", "objects": "people and vehicles"},
        "team_member": "jarvis",
        "need_more_data": False,
    }
    return _check(result, expected, text, elapsed)


def test_5(parser, text):
    # hey jarvis hold the junction
    result, elapsed = _run(parser, text)
    expected = {
        "fly_command": {"fly_cmd_type": "", "location": ""},
        "vision_command": {"vision_cmd_type": "hold", "objects": ""},
        "team_member": "jarvis",
        "need_more_data": False,
    }
    return _check(result, expected, text, elapsed)


def test_6(parser, text):
    # buddy hold the junction and tell me if you see red car or blue truck
    result, elapsed = _run(parser, text)
    expected = {
        "fly_command": {"fly_cmd_type": "", "location": ""},
        "vision_command": {"vision_cmd_type": "hold", "objects": "red car or blue truck"},
        "team_member": "buddy",
        "need_more_data": False,
    }
    return _check(result, expected, text, elapsed)


def test_7(parser, text):
    # buddy follow the yellow car
    result, elapsed = _run(parser, text)
    expected = {
        "fly_command": {"fly_cmd_type": "follow", "location": ""},
        "vision_command": {"vision_cmd_type": "follow", "objects": "yellow car"},
        "team_member": "buddy",
        "need_more_data": False,
    }
    return _check(result, expected, text, elapsed)


def test_8(parser, text):
    # hey team follow
    result, elapsed = _run(parser, text)
    expected = {
        "fly_command": {"fly_cmd_type": "follow", "location": ""},
        "vision_command": {"vision_cmd_type": "follow", "objects": ""},
        "team_member": "team",
        "need_more_data": True,
    }
    return _check(result, expected, text, elapsed)


def test_9(parser, text):
    # buddy describe
    result, elapsed = _run(parser, text)
    expected = {
        "fly_command": {"fly_cmd_type": "", "location": ""},
        "vision_command": {"vision_cmd_type": "describe", "objects": ""},
        "team_member": "buddy",
        "need_more_data": False,
    }
    return _check(result, expected, text, elapsed)


def test_10(parser, text):
    # buddy describe the person in the car
    result, elapsed = _run(parser, text)
    expected = {
        "fly_command": {"fly_cmd_type": "", "location": ""},
        "vision_command": {"vision_cmd_type": "describe", "objects": "person in the car"},
        "team_member": "buddy",
        "need_more_data": False,
    }
    return _check(result, expected, text, elapsed)


def test_11(parser, text):
    # hey jarvis point at the yellow car
    result, elapsed = _run(parser, text)
    expected = {
        "fly_command": {"fly_cmd_type": "", "location": ""},
        "vision_command": {"vision_cmd_type": "point", "objects": "yellow car"},
        "team_member": "jarvis",
        "need_more_data": False,
    }
    return _check(result, expected, text, elapsed)

def test_12(parser, text):
    # hey jarvis surround the building and tell me what you see hey jarvis look for birds
    result, elapsed = _run(parser, text)
    expected = {
        "fly_command": {"fly_cmd_type": "surround", "location": "building"},
        "vision_command": {"vision_cmd_type": "summary", "objects": "birds"},
        "team_member": "jarvis",
        "need_more_data": False,
    }
    return _check(result, expected, text, elapsed)


def run_all_tests():
    parser = LlmCommandParser_V2()

    tests = [
        (test_1, "hey buddy fly to building number two"),
        (test_2, "hey team fly home"),
        (test_3, "hey jarvis surround the junction"),
        (test_4, "hey jarvis surround the building and look for people and vehicles"),
        (test_5, "hey jarvis hold the junction"),
        (test_6, "buddy hold the junction and tell me if you see red car or blue truck"),
        (test_7, "buddy follow the yellow car"),
        (test_8, "hey team follow"),
        (test_9, "buddy describe"),
        (test_10, "buddy describe the person in the car"),
        (test_11, "hey jarvis point at the yellow car"),
        (test_12, "hey jarvis surround the building and tell me what you see hey jarvis look for birds"),
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


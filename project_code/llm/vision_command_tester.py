"""
Tester for VisionParser.parse.

Run from the `project_code` directory (so the relative
"llm/vision_parser_prompt.txt" path resolves correctly):

    cd project_code
    python -m llm.vision_command_tester
"""

from project_code.llm.llm_vision_parser import VisionParser


def run_test(parser, text, expected):
    """
    Run a single test case and compare the parsed vision_commands against `expected`.

    text: the user command to parse.
    expected: list of dicts, each with the exact expected fields, e.g.
        [{"command": "summary", "objects": "vehicles, people", "need_more_data": False}]
    """
    actual = parser.parse(text)
    actual_commands = actual.get("vision_commands", [])

    ok = actual_commands == expected

    status = "PASS" if ok else "FAIL"
    print(f"[{status}] {text}")
    if not ok:
        print(f"    expected: {expected}")
        print(f"    actual  : {actual_commands}")
    return ok


def run_all_tests():
    parser = VisionParser()

    tests = [
        (
            "point to the red car or blue truck",
            [{"command": "point", "objects": "red car, blue truck", "need_more_data": False}],
        ),
        (
            "point",
            [{"command": "point", "objects": "", "need_more_data": True}],
        ),
        (
            "hold the junction",
            [{"command": "hold", "objects": "junction", "need_more_data": False}],
        ),
        (
            "Hold the junction and look for weapons",
            [{"command": "hold", "objects": "junction, weapons", "need_more_data": False}],
        ),
        (
            "surround and tell me about vehicles and people you see",
            [{"command": "summary", "objects": "vehicles, people", "need_more_data": False}],
        ),
        (
            "surround and tell me what you see",
            [{"command": "summary", "objects": "", "need_more_data": True}],
        ),
        (
            "describe",
            [{"command": "describe", "objects": "", "need_more_data": False}],
        ),
        (
            "describe the people",
            [{"command": "describe", "objects": "people", "need_more_data": False}],
        ),
    ]

    results = []
    for text, expected in tests:
        try:
            results.append(run_test(parser, text, expected))
        except Exception as e:
            print(f"[ERROR] {text}: raised an exception: {e}")
            results.append(False)

    passed = sum(results)
    total = len(results)
    print(f"\n{passed}/{total} tests passed.")


if __name__ == '__main__':
    run_all_tests()


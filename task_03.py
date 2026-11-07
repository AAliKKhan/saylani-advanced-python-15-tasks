"""
Task 03 | Recursive JSON Path Explorer
Recursion, nested lists/dictionaries

Problem: Implement find_paths(data, target) that recursively searches nested
dictionaries and lists and returns all paths whose value equals target.

Requirements:
  - Use dot notation for dictionary keys and [index] for list positions.
  - Preserve traversal order.
  - Do not treat bool True as numeric 1.

Sample / Expected Behavior:
  Input: {"a":[{"x":5},5],"b":{"y":5}}, target=5
  ->  ["a[0].x", "a[1]", "b.y"]
"""


def _matches(value, target):
    """Equality check that never confuses bools with numbers.

    In Python ``True == 1`` and ``False == 0``; this helper keeps the two
    domains apart so a bool is only ever matched by a bool target.
    """
    if isinstance(value, bool) != isinstance(target, bool):
        return False
    return value == target


def find_paths(data, target):
    """Return every path in ``data`` whose value equals ``target``.

    Dictionary keys are joined with dots, list positions with ``[i]``.
    Traversal follows insertion order for dicts and index order for lists,
    and the root path is the empty string.
    """
    results = []

    def walk(node, path):
        if _matches(node, target):
            results.append(path)

        if isinstance(node, dict):
            for key, value in node.items():
                child = f"{path}.{key}" if path else str(key)
                walk(value, child)
        elif isinstance(node, list):
            for index, value in enumerate(node):
                walk(value, f"{path}[{index}]")

    walk(data, "")
    return results


SAMPLE_DATA = {"a": [{"x": 5}, 5], "b": {"y": 5}}


if __name__ == "__main__":
    assert find_paths(SAMPLE_DATA, 5) == ["a[0].x", "a[1]", "b.y"]
    assert find_paths(SAMPLE_DATA, 6) == []
    assert find_paths([], 1) == []
    assert find_paths({"t": True, "n": 1}, True) == ["t"]
    assert find_paths({"t": True, "n": 1}, 1) == ["n"]
    assert find_paths({"t": True, "n": 1}, 0) == []
    assert find_paths([1, [2, [3]]], 3) == ["[1][1][0]"]
    assert find_paths("root", "root") == [""]
    print("all sample cases passed")

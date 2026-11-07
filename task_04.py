"""
Task 04 | Dependency Execution Planner
Graphs, sets, algorithms

Problem: Given tasks and prerequisite pairs (A,B) meaning A must finish before
B, return a valid execution order.

Requirements:
  - Detect cycles and raise ValueError with a clear message.
  - For multiple available tasks, select alphabetically first.
  - Reject unknown task names.

Sample / Expected Behavior:
  Tasks = ["build","test","deploy"]; dependencies = [("build","test"),
  ("test","deploy")] -> ["build","test","deploy"].
"""

import heapq


def plan_execution(tasks, dependencies):
    """Return a valid topological execution order for ``tasks``.

    ``dependencies`` holds (before, after) pairs: ``before`` must finish
    first. Ties between runnable tasks are broken alphabetically so the
    result is deterministic.

    Raises ValueError for unknown task names and for dependency cycles.
    """
    if tasks is None or dependencies is None:
        raise TypeError("tasks and dependencies are required")

    task_list = list(tasks)
    if len(set(task_list)) != len(task_list):
        duplicates = sorted({t for t in task_list if task_list.count(t) > 1})
        raise ValueError(f"duplicate task names: {duplicates}")

    known = set(task_list)

    dependents = {task: set() for task in task_list}
    indegree = {task: 0 for task in task_list}

    for pair in dependencies:
        if not isinstance(pair, (tuple, list)) or len(pair) != 2:
            raise ValueError(f"dependency must be a (before, after) pair, "
                             f"got {pair!r}")
        before, after = pair
        if before not in known:
            raise ValueError(f"unknown task in dependency: {before!r}")
        if after not in known:
            raise ValueError(f"unknown task in dependency: {after!r}")
        if before == after:
            raise ValueError(f"task cannot depend on itself: {before!r}")
        if after in dependents[before]:
            continue  # duplicate edge, ignore
        dependents[before].add(after)
        indegree[after] += 1

    # Min-heap of ready tasks => alphabetically first is always chosen.
    ready = [task for task in task_list if indegree[task] == 0]
    heapq.heapify(ready)

    order = []
    while ready:
        task = heapq.heappop(ready)
        order.append(task)
        for dependent in sorted(dependents[task]):
            indegree[dependent] -= 1
            if indegree[dependent] == 0:
                heapq.heappush(ready, dependent)

    if len(order) != len(task_list):
        remaining = sorted(set(task_list) - set(order))
        raise ValueError(
            "dependency cycle detected involving tasks: "
            + ", ".join(remaining)
        )

    return order


if __name__ == "__main__":
    assert plan_execution(["build", "test", "deploy"],
                          [("build", "test"), ("test", "deploy")]) == \
        ["build", "test", "deploy"]

    # Alphabetical tie-breaking: nothing depends on anything.
    assert plan_execution(["test", "build", "deploy"], []) == \
        ["build", "deploy", "test"]

    # Diamond with a cycle-free alternative keeps alphabetical order.
    assert plan_execution(["a", "b", "c"], [("c", "a"), ("c", "b")]) == \
        ["c", "a", "b"]

    try:
        plan_execution(["a", "b"], [("a", "b"), ("b", "a")])
    except ValueError as exc:
        assert "cycle" in str(exc).lower()
    else:
        raise AssertionError("cycle should raise ValueError")

    try:
        plan_execution(["a"], [("a", "zzz")])
    except ValueError as exc:
        assert "unknown" in str(exc).lower()
    else:
        raise AssertionError("unknown task should raise ValueError")

    print("all sample cases passed")

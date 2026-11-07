"""
Task 12 | Custom Iterable Range Toolkit
Iterators, generators, dunder methods

Problem: Create a ReversibleRange(start, stop, step) class supporting
iteration, reversed iteration, len(), and membership tests without
constructing a list.

Requirements:
  - Match Python range stop-exclusive semantics for positive and negative
    nonzero steps.
  - Implement __iter__, __reversed__, __len__, and __contains__.

Sample / Expected Behavior:
  ReversibleRange(2, 11, 3) -> [2, 5, 8]; reversed -> [8, 5, 2];
  5 in object -> True.
"""


class ReversibleRange:
    """A lazy range that never materialises its values as a list."""

    def __init__(self, start, stop=None, step=1):
        if stop is None:
            start, stop = 0, start
        for name, value in (("start", start), ("stop", stop),
                            ("step", step)):
            if isinstance(value, bool) or not isinstance(value, int):
                raise TypeError(f"{name} must be an int, got {value!r}")
        if step == 0:
            raise ValueError("step must not be 0")

        self._start = start
        self._stop = stop
        self._step = step

    @property
    def start(self):
        return self._start

    @property
    def stop(self):
        return self._stop

    @property
    def step(self):
        return self._step

    def _length(self):
        """Number of values, computed with integer arithmetic only."""
        if self._step > 0:
            if self._start >= self._stop:
                return 0
            return -((self._start - self._stop) // self._step)
        if self._start <= self._stop:
            return 0
        positive_step = -self._step
        return ((self._start - self._stop) + positive_step - 1) \
            // positive_step

    def __len__(self):
        return self._length()

    def __iter__(self):
        value = self._start
        if self._step > 0:
            while value < self._stop:
                yield value
                value += self._step
        else:
            while value > self._stop:
                yield value
                value += self._step

    def __reversed__(self):
        # Walk backwards without building an intermediate list.
        count = self._length()
        if count == 0:
            return
        last = self._start + (count - 1) * self._step
        value = last
        step = -self._step
        stop = self._start - self._step  # one step past the first value
        if self._step > 0:
            while value > stop:
                yield value
                value += step
        else:
            while value < stop:
                yield value
                value += step

    def __contains__(self, item):
        if isinstance(item, bool) or not isinstance(item, int):
            return False
        if self._length() == 0:
            return False
        if self._step > 0:
            if not (self._start <= item < self._stop):
                return False
            return (item - self._start) % self._step == 0
        if not (self._stop < item <= self._start):
            return False
        return (self._start - item) % (-self._step) == 0

    def __repr__(self):
        return (f"ReversibleRange({self._start}, {self._stop}, "
                f"{self._step})")

    def __eq__(self, other):
        if not isinstance(other, ReversibleRange):
            return NotImplemented
        return (self._start, self._stop, self._step) == \
               (other.start, other.stop, other.step)

    def __hash__(self):
        return hash((self._start, self._stop, self._step))


if __name__ == "__main__":
    forward = ReversibleRange(2, 11, 3)
    assert list(forward) == [2, 5, 8]
    assert list(reversed(forward)) == [8, 5, 2]
    assert len(forward) == 3
    assert 5 in forward
    assert 11 not in forward          # stop is exclusive
    assert 2 in forward
    assert 3 not in forward

    # Negative step (stop-exclusive as well)
    down = ReversibleRange(10, 0, -3)
    assert list(down) == [10, 7, 4, 1]
    assert list(reversed(down)) == [1, 4, 7, 10]
    assert len(down) == 4
    assert 1 in down and 0 not in down and 10 in down
    assert 2 not in down

    # Default forms and empty ranges
    assert list(ReversibleRange(3)) == [0, 1, 2]
    assert list(ReversibleRange(1, 4)) == [1, 2, 3]
    assert list(ReversibleRange(5, 5)) == []
    assert len(ReversibleRange(5, 5)) == 0
    assert list(reversed(ReversibleRange(5, 5))) == []
    assert 1 not in ReversibleRange(5, 5)
    assert list(ReversibleRange(0, 10, 4)) == [0, 4, 8]

    # Validation
    for bad in ((1, 5, 0),):
        try:
            ReversibleRange(*bad)
        except ValueError:
            pass
        else:
            raise AssertionError("step=0 must raise")
    try:
        ReversibleRange(1.5, 5)
    except TypeError:
        pass
    else:
        raise AssertionError("non-int bounds must raise")

    # No list is ever constructed: values are produced on demand.
    big = ReversibleRange(0, 10**9)
    assert len(big) == 10**9
    iterator = iter(big)
    assert next(iterator) == 0 and next(iterator) == 1

    print("all sample cases passed")

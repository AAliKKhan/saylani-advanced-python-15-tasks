"""
Task 02 | Longest Valid Window
Sliding window, dictionaries

Problem: Write longest_unique_window(text) to find the longest contiguous
substring with no repeated characters. Return the substring, start index, and
length.

Requirements:
  - Target O(n) time.
  - On equal-length windows, select the earliest.
  - Treat spaces and punctuation as characters.

Sample / Expected Behavior:
  Input: "abcabcbb" -> ("abc", 0, 3);  "" -> ("", 0, 0).
"""

EMPTY_RESULT = ("", 0, 0)


def longest_unique_window(text):
    """Return (substring, start_index, length) of the longest window with
    no repeated characters.

    Runs in O(n) using a sliding window plus a last-seen-index map.
    When several windows share the maximum length, the earliest one wins.
    """
    if not isinstance(text, str):
        raise TypeError(f"text must be a str, got {type(text).__name__}")
    if not text:
        return EMPTY_RESULT

    last_seen = {}
    window_start = 0
    best_start = 0
    best_length = 0

    for index, char in enumerate(text):
        previous = last_seen.get(char)
        if previous is not None and previous >= window_start:
            window_start = previous + 1
        last_seen[char] = index

        current_length = index - window_start + 1
        # Strict > keeps the earliest window on ties.
        if current_length > best_length:
            best_length = current_length
            best_start = window_start

    return (text[best_start:best_start + best_length], best_start, best_length)


if __name__ == "__main__":
    cases = [
        ("abcabcbb", ("abc", 0, 3)),
        ("", ("", 0, 0)),
        ("bbbbb", ("b", 0, 1)),
        ("pwwkew", ("wke", 2, 3)),
        ("dvdf", ("vdf", 1, 3)),
        ("aab", ("ab", 1, 2)),
        ("abba", ("ab", 0, 2)),
        (" ", (" ", 0, 1)),
        ("abc def!", ("abc def!", 0, 8)),
    ]
    for text, expected in cases:
        actual = longest_unique_window(text)
        assert actual == expected, f"{text!r}: {actual} != {expected}"
    print("all sample cases passed")

"""
Task 09 | Streaming Log Inspector
Generators, iterators, file handling

Problem: Write a generator read_errors(path) that streams a log file line by
line, yielding (line_number, timestamp, message) only for ERROR records. Build
summarize_errors() to count errors by date.

Requirements:
  - Do not load the whole file into memory.
  - Skip malformed lines while tracking their count.
  - Expected format: YYYY-MM-DD HH:MM:SS | LEVEL | message.

Sample / Expected Behavior:
  Input line: 2026-11-07 10:30:00 | ERROR | Connection lost
  -> (1, "2026-11-07 10:30:00", "Connection lost").
"""

from datetime import datetime

TIMESTAMP_FORMAT = "%Y-%m-%d %H:%M:%S"


def _parse_line(line):
    """Return (timestamp, level, message) or None when the line is malformed."""
    parts = line.split(" | ", 2)
    if len(parts) != 3:
        return None
    timestamp, level, message = parts
    try:
        datetime.strptime(timestamp, TIMESTAMP_FORMAT)
    except ValueError:
        return None
    return timestamp, level.strip(), message


def read_errors(path, stats=None):
    """Yield (line_number, timestamp, message) for each ERROR record.

    The file is streamed line by line, so memory use stays constant no matter
    how large the log is. Malformed lines are skipped; when ``stats`` is a
    dict it is updated in place with the keys 'lines', 'malformed' and
    'errors'. Line numbers are 1-based and count every line, skipped ones
    included.
    """
    if not isinstance(path, str) or not path:
        raise TypeError("path must be a non-empty string")

    counters = stats if stats is not None else {}
    counters.setdefault("lines", 0)
    counters.setdefault("malformed", 0)
    counters.setdefault("errors", 0)

    with open(path, "r", encoding="utf-8", errors="replace") as handle:
        for number, raw in enumerate(handle, start=1):
            line = raw.rstrip("\r\n")
            counters["lines"] += 1
            if not line.strip():
                counters["malformed"] += 1
                continue
            parsed = _parse_line(line)
            if parsed is None:
                counters["malformed"] += 1
                continue
            timestamp, level, message = parsed
            if level == "ERROR":
                counters["errors"] += 1
                yield number, timestamp, message


def summarize_errors(path, stats=None):
    """Return {'YYYY-MM-DD': error_count, ...} for the log file.

    Pass the same ``stats`` dict to both helpers if you also need the
    malformed-line counters afterwards.
    """
    counts = {}
    for _number, timestamp, _message in read_errors(path, stats):
        date = timestamp[:10]
        counts[date] = counts.get(date, 0) + 1
    return counts


SAMPLE_LOG = """\
2026-11-07 10:30:00 | INFO | service started
2026-11-07 10:30:01 | ERROR | Connection lost
not a log line at all
2026-11-07 11:45:12 | ERROR | Retrying request
2026-11-08 09:00:00 | WARNING | Disk almost full
2026-11-08 09:15:44 | ERROR | Timeout after 30s
bad-date 12:00:00 | ERROR | should be skipped
2026-11-08 09:59:59 | ERROR | Connection lost | with pipes
"""


def write_sample_log(path):
    """Generate a sample log file (included sample data for this task)."""
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(SAMPLE_LOG)
    return path


if __name__ == "__main__":
    import os
    import tempfile

    with tempfile.TemporaryDirectory() as folder:
        log_path = os.path.join(folder, "app.log")
        write_sample_log(log_path)

        stats = {}
        errors = list(read_errors(log_path, stats))
        assert errors == [
            (2, "2026-11-07 10:30:01", "Connection lost"),
            (4, "2026-11-07 11:45:12", "Retrying request"),
            (6, "2026-11-08 09:15:44", "Timeout after 30s"),
            (8, "2026-11-08 09:59:59", "Connection lost | with pipes"),
        ], errors
        assert stats["malformed"] == 2, stats
        assert stats["errors"] == 4
        assert stats["lines"] == 8

        counts = summarize_errors(log_path)
        assert counts == {"2026-11-07": 2, "2026-11-08": 2}, counts

    print("all sample cases passed")

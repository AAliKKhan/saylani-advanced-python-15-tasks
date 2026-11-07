"""
Task 13 | Booking Conflict Scheduler
Datetime, sorting, interval algorithms

Problem: Implement a room booking scheduler. Each booking has room, start
datetime, end datetime, and booking ID. Accept bookings only when they do not
overlap existing bookings for the same room.

Requirements:
  - Use datetime objects; reject end <= start and duplicate IDs.
  - Adjacent bookings are allowed.
  - Return conflicts for rejected requests.

Sample / Expected Behavior:
  Room A: 09:00-10:00 and 10:00-11:00 accepted; 09:30-10:30 rejected.
"""

from datetime import datetime

BOOKING_FIELDS = ("booking_id", "room", "start", "end")


class BookingConflict(ValueError):
    """Raised when a booking overlaps an existing one."""


class Booking:
    """Immutable value object describing a single room reservation."""

    __slots__ = ("_booking_id", "_room", "_start", "_end")

    def __init__(self, booking_id, room, start, end):
        if not isinstance(booking_id, str) or not booking_id.strip():
            raise ValueError("booking_id must be a non-empty string")
        if not isinstance(room, str) or not room.strip():
            raise ValueError("room must be a non-empty string")
        if not isinstance(start, datetime) or not isinstance(end, datetime):
            raise TypeError("start and end must be datetime objects")
        if end <= start:
            raise ValueError("end must be strictly after start "
                             f"(start={start.isoformat()}, "
                             f"end={end.isoformat()})")

        self._booking_id = booking_id.strip()
        self._room = room.strip()
        self._start = start
        self._end = end

    @property
    def booking_id(self):
        return self._booking_id

    @property
    def room(self):
        return self._room

    @property
    def start(self):
        return self._start

    @property
    def end(self):
        return self._end

    def overlaps(self, other):
        """Half-open intervals: [start, end). Touching ends do not overlap."""
        if self.room != other.room:
            return False
        return self.start < other.end and other.start < self.end

    def as_dict(self):
        return {
            "booking_id": self.booking_id,
            "room": self.room,
            "start": self.start.isoformat(),
            "end": self.end.isoformat(),
        }

    def __repr__(self):
        return (f"Booking({self.booking_id!r}, {self.room!r}, "
                f"{self.start.isoformat()} -> {self.end.isoformat()})")


class BookingScheduler:
    """Accepts non-overlapping bookings and records every rejection."""

    def __init__(self):
        self._bookings = {}
        self._by_room = {}
        self._conflicts = []

    @property
    def conflicts(self):
        """Requests rejected because they overlapped an existing booking."""
        return tuple(self._conflicts)

    def add(self, booking):
        """Try to schedule ``booking``.

        Returns True when accepted. Returns False (and records a conflict)
        when it overlaps an existing booking for the same room. Duplicate
        booking IDs and invalid ranges raise ValueError.
        """
        if not isinstance(booking, Booking):
            raise TypeError("booking must be a Booking instance")
        if booking.booking_id in self._bookings:
            raise ValueError(f"duplicate booking id: {booking.booking_id!r}")

        existing_list = self._by_room.setdefault(booking.room, [])
        for existing in existing_list:
            if booking.overlaps(existing):
                self._conflicts.append({
                    "booking": booking.as_dict(),
                    "conflicts_with": existing.as_dict(),
                    "reason": (f"overlaps {existing.booking_id} "
                               f"({existing.start.isoformat()} - "
                               f"{existing.end.isoformat()}) in room "
                               f"{booking.room!r}"),
                })
                return False

        # Insert sorted by start time so scanning stays cheap and ordered.
        position = 0
        while position < len(existing_list) \
                and existing_list[position].start <= booking.start:
            position += 1
        existing_list.insert(position, booking)
        self._bookings[booking.booking_id] = booking
        return True

    def add_many(self, bookings):
        """Schedule several bookings; returns the list of conflicts."""
        new_conflicts = []
        before = len(self._conflicts)
        for booking in bookings:
            self.add(booking)
        new_conflicts = list(self._conflicts[before:])
        return new_conflicts

    def get(self, booking_id):
        if booking_id not in self._bookings:
            raise KeyError(f"unknown booking id: {booking_id!r}")
        return self._bookings[booking_id]

    def bookings_for(self, room):
        """All accepted bookings for a room, ordered by start time."""
        return tuple(self._by_room.get(room, ()))

    def all_bookings(self):
        return tuple(sorted(self._bookings.values(),
                            key=lambda b: (b.start, b.booking_id)))

    def is_free(self, room, start, end):
        """True when [start, end) fits in ``room`` without overlapping."""
        probe = Booking("probe", room, start, end)
        return all(not probe.overlaps(b) for b in self.bookings_for(room))


def _dt(text):
    return datetime.strptime(text, "%Y-%m-%d %H:%M")


if __name__ == "__main__":
    scheduler = BookingScheduler()

    morning = Booking("B1", "A", _dt("2026-11-07 09:00"),
                      _dt("2026-11-07 10:00"))
    next_slot = Booking("B2", "A", _dt("2026-11-07 10:00"),
                        _dt("2026-11-07 11:00"))
    overlap = Booking("B3", "A", _dt("2026-11-07 09:30"),
                      _dt("2026-11-07 10:30"))

    assert scheduler.add(morning) is True     # accepted
    assert scheduler.add(next_slot) is True   # adjacent, accepted
    assert scheduler.add(overlap) is False    # conflict
    assert len(scheduler.conflicts) == 1
    assert scheduler.conflicts[0]["conflicts_with"]["booking_id"] == "B1"

    # Same window in another room is fine.
    other_room = Booking("B4", "B", _dt("2026-11-07 09:00"),
                         _dt("2026-11-07 10:00"))
    assert scheduler.add(other_room) is True

    # Duplicate IDs are rejected outright.
    try:
        scheduler.add(Booking("B1", "C", _dt("2026-11-08 09:00"),
                              _dt("2026-11-08 10:00")))
    except ValueError as exc:
        assert "duplicate" in str(exc)
    else:
        raise AssertionError("duplicate id accepted")

    # Invalid ranges are rejected.
    try:
        Booking("B5", "A", _dt("2026-11-07 11:00"),
                _dt("2026-11-07 11:00"))
    except ValueError:
        pass
    else:
        raise AssertionError("end <= start accepted")

    assert scheduler.is_free("A", _dt("2026-11-07 11:00"),
                             _dt("2026-11-07 12:00")) is True
    assert scheduler.is_free("A", _dt("2026-11-07 09:15"),
                             _dt("2026-11-07 09:45")) is False
    assert [b.booking_id for b in scheduler.bookings_for("A")] == \
        ["B1", "B2"]
    print("all sample cases passed")

"""
Task 07 | Employee Payroll Engine
Inheritance, polymorphism, abstract classes

Problem: Define abstract Employee with calculate_pay(). Implement
SalariedEmployee, HourlyEmployee, and CommissionEmployee with different pay
formulas. Generate a unified payroll summary.

Requirements:
  - Hourly overtime above 40 hours pays 1.5x.
  - Commission employees receive base + sales*rate.
  - Prevent direct instantiation of Employee.

Sample / Expected Behavior:
  Hourly rate=20, hours=45 -> 950; Commission base=500, sales=4000, rate=.10
  -> 900.
"""

from abc import ABC, abstractmethod

OVERTIME_THRESHOLD = 40.0
OVERTIME_MULTIPLIER = 1.5


def _require_number(name, value, minimum=0):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"{name} must be a number, got {value!r}")
    if value < minimum:
        raise ValueError(f"{name} must be >= {minimum}, got {value!r}")
    return value


def _require_text(name, value):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a non-empty string")
    return value.strip()


class Employee(ABC):
    """Abstract base class: cannot be instantiated directly."""

    def __init__(self, employee_id, name):
        self._employee_id = _require_text("employee_id", employee_id)
        self._name = _require_text("name", name)

    @property
    def employee_id(self):
        return self._employee_id

    @property
    def name(self):
        return self._name

    @property
    @abstractmethod
    def kind(self):
        """Short label used in payroll summaries."""

    @abstractmethod
    def calculate_pay(self):
        """Return the pay owed for the current period."""

    def payroll_row(self):
        return {
            "employee_id": self.employee_id,
            "name": self.name,
            "type": self.kind,
            "pay": round(float(self.calculate_pay()), 2),
        }

    def __repr__(self):
        return (f"{type(self).__name__}(id={self.employee_id!r}, "
                f"name={self.name!r})")


class SalariedEmployee(Employee):
    """Fixed salary for the period."""

    def __init__(self, employee_id, name, salary):
        super().__init__(employee_id, name)
        self._salary = _require_number("salary", salary)

    @property
    def kind(self):
        return "salaried"

    @property
    def salary(self):
        return self._salary

    def calculate_pay(self):
        return float(self._salary)


class HourlyEmployee(Employee):
    """Paid by the hour; hours beyond 40 earn 1.5x the regular rate."""

    def __init__(self, employee_id, name, hourly_rate, hours_worked):
        super().__init__(employee_id, name)
        self._hourly_rate = _require_number("hourly_rate", hourly_rate)
        self._hours_worked = _require_number("hours_worked", hours_worked)

    @property
    def kind(self):
        return "hourly"

    @property
    def hourly_rate(self):
        return self._hourly_rate

    @property
    def hours_worked(self):
        return self._hours_worked

    def calculate_pay(self):
        regular = min(self._hours_worked, OVERTIME_THRESHOLD)
        overtime = max(0.0, self._hours_worked - OVERTIME_THRESHOLD)
        return (regular * self._hourly_rate
                + overtime * self._hourly_rate * OVERTIME_MULTIPLIER)


class CommissionEmployee(Employee):
    """Base salary plus a percentage of sales."""

    def __init__(self, employee_id, name, base, sales, rate):
        super().__init__(employee_id, name)
        self._base = _require_number("base", base)
        self._sales = _require_number("sales", sales)
        self._rate = _require_number("rate", rate)

    @property
    def kind(self):
        return "commission"

    @property
    def base(self):
        return self._base

    @property
    def sales(self):
        return self._sales

    @property
    def rate(self):
        return self._rate

    def calculate_pay(self):
        return self._base + self._sales * self._rate


def payroll_summary(employees):
    """Return {'rows': [...], 'total': x} for any mix of Employee types."""
    if not isinstance(employees, (list, tuple)):
        raise TypeError("employees must be a list or tuple")

    rows = []
    total = 0.0
    seen_ids = set()
    for index, employee in enumerate(employees):
        if not isinstance(employee, Employee):
            raise TypeError(f"employee at index {index} is not an Employee")
        if employee.employee_id in seen_ids:
            raise ValueError(f"duplicate employee id: {employee.employee_id!r}")
        seen_ids.add(employee.employee_id)
        row = employee.payroll_row()
        rows.append(row)
        total += row["pay"]

    rows.sort(key=lambda r: r["employee_id"])
    return {"rows": rows, "total": round(total, 2)}


def format_summary(summary):
    lines = [f'{r["employee_id"]} {r["name"]} ({r["type"]}): {r["pay"]}'
             for r in summary["rows"]]
    lines.append(f'TOTAL: {summary["total"]}')
    return "\n".join(lines)


if __name__ == "__main__":
    # Abstract class cannot be instantiated.
    try:
        Employee("E0", "Nobody")
    except TypeError:
        pass
    else:
        raise AssertionError("Employee must be abstract")

    hourly = HourlyEmployee("E1", "Ali", hourly_rate=20, hours_worked=45)
    assert hourly.calculate_pay() == 950

    commission = CommissionEmployee("E2", "Sara", base=500, sales=4000,
                                    rate=0.10)
    assert commission.calculate_pay() == 900

    salaried = SalariedEmployee("E3", "Hina", salary=1200)
    assert salaried.calculate_pay() == 1200

    summary = payroll_summary([hourly, commission, salaried])
    assert summary["total"] == 950 + 900 + 1200
    print(format_summary(summary))

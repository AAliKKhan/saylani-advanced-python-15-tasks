"""
Task 14 | Command-Line Contact Manager
Modules, JSON, CRUD, validation

Problem: Build a menu-driven CLI contact manager with add, search, update,
delete, list, and persistent JSON storage. Each contact has a unique ID, name,
phone, and email.

Requirements:
  - Use separate functions/modules for storage and business logic.
  - Handle missing/corrupt JSON safely without silently deleting existing
    data.
  - Search names case-insensitively.

Sample / Expected Behavior:
  Add ID=1, name="Ayesha"; restart application; search "aye" -> contact
  remains available.
"""

import json
import os
import re
import shutil
import sys
import time

DEFAULT_STORAGE = "contacts.json"

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
PHONE_RE = re.compile(r"^\+?[0-9][0-9 ()\-]{5,}$")


# --------------------------------------------------------------------------
# Storage layer: JSON persistence only, no business rules.
# --------------------------------------------------------------------------
def load_contacts(path=DEFAULT_STORAGE):
    """Read contacts from ``path``.

    * Missing file  -> empty book (nothing to lose).
    * Corrupt file  -> the broken file is copied to ``<path>.corrupt-<ts>``
      so no data is silently destroyed, and an empty book is returned.
    """
    if not os.path.exists(path):
        return {}

    try:
        with open(path, "r", encoding="utf-8") as handle:
            data = json.load(handle)
    except (json.JSONDecodeError, UnicodeDecodeError, OSError) as exc:
        backup = _backup_corrupt(path)
        print(f"[warn] could not read {path} ({exc}); "
              f"original preserved at {backup}")
        return {}

    if not isinstance(data, dict):
        backup = _backup_corrupt(path)
        print(f"[warn] {path} does not hold a contact object; "
              f"original preserved at {backup}")
        return {}

    contacts = {}
    for key, value in data.items():
        if isinstance(value, dict) and "name" in value:
            contacts[str(key)] = value
    return contacts


def _backup_corrupt(path):
    stamp = time.strftime("%Y%m%d-%H%M%S")
    backup = f"{path}.corrupt-{stamp}"
    try:
        shutil.copy2(path, backup)
    except OSError:
        backup = path
    return backup


def save_contacts(contacts, path=DEFAULT_STORAGE):
    """Write contacts atomically so a crash cannot truncate the file."""
    directory = os.path.dirname(os.path.abspath(path))
    temp_path = os.path.join(directory, f".{os.path.basename(path)}.tmp")
    with open(temp_path, "w", encoding="utf-8") as handle:
        json.dump(contacts, handle, indent=2, ensure_ascii=False)
        handle.write("\n")
    os.replace(temp_path, path)


# --------------------------------------------------------------------------
# Business logic: validation, search, CRUD. No printing, no file access.
# --------------------------------------------------------------------------
def validate_name(name):
    if not isinstance(name, str) or not name.strip():
        raise ValueError("name must be a non-empty string")
    return name.strip()


def validate_phone(phone):
    if not isinstance(phone, str) or not PHONE_RE.match(phone.strip()):
        raise ValueError(f"invalid phone number: {phone!r}")
    return phone.strip()


def validate_email(email):
    if not isinstance(email, str) or not EMAIL_RE.match(email.strip()):
        raise ValueError(f"invalid email address: {email!r}")
    return email.strip()


def next_contact_id(contacts):
    """Highest numeric id + 1 (strings that are not numbers start at 1)."""
    numbers = [int(key) for key in contacts if str(key).isdigit()]
    return (max(numbers) + 1) if numbers else 1


def add_contact(contacts, name, phone, email, contact_id=None):
    """Create and store a contact; returns the new record."""
    record = {
        "name": validate_name(name),
        "phone": validate_phone(phone),
        "email": validate_email(email),
    }
    if contact_id is None:
        contact_id = next_contact_id(contacts)
    contact_id = str(contact_id)
    if contact_id in contacts:
        raise ValueError(f"contact id {contact_id!r} already exists")
    contacts[contact_id] = record
    return {"id": contact_id, **record}


def search_contacts(contacts, query):
    """Case-insensitive substring search over contact names."""
    if not isinstance(query, str):
        raise TypeError("query must be a string")
    needle = query.strip().lower()
    if not needle:
        return []
    return [{"id": cid, **rec} for cid, rec in sorted(
        contacts.items(), key=lambda kv: kv[1]["name"].lower())
        if needle in rec["name"].lower()]


def get_contact(contacts, contact_id):
    contact_id = str(contact_id)
    if contact_id not in contacts:
        raise KeyError(f"unknown contact id: {contact_id!r}")
    return {"id": contact_id, **contacts[contact_id]}


def update_contact(contacts, contact_id, **changes):
    """Update the given fields of an existing contact."""
    record = get_contact(contacts, contact_id)
    updated = dict(record)

    if "name" in changes and changes["name"] is not None:
        updated["name"] = validate_name(changes["name"])
    if "phone" in changes and changes["phone"] is not None:
        updated["phone"] = validate_phone(changes["phone"])
    if "email" in changes and changes["email"] is not None:
        updated["email"] = validate_email(changes["email"])

    updated.pop("id", None)
    contacts[str(contact_id)] = updated
    return {"id": str(contact_id), **updated}


def delete_contact(contacts, contact_id):
    contact_id = str(contact_id)
    record = get_contact(contacts, contact_id)
    del contacts[contact_id]
    return record


def list_contacts(contacts):
    return [{"id": cid, **rec} for cid, rec in sorted(
        contacts.items(), key=lambda kv: kv[1]["name"].lower())]


# --------------------------------------------------------------------------
# CLI layer
# --------------------------------------------------------------------------
MENU = """
1) Add contact
2) Search contact
3) Update contact
4) Delete contact
5) List contacts
0) Quit
"""


def _prompt(read, label):
    return read(f"{label}: ").strip()


def run_cli(read=input, write=print, path=DEFAULT_STORAGE):
    """Menu-driven loop. ``read``/``write`` are injectable for testing."""
    contacts = load_contacts(path)
    write(f"Contact manager (storage: {path}) - "
          f"{len(contacts)} contact(s) loaded")

    while True:
        write(MENU)
        choice = _prompt(read, "Choice")
        try:
            if choice == "0":
                save_contacts(contacts, path)
                write("Goodbye.")
                return contacts
            elif choice == "1":
                name = _prompt(read, "Name")
                phone = _prompt(read, "Phone")
                email = _prompt(read, "Email")
                contact = add_contact(contacts, name, phone, email)
                save_contacts(contacts, path)
                write(f"Added {contact['id']}: {contact['name']}")
            elif choice == "2":
                query = _prompt(read, "Name fragment")
                found = search_contacts(contacts, query)
                if not found:
                    write("No matches.")
                for item in found:
                    write(f"  [{item['id']}] {item['name']} | "
                          f"{item['phone']} | {item['email']}")
            elif choice == "3":
                contact_id = _prompt(read, "Contact id")
                name = _prompt(read, "New name (blank to keep)")
                phone = _prompt(read, "New phone (blank to keep)")
                email = _prompt(read, "New email (blank to keep)")
                contact = update_contact(
                    contacts, contact_id,
                    name=name or None, phone=phone or None,
                    email=email or None)
                save_contacts(contacts, path)
                write(f"Updated {contact['id']}: {contact['name']}")
            elif choice == "4":
                contact_id = _prompt(read, "Contact id")
                removed = delete_contact(contacts, contact_id)
                save_contacts(contacts, path)
                write(f"Deleted {removed['name']}")
            elif choice == "5":
                items = list_contacts(contacts)
                if not items:
                    write("Address book is empty.")
                for item in items:
                    write(f"  [{item['id']}] {item['name']} | "
                          f"{item['phone']} | {item['email']}")
            else:
                write("Unknown option.")
        except (ValueError, KeyError, TypeError) as exc:
            write(f"Error: {exc}")
            save_contacts(contacts, path)


def seed_sample_contacts(path=DEFAULT_STORAGE):
    """Write sample data for this task (id 1 = Ayesha, plus two more)."""
    contacts = {
        "1": {"name": "Ayesha", "phone": "03001234567",
              "email": "ayesha@example.com"},
        "2": {"name": "Bilal", "phone": "03117654321",
              "email": "bilal@example.com"},
        "3": {"name": "Caleb", "phone": "03221112233",
              "email": "caleb@example.com"},
    }
    save_contacts(contacts, path)
    return contacts


def self_test(path=None):
    """Exercise the whole stack against a temporary store (no TTY needed)."""
    import tempfile

    with tempfile.TemporaryDirectory() as folder:
        target = path or os.path.join(folder, "contacts.json")
        seed_sample_contacts(target)

        # Simulate an application restart: reload from disk.
        reloaded = load_contacts(target)
        found = search_contacts(reloaded, "aye")
        assert len(found) == 1 and found[0]["name"] == "Ayesha", found

        add_contact(reloaded, "Zoya", "03331234567", "zoya@example.com")
        update_contact(reloaded, "2", phone="03000000000")
        assert get_contact(reloaded, "2")["phone"] == "03000000000"
        assert len(list_contacts(reloaded)) == 4
        delete_contact(reloaded, "4")
        assert len(list_contacts(reloaded)) == 3
        save_contacts(reloaded, target)

        # Corrupt JSON must be preserved, not wiped.
        corrupt = os.path.join(folder, "broken.json")
        with open(corrupt, "w", encoding="utf-8") as handle:
            handle.write("{not valid json")
        assert load_contacts(corrupt) == {}
        backups = [f for f in os.listdir(folder) if f.startswith("broken.json")]
        assert any("corrupt" in name for name in backups), backups
        assert open(corrupt, encoding="utf-8").read() == "{not valid json"

        # Scripted CLI run with injected input.
        script = iter(["5", "2", "aye", "0"])
        buffer = []
        run_cli(read=lambda prompt: next(script),
                write=lambda msg="": buffer.append(str(msg)),
                path=target)
        assert any("Ayesha" in line for line in buffer)

    print("self test passed")
    return 0


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    path = DEFAULT_STORAGE
    if "--storage" in argv:
        path = argv[argv.index("--storage") + 1]
    if "--seed" in argv:
        seed_sample_contacts(path)
        print(f"Sample contacts written to {path}")
        return 0
    if "--selftest" in argv:
        return self_test()
    try:
        run_cli(path=path)
    except EOFError:
        # No interactive terminal available: run the scripted self test.
        print("\n[info] non-interactive input, running self test instead")
        return self_test()
    return 0


if __name__ == "__main__":
    sys.exit(main())

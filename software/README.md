# Software subgroup

The project card (D5) asks for a laptop service, database, dashboard and notification path. That work belongs to the software subgroup and is not in this folder yet.

Add it here, for example:

- `service/`: reads the Pico's USB serial lines, applies the CR-2 rate rules (over 100 mL/h for 5 min = advisory, rate doubles within 30 min = critical), stores readings in SQLite.
- `dashboard/`: live chart of mL/h and the alarm banner.
- `notify/`: outbound message to registered users.

The serial line format the firmware sends is in [`../docs/serial-output.md`](../docs/serial-output.md).

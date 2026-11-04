# Software subgroup

The project card (D5) asks for a laptop service, database, dashboard and notification path. That work belongs to the software subgroup. It runs and was demonstrated (dashboard at `localhost:5000` and a Telegram bot that sends CRITICAL alerts; see [`../docs/photos/`](../docs/photos/) 17 and 18 and [`../docs/videos/`](../docs/videos/)), but the source code still has to be added to this folder.

Add it here, for example:

- `service/`: reads the Pico's USB serial lines, applies the CR-2 rate rules (over 100 mL/h for 5 min = advisory, rate doubles within 30 min = critical), stores readings in SQLite.
- `dashboard/`: live chart of mL/h and the alarm banner.
- `notify/`: outbound message to registered users.

The serial line format the firmware sends is in [`../docs/serial-output.md`](../docs/serial-output.md).

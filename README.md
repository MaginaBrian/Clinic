# Mwangaza Clinic

Patients book 30-minute appointments with one of five doctors. A booked slot disappears for everyone else. Cancelling or rescheduling puts the old time back.

## Design

Doctors, patients, weekly working hours, and appointments are the only stored records. Empty slots are not stored. A slot is whatever 30-minute start fits inside a doctor's working blocks for that weekday, minus rows that are still `booked`.

A doctor can have more than one block on the same weekday. That is how a lunch break is modelled: 09:00–12:30 and 14:00–17:00, not one long shift with a hole punched in it.

Cancelled appointments stay in the table. The unique rule is partial: `(doctor, start_time)` must be unique only where `status = booked`. A cancelled row does not block the next booking, and freeing a slot does not require a delete.

Times are stored timezone-aware. Working hours are clinic wall-clock times, so the clinic zone is `Africa/Nairobi`. An offset-less booking time is read as Nairobi time.

Two requests for the same doctor cannot both pass the checks. Each write locks that doctor's row inside a transaction, then validates. The partial unique constraint is the backstop: if a second insert still races through, the database rejects it and the API returns 409.

There is no login in this version. A patient is a name and a phone number. The browser remembers the patient id on that device.

## API

Every error uses the same body:

```json
{"error": {"code": "slot_taken", "message": "...", "details": {}}}
```

`details` is present for payload validation only.

| Status | When |
| --- | --- |
| 400 | The request is wrong: bad payload, past time, inside the one-hour lead, outside working hours, or not on a 30-minute slot start. |
| 404 | That doctor, patient, or appointment does not exist. |
| 409 | The request is valid but clashes with current state: slot taken, patient already booked then, or the appointment is already cancelled. |

| Method | Path | Behaviour |
| --- | --- | --- |
| `GET` | `/doctors` | Active doctors. |
| `GET` | `/doctors/{id}/availability?date=YYYY-MM-DD` | Free 30-minute slots that day. A day the doctor does not work is an empty list, not an error. |
| `POST` | `/appointments` | Book `doctor_id`, `patient_id`, `start_time`, optional `notes`. |
| `GET` | `/appointments/{id}` | One appointment. |
| `PATCH` | `/appointments/{id}/cancel` | Body `{"reason": "..."}`. Reason is required. Already cancelled returns 409. The slot is bookable again. |
| `PATCH` | `/appointments/{id}/reschedule` | Body `{"start_time": "..."}`. The new time is checked with the same rules as a new booking. A cancelled appointment cannot be moved. |
| `POST` | `/patients` | Create a patient. |
| `GET` | `/patients/{id}` | One patient. |
| `GET` | `/patients/{id}/appointments` | Upcoming booked visits, soonest first. Cancelled visits are left out. |
| `GET` | `/health` | `{"status": "ok"}`. |

Bookings must start at least 60 minutes from now (`MIN_BOOKING_LEAD_MINUTES`).

Domain rules live in `backend/clinic/services/`. Views only parse input and call those functions. Tests cover availability, booking, cancel, reschedule, and the patient list (`python manage.py test clinic`, 42 tests).

## Run locally

```bash
python3 -m venv .venv
.venv/bin/pip install -r backend/requirements.txt
DEBUG=1 .venv/bin/python backend/manage.py migrate
DEBUG=1 .venv/bin/python backend/manage.py seed_clinic
DEBUG=1 .venv/bin/python backend/manage.py runserver 127.0.0.1:8000
```

In another terminal:

```bash
npm install --prefix frontend
npm run dev --prefix frontend
```

Open http://127.0.0.1:5173/. Vite proxies `/doctors`, `/appointments`, and `/patients` to port 8000. SQLite is the local database. Production uses `DATABASE_URL`.

## Deployment and CI/CD

The app is one Render web service. `build.sh` installs Python dependencies, builds the React app, and copies it to `backend/frontend_dist`. WhiteNoise serves that folder at `/`, and Django serves the API on the same host.

`render.yaml` is the blueprint. It creates the web service and a Postgres database in Frankfurt. `autoDeployTrigger` is `checksPass`, so Render ships a new build only after the GitHub Actions test check on that commit succeeds.

Public URL: https://mwangaza-clinic.onrender.com once the blueprint has finished its first deploy. Render will show the exact hostname on the service page if that name is already taken.

Pipeline (`.github/workflows/ci-cd.yml`):

- On every pull request and every push, GitHub Actions installs the Python dependencies and runs `python manage.py test clinic`.
- Render deploys the linked branch only after that check passes.
- The deploy runs `build.sh`, then starts the service. Startup migrates the database, seeds the five doctors, and then runs gunicorn. Free instances cannot use a separate pre-deploy command.

Approve the first deploy here:

https://render.com/deploy?repo=https://github.com/MaginaBrian/Clinic/tree/cursor/assessment-sections-693d

Sign in, connect GitHub if Render asks, review the web service and database, then click Deploy Blueprint. Later pushes to the linked branch go out on their own after the tests pass. After this branch is merged, point the service at `main` in the Render dashboard.

`SECRET_KEY` is generated by Render. `DEBUG` is false there. The five doctors are seeded on each release. The seed command is safe to run again.

## Section 4 — AI reflection

1. I used AI to file source into the paths I named and to strip comments, to draft commit messages, to list which backend files were still empty, to boot the API and the Vite app locally, and to draft this README, `build.sh`, `render.yaml`, and the GitHub Actions workflow. I wrote the booking rules, models, and UI myself and checked the result against the tests.

2. One paste of `backend/clinic/services/booking.py` was cut off at `return app`. I asked for that file to be placed as given. The suggestion finished the function as `return appt`, which is the appointment loaded in that function. Leaving the truncated name would have raised `NameError` on every reschedule. I kept that correction and re-read the function before committing.

3. While starting the app, `frontend/src/time.js` was still empty, so the tool invented formatters. I caught it because the page is supposed to show Nairobi times in a specific shape: 12-hour labels, a narrow no-break space, `dayKey` via `en-CA`, and `addDays` from a UTC date key. The invented file did not match. I replaced it with the version I had written and only then treated the page as ready.

4. I decided, without asking the tool, that cancelled visits stay stored and that only `booked` rows compete for a slot. Deleting the row would make the slot free too, but the clinic would lose the reason and the time of cancellation. I also decided that open slots are computed from weekly hours instead of being inserted as empty rows. Storing every future slot means a schedule change has to rewrite rows nobody has booked. Generating them keeps the working-hours table as the only schedule.

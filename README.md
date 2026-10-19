# Mwangaza Clinic — Appointment Booking

A clinic booking application for five doctors. Patients can view free 30-minute slots, book appointments, cancel, and reschedule.

| | Link |
|---|---|
| Live application | [https://mwangaza-clinic.onrender.com](https://mwangaza-clinic.onrender.com) |
| API health | [https://mwangaza-clinic.onrender.com/health](https://mwangaza-clinic.onrender.com/health) |
| Source code | [https://github.com/MaginaBrian/Clinic](https://github.com/MaginaBrian/Clinic) |

**Stack:** Django REST Framework, PostgreSQL (SQLite for local development), React + Vite, GitHub Actions, Render. No Docker required.

## 1. System design

### Models

| Model | Responsibility |
|---|---|
| `Doctor` | Name, specialty, active status |
| `WorkingHours` | Weekly working blocks, including breaks |
| `Patient` | Name, phone, optional email |
| `Appointment` | Doctor, patient, start/end time, status and cancellation details |

A doctor has many working-hour blocks and appointments. A patient can have many appointments.

### Architecture and decisions

- **Modular backend:** `models.py` stores data, `serializers.py` validates requests, `views.py` handles HTTP, and `services/booking.py` and `services/slots.py` hold business rules.
- **Generated availability:** The system calculates 30-minute slots from working hours, then removes booked and too-soon slots. This avoids maintaining a separate slots table.
- **Double-booking protection:** Booking and rescheduling use transactions and doctor row locks. PostgreSQL also enforces a partial unique constraint on `(doctor, start_time)` for active bookings.
- **Cancellation:** Appointments are marked `cancelled`, not deleted. This keeps a record and releases the slot.
- **Rescheduling:** The existing appointment is updated after validating the new slot. Its ID stays the same.
- **Time:** The clinic uses `Africa/Nairobi`. Datetimes are timezone-aware.
- **Deployment:** Django serves the built React application alongside the API, keeping hosting simple.

**Trade-offs:** A modular monolith is easier to run than microservices for five doctors. Doctor-level locking may limit write throughput at much larger scale, but it is appropriate here. Dynamically generated slots are simpler, although future doctor leave and holiday exceptions will need an additional model.

**Rules I chose:** Bookings must start on a valid 30-minute slot, be at least one hour ahead, and fit fully inside working hours. A patient cannot hold two appointments at the same time. A cancelled appointment cannot be rescheduled. An appointment that has started cannot be cancelled or rescheduled. An off-day returns an empty availability list.

**Future work:** Patient authentication and authorization, reminders, doctor leave, multiple clinics, and rate limiting. **This is a demonstration application; without authentication it must not be used for real patient data.**

## 2. API implementation

| Method | Endpoint | Purpose |
|---|---|---|
| `GET` | `/doctors` | List doctors |
| `GET` | `/doctors/{id}/availability?date=YYYY-MM-DD` | Show free slots |
| `POST` | `/appointments` | Book an appointment |
| `GET` | `/appointments/{id}` | View an appointment |
| `PATCH` | `/appointments/{id}/cancel` | Cancel with a reason |
| `PATCH` | `/appointments/{id}/reschedule` | Move to a valid slot |
| `POST` | `/patients` | Register a patient |
| `GET` | `/patients/{id}` | View a patient |
| `GET` | `/patients/{id}/appointments` | Upcoming appointments (bonus) |
| `GET` | `/health` | Health check |

Example booking request:

```bash
curl -X POST http://localhost:8000/appointments \
  -H 'Content-Type: application/json' \
  -d '{"doctor_id":1,"patient_id":1,"start_time":"2026-11-03T10:00:00+03:00"}'
```

The API returns `201` for a successful booking, `400` for invalid requests, `404` for missing records, and `409` for conflicts. Errors use a consistent JSON format: `{"error":{"code":"slot_taken","message":"..."}}`.

**Testing:** Tests are in `backend/clinic/tests/` and cover availability, working-hour boundaries, invalid dates, double bookings, cancellation, rescheduling, timezone handling, patient appointments, and database constraints. Run the tests to confirm results before submission.

## 3. Run locally and deploy

**Requirements:** Python 3.12+, Node.js 22+.

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export DEBUG=true
python manage.py migrate
python manage.py seed_clinic
python manage.py runserver
```

Backend: `http://localhost:8000`.

### Frontend (new terminal)

```bash
cd frontend
npm install
npm run dev
```

Frontend: `http://localhost:5173`. Commit the generated `frontend/package-lock.json` so CI and Render can use `npm ci`.

### Tests and build

```bash
cd backend
DEBUG=true python manage.py test

# In frontend/
npm run lint
npm run build
```

### Deployment and CI/CD

The project uses `render.yaml` and `build.sh` for a Render native Python web service and PostgreSQL database. The build script installs dependencies, builds React, collects static files, runs migrations, and seeds the five doctors. Gunicorn starts Django.

GitHub Actions (`.github/workflows/ci-cd.yml`) runs backend tests against PostgreSQL 16, checks migrations, and lints/builds the frontend on every pull request. A push or merge to **`main`** runs the checks again; if they pass, the workflow triggers Render using a deploy hook and checks `/health`.

**To activate deployment:**

1. Commit `frontend/package-lock.json` and ensure `build.sh` is executable (`chmod +x build.sh`).
2. Push the repository to GitHub and create a Render Blueprint from `render.yaml`.
3. Add the Render deploy-hook URL as the GitHub secret `RENDER_DEPLOY_HOOK_URL`.
4. Add the live application URL as the GitHub Actions variable `APP_URL`.
5. Merge a pull request into `main`, check GitHub Actions and Render logs, then confirm the deployed app and API health endpoint are responding.

**Note:** The public URL is supplied for deployment. Confirm that the app and `/health` endpoint respond and that GitHub Actions completes successfully. A health check does not independently prove that the newest commit is running.

## 4. AI reflection

### 1. What did you use AI for across the four sections?

I used ChatGPT during the system design phase to explore architectural approaches and organize the project into maintainable modules. AI helped me identify how to separate database models, API serializers, business logic, views, and automated tests.

I reviewed the suggested structure and organized the Django backend into dedicated services for booking and availability calculations. I also structured the React frontend around reusable components to keep the user interface maintainable.

AI was particularly useful in helping me consider separation of concerns and potential edge cases. However, I remained responsible for understanding the architecture, evaluating the suggested design, and ensuring it aligned with the clinic booking requirements.

For implementation and testing, I used AI-generated drafts for the Django API, React interface, and test cases. AI also helped draft the Render and GitHub Actions configuration. I reviewed these suggestions against the requirements and code.

### 2. Give one example where an AI suggestion improved your work. What did you prompt it with?

AI suggested a PostgreSQL partial unique constraint to prevent two active bookings for the same doctor and time. This is safer than checking availability in application code alone because two requests can arrive together. Cancelled appointments can still keep their history without blocking a new booking.

**Prompt:**

> How can I prevent two patients from booking the same 30-minute slot at the same time in Django REST Framework and PostgreSQL, while allowing cancelled slots to be booked again?


### 3. Give one example where AI output was wrong or incomplete. How did you catch it?

An AI-generated test treated **4:30 PM** as outside working hours for a doctor finishing at **5:00 PM**. But a 30-minute appointment starting at 4:30 PM ends exactly at 5:00 PM, so it is valid. The test expectation was corrected after checking it against the slot rules.


### 4. Name two decisions you made without AI. Why did you trust your own judgment?

**Technology stack:** I chose Django REST Framework and React with Vite because I have worked with Python APIs and React before. I could focus on the booking logic instead of learning a new stack.

**Deployment simplicity:** After reviewing the requirements and considering the available options, I made the final decision to remove Docker. Render supports native Python deployment, so containers would add unnecessary setup for this project.

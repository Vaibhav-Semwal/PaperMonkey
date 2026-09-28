# Paper Maker Portal

- **Frontend:** React (Vite)
- **Auth:** Firebase Authentication (email/password) — login, logout, change password
- **Backend:** FastAPI — the frontend talks only to FastAPI
- **Data/roles:** Django — owns the database (via Django ORM) and the Django Admin UI
  for managing which users are "teacher" vs "student".

```
project/
  backend/             Django project: DB models + admin UI (role management) + FastAPI app the React frontend calls
  frontend/            React app (Vite)
```

## How auth works

1. React signs the user up / logs them in directly against **Firebase**
   (`firebase/auth` JS SDK). Firebase handles password storage, login, logout,
   and password changes — no passwords ever touch our backend.
2. On sign-up, React calls `POST /api/register` on FastAPI with the chosen
   role ("teacher" or "student") and the user's Firebase ID token.
3. FastAPI verifies the ID token with the **Firebase Admin SDK**, then creates
   a `Profile` row (Django model) mapping `firebase_uid -> role`.
4. On every future request, React attaches `Authorization: Bearer <idToken>`.
   FastAPI verifies it, looks up the Django `Profile`, and returns
   role-specific dashboard data.
5. An admin can also open Django Admin (`/admin`) and change a user's role
   there directly.

## 1. Set up Firebase

1. Go to the [Firebase Console](https://console.firebase.google.com/), create a project.
2. **Build > Authentication > Get Started > Sign-in method** → enable **Email/Password**.
3. **Project settings > General > Your apps** → add a Web app → copy the config
   into `frontend/.env` (copy from `frontend/.env.example`).
4. **Project settings > Service accounts** → "Generate new private key" → save
   the JSON as `backend-fastapi/serviceAccountKey.json` (this file is
   git-ignored; never commit it).

## 2. Run the Program

overall setup
```bash
python backend-django/manage.py makemigrations
python backend-django/manage.py migrate
python backend-django/manage.py createsuperuser   # for logging into /admin
docker compose -up
```

FastAPI docs / try-it-out UI: http://localhost:8000/docs

## 3. Try it out

1. Open http://localhost:5173 → you're redirected to `/login`.
2. Click "Sign up", pick role Teacher or Student, submit.
3. You land on `/teacher` or `/student` showing a role-specific "Hello World" dashboard.
4. Use "Change Password" to update your password (re-authenticates with your current password first).
5. Use "Log Out" to sign out via Firebase.
6. To change someone's role after the fact, log into Django Admin
   (http://localhost:8001/admin) and edit their `Profile.role`.

## Notes / next steps for production

- Set `DEBUG=False` and a real `DJANGO_SECRET_KEY` in `backend-django`.
- Swap SQLite for Postgres in `backend-django/core/settings.py` for production.
- Lock down CORS `allow_origins` in `backend-fastapi/main.py` to your real domain.
- Consider adding Firebase custom claims for role instead of (or alongside) the
  Django table if you want the role embedded directly in the ID token.

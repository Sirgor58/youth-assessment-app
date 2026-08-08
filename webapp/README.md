# CYDC-GH0954 Youth Assessment Web App

Mobile-friendly Flask web app based on the existing Youth Assessment System. It includes the 227 imported participants, assessment questions, scoring, periods, participant history, results, and admin edit/delete controls.

## Run on your laptop

Open PowerShell in this `webapp` folder:

```powershell
py -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
py app.py
```

Then open `http://127.0.0.1:5000`.

Default temporary accounts:
- Teacher / `teacher123`
- Admin / `admin123`

Change these before real use by setting `TEACHER_PASSWORD`, `ADMIN_PASSWORD`, and `SECRET_KEY` in the hosting environment.

## Hosting

PythonAnywhere supports Flask web apps and a free account currently provides one web app, one web worker, and 512 MB storage; the free account has a one-month expiry. See the official setup guide before deployment. The SQLite database is included for this initial deployment.

For a longer-term multi-user system, move the database to PostgreSQL/MySQL rather than relying on a single SQLite file.

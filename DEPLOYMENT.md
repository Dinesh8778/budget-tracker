# Django Budget Tracker Deployment Guide

This project has been configured for easy and robust production deployment. It relies on environment variables, serves static files via **WhiteNoise**, handles database configuration dynamically via **dj-database-url**, and includes containerization via **Docker**.

Below are the step-by-step guides for three typical environments:
1. **PythonAnywhere** (Recommended for SQLite users)
2. **Render or Railway** (Recommended for PostgreSQL PaaS deployment)
3. **Docker/VPS** (Recommended for self-hosting)

---

## 🛠️ Step 0: Environment Configuration (.env)

No matter where you deploy, the project now relies on environment variables. In local development or VPS environments, create a `.env` file in the project root:

```env
DEBUG=False
SECRET_KEY=your-highly-secret-production-random-key
ALLOWED_HOSTS=yourdomain.com,localhost,127.0.0.1
# DATABASE_URL = sqlite:///db.sqlite3  (Optional, defaults to SQLite)
```

---

## 🐍 Option A: PythonAnywhere (Easiest, retains SQLite)

PythonAnywhere is the best choice if you want to keep the application lightweight, free, and continue using the SQLite database (`db.sqlite3`).

### 1. Upload Your Files
1. Sign up for a free or beginner account on [PythonAnywhere](https://www.pythonanywhere.com/).
2. Push your project to a GitHub repository and clone it in a PythonAnywhere Bash Console:
   ```bash
   git clone https://github.com/your-username/budget-tracker.git
   ```

### 2. Configure Virtual Environment & Packages
Create a virtualenv and install the packages:
```bash
mkvirtualenv --python=/usr/bin/python3.10 budget-tracker-env
pip install -r requirements.txt
```

### 3. Create database and static files
Run standard migrations and collect static files:
```bash
python manage.py migrate
python manage.py collectstatic --noinput
```

### 4. Setup PythonAnywhere Web API
1. Navigate to the **Web** tab in PythonAnywhere.
2. Click **Add a new web app**.
3. Choose **Manual Configuration** -> select **Python 3.10**.
4. Set the **Virtualenv** path to: `/home/your-username/.virtualenvs/budget-tracker-env`
5. Under **Code**, check the path directory points to: `/home/your-username/budget-tracker`
6. Edit the **WSGI configuration file** (there is a link to configure it). Replace its contents with:
   ```python
   import os
   import sys

   # Add your project path to sys.path
   path = '/home/your-username/budget-tracker'
   if path not in sys.path:
       sys.path.append(path)

   # Set environment variables for django-environ
   os.environ['DEBUG'] = 'False'
   os.environ['SECRET_KEY'] = 'your-secure-secret-key-here'
   os.environ['ALLOWED_HOSTS'] = 'your-username.pythonanywhere.com'

   from django.core.wsgi import get_wsgi_application
   application = get_wsgi_application()
   ```
7. Click **Reload** to start your site.

### 5. Setup recurring EMI payments (Cron Job)
Because `django-crontab` relies on local system cron daemons that are not accessible on PythonAnywhere, configure it using the **Tasks** dashboard:
1. Go to the **Tasks** tab.
2. Under **Scheduled Tasks**, set the time (e.g. `00:00`).
3. Enter the daily execution command:
   ```bash
   workon budget-tracker-env && python /home/your-username/budget-tracker/manage.py process_emi_payments
   ```

---

## ☁️ Option B: Render or Railway (PaaS with PostgreSQL)

*Note: Because Render dynos are ephemeral, SQLite files get deleted on rebuild. Using PostgreSQL ensures permanent database persistence.*

### 1. Database Setup
1. Go to [Render Dashboard](https://dashboard.render.com/) and click **New** -> **PostgreSQL**.
2. Give it a name and copy the **Internal Database URL** or **External Database URL**.

### 2. Configure Web Service
1. Click **New** -> **Web Service** and connect your GitHub repository.
2. Configure settings:
   - **Environment**: `Python`
   - **Build Command**: `pip install -r requirements.txt && python manage.py collectstatic --noinput`
   - **Start Command**: `gunicorn your_project.wsgi:application` (Render will also automatically read the **Procfile** we created).
3. Under **Advanced / Environment Variables**, add:
   - `DATABASE_URL`: *Your PostgreSQL Database Connection URL*
   - `DEBUG`: `False`
   - `SECRET_KEY`: *Any random secure string*
   - `ALLOWED_HOSTS`: `*` (or your Render URL, e.g. `budget-tracker.onrender.com`)
4. Click **Deploy**.

### 3. Run Initial Migrations
In the Web Service shell or via Render's dashboard console:
```bash
python manage.py migrate
```

### 4. Setup recurring EMI payments (Cron Job)
1. Go to **New** -> **Cron Job**.
2. Set the schedule input to: `0 0 * * *` (Daily at Midnight).
3. Set the start command to:
   ```bash
   python manage.py process_emi_payments
   ```

---

## 🐳 Option C: Docker or VPS (Self-Hosting)

You can spin up the app on any VPS (AWS, DigitalOcean, Hetzner, etc.) using Docker.

### 1. Run via Docker Compose
All necessary configuration files (`Dockerfile` and `docker-compose.yml`) are included in the repository.
1. Spin up the setup in detached background mode:
   ```bash
   docker-compose up --build -d
   ```
2. Run database migrations:
   ```bash
   docker-compose exec web python manage.py migrate
   ```
3. The app is now live at `http://localhost:8000`.

### 2. Setup Cron for EMI Payments on VPS
To process EMI payments on the Docker host, register a host crontab task:
1. Open host crontab:
   ```bash
   crontab -e
   ```
2. Append the target cron line:
   ```cron
   0 0 * * * docker exec -t budget-tracker-web-1 python manage.py process_emi_payments >> /var/log/emi_cron.log 2>&1
   ```

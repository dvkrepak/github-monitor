
<img align="right" src="https://i.imgur.com/EkmzUIf.png" alt="GitHub Logo" width="400" height="200">

## **GitHub Activity Monitor**

A Django-based service that tracks GitHub repository activity using the GitHub Events API.

---

### 🧩 Overview

- Monitors up to **5 repositories**.
- Collects **GitHub events** via API and stores them in PostgreSQL.
- Computes **average time between events**, grouped by `(repository, event_type)`.
- Applies rolling window: **last 7 days** or **up to 500 events** per group.
- Exposes analytics via **REST API** with auto-generated **Swagger docs**.
- Persists data across restarts; minimizes API calls.

---

### ⚙️ Technologies

- **Python 3.12**, **Django 5**
- **Django REST Framework**
- **PostgreSQL**
- **Docker & Docker Compose**
- **drf-spectacular** (OpenAPI/Swagger schema)
- **NumPy**

---

### 🚀 Running Locally (via Docker)

> Requires `docker` and `docker compose`

1. **Clone and enter the project:**
   ```bash
   git clone git@github.com:dvkrepak/github-monitor.git
   cd github-monitor
   ```

2. **Create `.env` file:**
   ```bash
   cp .env.example .env
   ```

   Set your GitHub token:
   ```
   GITHUB_TOKEN=ghp_XXXXXXXXXXXXXXXX
   ```

3. **Build and launch the app:**
   ```bash
   docker compose up --build
   ```

4. **[Optional] Load test data:**
   ```bash
   docker compose exec web python manage.py load_test_data
   ```

   > Adds repositories (active/inactive), event types, and realistic event samples.

5. **[Optional] Create a superuser for admin:**
   ```bash
   docker compose exec web python manage.py createsuperuser
   ```

6. **[Optional] Fetch live GitHub data:**
   ```bash
   docker compose exec web python manage.py fetch_github_events
   ```

   > For each active repository, fetches up to **500 events** or all events from the **last 7 days**, whichever is less.

---

### 📌 API Endpoints

> Interactive docs available at:  
> **http://localhost:8000/api/docs/swagger/**

| Endpoint                            | Method | Description                                    |
|-------------------------------------|--------|------------------------------------------------|
| `/api/stats/`                       | GET    | Stats for all active repositories              |
| `/api/stats/<slug>/`               | GET    | Stats for a specific repository                |
| `/api/schema/`                      | GET    | Raw OpenAPI schema                             |
| `/api/docs/swagger/`               | GET    | Swagger UI with full schema                    |

**Query Parameters**:
- `days`: Number of days to include (default: 7)
- `limit`: Max number of events per group (default: 500)

---

### 🛠 Example Use Cases

- Compare how frequently different types of events occur across repositories.
- Detect changes in development activity over time.
- Integrate event stats into dashboards or alerts.

---

### ⏱ Time Spent

- App implementation (core logic): **~2h 15m**
- Dockerization, testing, docs: **~1h**
- **Total: ~3h 20m**

---

### 📎 Notes

- GitHub token is required to avoid hitting the API rate limit.
- `slug` field in `Repository` model is used in URLs.
- The system avoids re-fetching known events to minimize GitHub traffic.
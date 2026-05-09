## Setup Instructions

### Environment Setup
```bash
git clone https://github.com/Anmol012/financial-document-analyzer
cd financial-document-analyzer
```

Install:

* Python 3.11.x
* Node.js 18+
* MongoDB
* Redis
* (Optional) Docker

---

### Backend Setup

```bash
cd Backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Create `.env` file inside `Backend/`:

```env
MONGODB_URI=mongodb://localhost:27017/financial_analyzer
REDIS_URL=redis://localhost:6379/0
JWT_SECRET_KEY=your-secret-key-change-this
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
DEFAULT_LLM_PROVIDER=openai
OPENAI_API_KEY=your-openai-api-key
```

Start MongoDB and Redis:

```bash
mongod
redis-server
```

Run Celery worker:

```bash
cd Backend
source venv/bin/activate
celery -A celery_app worker --loglevel=info
```

Start backend server:

```bash
python run.py
```

Backend runs at `http://localhost:5000`

---

### Frontend Setup

```bash
cd frontend
npm install
```

Create `.env` inside `frontend/`:

```env
VITE_BASE_URL=http://localhost:5000/api
VITE_TEST_DATA=false
```

Run frontend:

```bash
npm run dev
```

Frontend runs at `http://localhost:5173`

---

## Running the Application

Ensure all services are running:

* MongoDB and Redis
* Backend (`python run.py`) — port 5000
* Celery worker (`celery -A celery_app worker`)
* Frontend (`npm run dev`) — port 5173

Access the app at `http://localhost:5173`

Optional Docker setup (starts MongoDB, Redis, backend, and Celery in one command):

```bash
cd Backend
docker-compose up -d
```

---

## API Endpoints

| Method | Endpoint                        | Description                        | Authentication |
| ------ | ------------------------------- | ---------------------------------- | -------------- |
| POST   | /api/auth/register              | Register a new user                | None           |
| POST   | /api/auth/login                 | Authenticate user and get JWT      | None           |
| POST   | /api/auth/logout                | Invalidate session (token blocklist) | JWT          |
| POST   | /api/auth/refresh               | Get new access token               | Refresh JWT    |
| GET    | /api/auth/me                    | Get current user profile           | JWT            |
| POST   | /api/documents/upload           | Upload a financial document        | JWT            |
| GET    | /api/documents                  | List user's documents              | JWT            |
| GET    | /api/documents/:id              | Get document details               | JWT            |
| GET    | /api/documents/:id/status       | Get analysis status (poll this)    | JWT            |
| POST   | /api/documents/:id/analyze      | Trigger AI analysis                | JWT            |
| GET    | /api/documents/:id/result       | Fetch completed analysis results   | JWT            |
| DELETE | /api/documents/:id              | Delete a document                  | JWT            |
| GET    | /api/documents/:id/download     | Download original PDF              | JWT            |
| GET    | /api/analysis/history           | Get analysis history               | JWT            |
| GET    | /api/analysis/:id/export        | Export analysis as PDF or CSV      | JWT            |
| DELETE | /api/analysis/:id               | Delete an analysis                 | JWT            |

---

## Frontend Features

* Login, registration, and logout with JWT-based authentication (access + refresh tokens)
* PDF upload with progress indicator
* Document table with search, status polling, analyze, view result, and delete
* Analysis dashboard with financial summary, risk score, market insights, recommendations
* Revenue trend (line chart) and profit margin (bar chart) visualizations
* Export results to PDF or CSV
* Analysis history view
* Dark mode and responsive UI
* Toast-based notifications

---

## Technologies Used

### Backend

* FastAPI + Uvicorn
* MongoDB (via pymongo)
* Redis (JWT blocklist + Celery broker)
* Celery (async task queue)
* CrewAI (multi-agent AI analysis)
* PyPDF2 + pytesseract (PDF text extraction + OCR)
* python-jose (JWT)
* slowapi (rate limiting)
* ReportLab + pandas (PDF/CSV export)
* bcrypt

### Frontend

* React
* Vite
* TailwindCSS
* shadcn/ui
* Recharts
* Axios
* React Router

---

## Debugging and Development

### Backend

* Use `python run.py` for local development (port 5000)
* Use `uvicorn run:app --reload --port 5000` for live reload
* API docs (Swagger UI) available at `http://localhost:5000/docs`
* Monitor Celery tasks with Flower:

  ```bash
  pip install flower
  celery -A celery_app flower
  ```

### Frontend

* Use React Developer Tools browser extension
* Hot reload is enabled by default (`npm run dev`)
* Inspect API calls via browser DevTools Network tab
* Set `VITE_TEST_DATA=true` in `frontend/.env` to use mock data without a backend

### Common Issues

* **CORS Errors**: `CORS_ORIGINS=*` is the default. For production, set `CORS_ORIGINS=http://your-frontend-domain.com`
* **Upload Errors**: Check file size (<100MB) and format (PDF only)
* **Auth Failures**: Verify `JWT_SECRET_KEY` in `.env` matches between restarts
* **Analysis Errors**: Check Celery worker is running and LLM API key is set
* **MongoDB Auth**: If using Docker, default credentials are `admin/admin123`. For local mongod without auth, set `MONGODB_URI=mongodb://localhost:27017/financial_analyzer`

---

## Testing

### Backend

```bash
pip install pytest pytest-asyncio httpx
pytest
```

### Frontend

```bash
npm install vitest @testing-library/react --save-dev
npm run test
```

### Manual Testing

* Register a new account, then log in
* Upload a sample PDF
* Click Analyze and watch status update automatically
* View results in the Analysis Dashboard
* Export as PDF and CSV
* Check Analysis History

---

## Deployment

### Backend

```bash
cd Backend
docker-compose up -d
```

Deploy to AWS EC2, Render, or Railway.
Use Nginx or Traefik as a reverse proxy in front of Gunicorn.

### Frontend

```bash
cd frontend
npm run build
```

Deploy the `dist/` folder to Vercel, Netlify, or serve via Nginx.

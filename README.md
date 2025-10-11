## Setup Instructions

### Environment Setup
```bash
git clone https://github.com/Anmol012/financial-document-analyzer
cd financial-document-analyzer
````

Install:

* Python 3.11.x
* Node.js 18+
* MongoDB
* Redis
* (Optional) Docker

---

### Backend Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Create `.env` file:

```env
MONGODB_URI=mongodb://localhost:27017/financial_analyzer
REDIS_URL=redis://localhost:6379/0
SECRET_KEY=your-secret-key
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

Start MongoDB and Redis:

```bash
mongod
redis-server
```

Run Celery worker:

```bash
cd backend
source venv/bin/activate
celery -A celery_app worker --loglevel=info
```

Start backend server:

```bash
python run.py
```

Backend runs at `http://localhost:8000`

---

### Frontend Setup

```bash
cd frontend
npm install
```

Initialize shadcn/ui:

```bash
npx shadcn-ui@latest init
npx shadcn-ui@latest add button input card table progress label dialog toast
```

Create `.env`:

```env
VITE_BASE_URL=http://localhost:8000
```

Update `src/config.js`:

```javascript
export const BASE_URL = import.meta.env.VITE_BASE_URL || 'http://localhost:8000';
export const TEST_DATA = false;
```

Run frontend:

```bash
npm run dev
```

Frontend runs at `http://localhost:5173`

---

## Running the Application

Ensure services are running:

* MongoDB and Redis
* Backend (`python run.py`)
* Celery worker
* Frontend (`npm run dev`)

Access the app at `http://localhost:5173`

Optional Docker setup:

```bash
cd backend
docker-compose up -d
```

---

## API Endpoints

| Method | Endpoint                   | Description                   | Authentication |
| ------ | -------------------------- | ----------------------------- | -------------- |
| POST   | /api/auth/register         | Register a new user           | None           |
| POST   | /api/auth/login            | Authenticate user and get JWT | None           |
| POST   | /api/auth/logout           | Invalidate session            | JWT            |
| POST   | /api/documents/upload      | Upload a financial document   | JWT            |
| GET    | /api/documents             | List user's documents         | JWT            |
| POST   | /api/documents/:id/analyze | Trigger AI analysis           | JWT            |
| GET    | /api/documents/:id/result  | Fetch analysis results        | JWT            |
| DELETE | /api/documents/:id         | Delete a document             | JWT (Admin)    |
| GET    | /api/analysis/history      | Get analysis history          | JWT            |
| GET    | /api/analysis/:id/export   | Export analysis as PDF/CSV    | JWT            |

---

## Frontend Features

* Login and registration with JWT-based authentication
* PDF upload with real-time progress
* Document table with search, analyze, view, delete
* Analysis dashboard with financial summary and risk insights
* History view with filters
* Export results to PDF or CSV
* Dark mode and responsive UI
* Toast-based notifications

---

## Technologies Used

### Backend

* FastAPI
* MongoDB
* Redis
* Celery
* CrewAI
* PyPDF2
* python-jose
* passlib

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

* Use `uvicorn app.main:app --reload` for live reload
* Use `pdb` or `ipdb` for debugging
* Monitor Celery with Flower:

  ```bash
  pip install flower
  celery -A celery_app flower
  ```
* Enable LLM observability for AI calls

### Frontend

* Use React Developer Tools
* Enable hot reload (`npm run dev`)
* Inspect API calls via browser DevTools

### Common Issues

* **CORS Errors**: Allow `http://localhost:5173` in FastAPI CORS settings
* **Upload Errors**: Check file size (<100MB) and format (PDF)
* **Auth Failures**: Verify JWT secret and expiry
* **Analysis Errors**: Check CrewAI and Celery worker status

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

### Manual

* Upload sample PDFs
* Test concurrent uploads and analysis
* Verify role-based access

---

## Deployment

### Backend

```bash
cd backend
docker-compose up -d
```

Deploy to AWS EC2, Render, or Heroku.
Use Nginx or Traefik as reverse proxy.

### Frontend

```bash
cd frontend
npm run build
```

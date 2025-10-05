# Financial Document Analyzer - Backend System

A comprehensive backend system for AI-powered financial document analysis using CrewAI, Flask, Celery, Redis, and MongoDB.

## Features

- **Multi-LLM Support**: OpenAI, Groq, and Ollama (Mistral 7B)
- **AI-Powered Analysis**: CrewAI-based financial document analysis
- **Async Processing**: Celery with Redis for background tasks
- **Document Management**: Upload, analyze, and export financial documents
- **User Authentication**: JWT-based authentication with role-based access control
- **Export Functionality**: Generate PDF and CSV reports
- **Docker Support**: Complete Docker Compose setup for easy deployment

## Tech Stack

- **Framework**: Flask 3.0
- **Database**: MongoDB 7.0
- **Cache/Queue**: Redis 7
- **Task Queue**: Celery 5.3
- **AI Framework**: CrewAI with LangChain
- **LLM Providers**: OpenAI, Groq, Ollama
- **PDF Processing**: PyPDF2, pdf2image, pytesseract
- **Containerization**: Docker & Docker Compose

## Project Structure

```
financial-document-analyzer/
├── app/
│   ├── __init__.py
│   ├── extensions.py
│   ├── models.py
│   ├── routes/
│   │   ├── auth.py
│   │   ├── documents.py
│   │   └── analysis.py
│   ├── services/
│   │   ├── llm_providers.py
│   │   ├── pdf_processor.py
│   │   └── crewai_analyzer.py
│   ├── tasks/
│   │   └── analysis_tasks.py
│   └── utils/
│       └── export_utils.py
├── config.py
├── run.py
├── celery_app.py
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── .env.example
└── README.md
```

## Quick Start

### Prerequisites

- Docker & Docker Compose
- API keys for LLM providers (optional, based on which provider you want to use)

### Installation

1. **Clone the repository**
```bash
git clone <repository-url>
cd financial-document-analyzer
```

2. **Create environment file**
```bash
cp .env.example .env
```

3. **Configure environment variables**
Edit `.env` file and add your API keys:
```env
# Choose your preferred LLM provider
DEFAULT_LLM_PROVIDER=openai  # or groq, ollama

# Add API keys for your chosen provider(s)
OPENAI_API_KEY=your-openai-key
GROQ_API_KEY=your-groq-key

# JWT Secret (change this!)
JWT_SECRET_KEY=your-super-secret-key
```

4. **Start the services**
```bash
docker-compose up -d
```

5. **Pull Ollama model (if using Ollama)**
```bash
docker exec -it financial_analyzer_ollama ollama pull mistral:7b
```

6. **Check services status**
```bash
docker-compose ps
```

The API will be available at: `http://localhost:5000`

## API Endpoints

### Authentication
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login user
- `POST /api/auth/logout` - Logout user
- `GET /api/auth/me` - Get current user info

### Documents
- `POST /api/documents/upload` - Upload document
- `GET /api/documents` - Get all documents
- `GET /api/documents/:id` - Get document details
- `POST /api/documents/:id/analyze` - Trigger analysis
- `GET /api/documents/:id/result` - Get analysis result
- `GET /api/documents/:id/download` - Download document
- `DELETE /api/documents/:id` - Delete document

### Analysis
- `GET /api/analysis/history` - Get analysis history
- `GET /api/analysis/:id` - Get specific analysis
- `GET /api/analysis/:id/export?format=pdf` - Export analysis (pdf/csv)
- `DELETE /api/analysis/:id` - Delete analysis

## LLM Provider Configuration

### OpenAI
```env
DEFAULT_LLM_PROVIDER=openai
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4-turbo-preview
```

### Groq
```env
DEFAULT_LLM_PROVIDER=groq
GROQ_API_KEY=gsk_...
GROQ_MODEL=mixtral-8x7b-32768
```

### Ollama (Local)
```env
DEFAULT_LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://ollama:11434
OLLAMA_MODEL=mistral:7b
```

## Usage Example

### 1. Register a User
```bash
curl -X POST http://localhost:5000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com",
    "password": "securepassword"
  }'
```

### 2. Login
```bash
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "securepassword"
  }'
```

### 3. Upload Document
```bash
curl -X POST http://localhost:5000/api/documents/upload \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -F "file=@/path/to/document.pdf" \
  -F "name=Financial Report Q4"
```

### 4. Analyze Document
```bash
curl -X POST http://localhost:5000/api/documents/DOC_ID/analyze \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "options": {
      "llm_provider": "openai",
      "focusAreas": ["financials", "risks"]
    }
  }'
```

### 5. Get Analysis Result
```bash
curl -X GET http://localhost:5000/api/documents/DOC_ID/result \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

## Development

### Running Locally (without Docker)

1. **Install dependencies**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

2. **Start MongoDB and Redis**
```bash
# MongoDB
mongod --port 27017

# Redis
redis-server
```

3. **Start Celery Worker**
```bash
celery -A celery_app worker --loglevel=info
```

4. **Start Flask App**
```bash
python run.py
```

### Monitoring

**View Celery logs**
```bash
docker-compose logs -f celery_worker
```

**View Flask logs**
```bash
docker-compose logs -f backend
```

**Access MongoDB**
```bash
docker exec -it financial_analyzer_mongodb mongosh -u admin -p admin123
```

**Access Redis CLI**
```bash
docker exec -it financial_analyzer_redis redis-cli
```

## Troubleshooting

### Ollama Model Not Found
```bash
docker exec -it financial_analyzer_ollama ollama pull mistral:7b
```

### Permission Denied on Uploads
```bash
chmod -R 777 uploads logs
```

### MongoDB Connection Issues
Ensure MongoDB is running and credentials match in `.env`:
```bash
docker-compose restart mongodb backend
```

### Celery Tasks Not Running
Check if Celery worker is running:
```bash
docker-compose ps celery_worker
docker-compose logs celery_worker
```

## Security Considerations

- Change `JWT_SECRET_KEY` in production
- Use strong passwords for MongoDB
- Enable HTTPS in production
- Implement rate limiting
- Validate and sanitize all inputs
- Use environment-specific configurations

## Performance Tuning

- Adjust Celery concurrency: `--concurrency=N`
- Configure Redis maxmemory
- Enable MongoDB indexes
- Use Gunicorn workers in production
- Implement caching strategies

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

MIT License - See LICENSE file for details

## Support

For issues and questions, please open an issue on GitHub.

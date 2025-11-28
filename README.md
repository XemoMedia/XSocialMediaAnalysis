# XSocialMedialAnalysis

A Python FastAPI application for social media analysis with sentiment analysis capabilities.

## Project Structure

This project follows a layered architecture similar to Spring Boot:

```
XSocialMedialAnalysis/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application entry point
│   ├── config.py            # Configuration settings
│   ├── database.py          # Database connection and session
│   ├── models/              # SQLAlchemy models (entities)
│   │   ├── __init__.py
│   │   └── comment_model.py
│   ├── schemas/             # Pydantic schemas (DTOs)
│   │   ├── __init__.py
│   │   └── sentiment_schemas.py
│   ├── repositories/        # Database access layer
│   │   ├── __init__.py
│   │   └── comment_repository.py
│   ├── services/           # Business logic layer
│   │   ├── __init__.py
│   │   ├── sentiment_service.py
│   │   └── comment_service.py
│   └── routes/             # API endpoints (controllers)
│       ├── __init__.py
│       └── sentiment_routes.py
├── requirements.txt
└── README.md
```

## Architecture Layers

### 1. **Models** (Entities)
- SQLAlchemy models representing database tables
- Similar to JPA entities in Spring Boot

### 2. **Repositories** (Data Access Layer)
- Handle all database operations
- Similar to Spring Data repositories

### 3. **Services** (Business Logic Layer)
- Contains business logic
- Coordinates between repositories and other services
- Similar to @Service in Spring Boot

### 4. **Routes** (Controllers)
- Define API endpoints
- Handle HTTP requests/responses
- Similar to @RestController in Spring Boot

### 5. **Schemas** (DTOs)
- Pydantic models for request/response validation
- Similar to DTOs in Spring Boot

## Setup Instructions

### 1. Install Dependencies

**Using `uv` (Recommended - Automatically creates virtual environment):**

```bash
# This will create .venv and install all dependencies from pyproject.toml
uv sync
```

> **Note**: `uv sync` uses `pyproject.toml` for dependencies. The project includes both `pyproject.toml` and `requirements.txt` for flexibility.

**Using pip (Alternative):**

```bash
# Create virtual environment manually
python -m venv .venv

# Activate virtual environment
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # macOS/Linux

# Install dependencies
pip install -r requirements.txt
```

> **Note**: See `UV_SETUP_GUIDE.md` for detailed `uv` instructions.

### 2. Configure Database

Create a `.env` file in the project root:

```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=postgres
DB_USER=postgres
DB_PASSWORD=root
DEBUG=False
```

Or update `app/config.py` with your database credentials.

### 2.1. Create Database Tables

**Important:** You need to create the `sentiment_analysis` table before using the API:

```bash
# Using psql
psql -U postgres -d postgres -f create_sentiment_analysis_table.sql
```

Or see `DATABASE_SETUP.md` for detailed instructions.

### 3. Run the Application

**Using `uv` (Recommended):**

```bash
uv run python run.py
```

**Or using uvicorn directly:**

```bash
# With uv
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Or activate venv first, then run
.venv\Scripts\activate  # Windows
python run.py
```

The API will be available at:
- API: http://localhost:8000
- Swagger UI: http://localhost:8000/swagger
- ReDoc: http://localhost:8000/redoc

## API Endpoints

### POST `/api/v1/sentiment/analyze`

Analyze sentiment for comments by their IDs.

**Request Body:**
```json
{
  "ids": ["comment_id_1", "comment_id_2", "comment_id_3"]
}
```

**Response:**
```json
{
  "results": [
    {
      "id": "comment_id_1",
      "text": "This is amazing!",
      "sentiment": "positive",
      "polarity": 0.75,
      "emotion": "joy"
    }
  ],
  "total_analyzed": 1,
  "total_requested": 1
}
```

### GET `/health`

Health check endpoint.

### GET `/`

Root endpoint with API information.

## Example cURL Request

```bash
curl -X POST "http://localhost:8000/api/v1/sentiment/analyze" \
  -H "Content-Type: application/json" \
  -d '{
    "ids": ["comment_id_1", "comment_id_2"]
  }'
```

## Key Differences from Spring Boot

1. **Dependency Injection**: FastAPI uses function parameters with `Depends()` instead of `@Autowired`
2. **Async Support**: FastAPI supports async/await natively
3. **Validation**: Pydantic handles validation automatically (similar to Bean Validation)
4. **Documentation**: Swagger/OpenAPI is automatically generated

## Notes

- The project uses TextBlob for sentiment analysis (similar to Stanford CoreNLP in Java)
- Database models should match your PostgreSQL schema
- All layers follow separation of concerns principle
- Logging is configured for debugging


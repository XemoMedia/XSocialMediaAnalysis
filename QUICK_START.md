# Quick Start Guide

## 1. Install Dependencies

```bash
# Navigate to project directory
cd XSocialMedialAnalysis

# Using uv (Recommended - automatically creates virtual environment)
# This uses pyproject.toml for dependencies
uv sync

# Or using pip (Alternative)
python -m venv .venv
.venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

## 2. Configure Database

Update `app/config.py` with your PostgreSQL credentials, or create a `.env` file:

```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=postgres
DB_USER=postgres
DB_PASSWORD=root
```

## 3. Run the Application

```bash
# Option 1: Using uv (Recommended - automatically uses virtual environment)
uv run python run.py

# Option 2: Using uvicorn directly with uv
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Option 3: Activate venv manually, then run
.venv\Scripts\activate  # Windows
python run.py
```

## 4. Test the API

### Using cURL:

```bash
curl -X POST "http://localhost:8000/api/v1/sentiment/analyze" \
  -H "Content-Type: application/json" \
  -d '{
    "ids": ["comment_id_1", "comment_id_2"]
  }'
```

### Using Swagger UI:

1. Open browser: http://localhost:8000/swagger
2. Find the `/api/v1/sentiment/analyze` endpoint
3. Click "Try it out"
4. Enter your comment IDs in the request body
5. Click "Execute"

## Project Structure Explained

```
app/
├── main.py              # FastAPI app (like @SpringBootApplication)
├── config.py            # Configuration (like application.properties)
├── database.py          # DB connection (like DataSource)
├── models/              # Entities (like JPA @Entity)
├── repositories/        # Data access (like @Repository)
├── services/            # Business logic (like @Service)
├── routes/              # Controllers (like @RestController)
└── schemas/             # DTOs (like DTOs in Spring Boot)
```

## Key Concepts for Spring Boot Developers

1. **Dependency Injection**: FastAPI uses `Depends()` instead of `@Autowired`
2. **Controllers**: Use `@router.post()` instead of `@PostMapping()`
3. **Services**: Regular Python classes (no annotations needed)
4. **Repositories**: Regular Python classes with database session
5. **Validation**: Pydantic schemas handle validation automatically

## Example Request/Response

**Request:**
```json
{
  "ids": ["comment_123", "comment_456"]
}
```

**Response:**
```json
{
  "results": [
    {
      "id": "comment_123",
      "text": "This is amazing!",
      "sentiment": "positive",
      "polarity": 0.75,
      "emotion": "joy"
    },
    {
      "id": "comment_456",
      "text": "I don't like this",
      "sentiment": "negative",
      "polarity": -0.5,
      "emotion": "sadness"
    }
  ],
  "total_analyzed": 2,
  "total_requested": 2
}
```


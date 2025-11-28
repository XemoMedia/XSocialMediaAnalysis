# Running XSocialMedialAnalysis with UV

This guide shows you how to set up and run the project using `uv`, which automatically manages virtual environments.

## Prerequisites

1. **Install `uv`** (if not already installed):
   ```bash
   # On Windows (PowerShell)
   powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
   
   # On macOS/Linux
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

2. **Verify installation**:
   ```bash
   uv --version
   ```

## Step-by-Step Setup

### Step 1: Navigate to Project Directory

```bash
cd D:\Xmedia\XSocialMedialAnalysis
```

### Step 2: Create Virtual Environment and Install Dependencies

`uv` will automatically create a virtual environment and install all dependencies:

```bash
uv sync
```

This command:
- Creates a virtual environment (if it doesn't exist)
- Installs all dependencies from `pyproject.toml`
- Creates a `uv.lock` file for reproducible builds

> **Note**: The project uses `pyproject.toml` for dependency management. If you prefer using `requirements.txt`, you can use:
> ```bash
> uv pip install -r requirements.txt
> ```

**Alternative**: If you want to use a specific Python version:

```bash
uv sync --python 3.11
```

### Step 3: Configure Database

Update `app/config.py` with your PostgreSQL credentials:

```python
db_host: str = "localhost"
db_port: int = 5432
db_name: str = "postgres"
db_user: str = "postgres"
db_password: str = "root"  # Change to your password
```

Or create a `.env` file in the project root:

```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=postgres
DB_USER=postgres
DB_PASSWORD=root
```

### Step 4: Run the Application

Using `uv run` (recommended - automatically uses the virtual environment):

```bash
uv run python run.py
```

Or using uvicorn directly:

```bash
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Or activate the virtual environment manually:

```bash
# Activate virtual environment (created by uv)
.venv\Scripts\activate  # Windows
# or
source .venv/bin/activate  # macOS/Linux

# Then run
python run.py
```

### Step 5: Verify the Application is Running

1. **Check the console output** - You should see:
   ```
   INFO:     Uvicorn running on http://0.0.0.0:8000
   ```

2. **Test the root endpoint**:
   ```bash
   curl http://localhost:8000/
   ```

3. **Open Swagger UI**:
   - Open browser: http://localhost:8000/swagger

## Common UV Commands

### Install New Dependencies

```bash
# Add a new package
uv add package-name

# Add a development dependency
uv add --dev package-name

# Install from requirements.txt
uv pip install -r requirements.txt
```

### Update Dependencies

```bash
# Update all dependencies
uv sync --upgrade

# Update a specific package
uv pip install --upgrade package-name
```

### Run Python Scripts

```bash
# Run any Python script with uv
uv run python script.py

# Run with specific Python version
uv run --python 3.11 python script.py
```

### Check Virtual Environment

```bash
# Show virtual environment location
uv venv

# Show installed packages
uv pip list
```

## Project Structure After UV Setup

After running `uv sync`, your project will have:

```
XSocialMedialAnalysis/
├── .venv/              # Virtual environment (created by uv)
├── uv.lock            # Lock file for reproducible builds
├── app/
├── requirements.txt
└── ...
```

## Testing the API

### Using cURL:

```bash
curl -X POST "http://localhost:8000/api/v1/sentiment/analyze" \
  -H "Content-Type: application/json" \
  -d "{\"ids\": [\"comment_id_1\", \"comment_id_2\"]}"
```

### Using PowerShell (Windows):

```powershell
$body = @{
    ids = @("comment_id_1", "comment_id_2")
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/api/v1/sentiment/analyze" `
    -Method POST `
    -ContentType "application/json" `
    -Body $body
```

## Troubleshooting

### Issue: `uv: command not found`

**Solution**: Install `uv` first (see Prerequisites)

### Issue: Database connection error

**Solution**: 
1. Check PostgreSQL is running
2. Verify credentials in `app/config.py`
3. Ensure database exists

### Issue: Port already in use

**Solution**: Change port in `run.py`:
```python
uvicorn.run(
    "app.main:app",
    host="0.0.0.0",
    port=8001  # Change to different port
)
```

### Issue: Module not found errors

**Solution**: Make sure you're using `uv run`:
```bash
uv run python run.py
```

## Quick Reference

```bash
# Initial setup (one time)
cd D:\Xmedia\XSocialMedialAnalysis
uv sync

# Run application
uv run python run.py

# Install new package
uv add package-name

# Update dependencies
uv sync --upgrade
```

## Next Steps

1. ✅ Run `uv sync` to install dependencies
2. ✅ Configure database in `app/config.py`
3. ✅ Run `uv run python run.py`
4. ✅ Test API at http://localhost:8000/swagger
5. ✅ Start analyzing sentiment!


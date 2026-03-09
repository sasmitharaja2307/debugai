# Start POLYHEAL AI backend
$env:POLYHEAL_PROJECT_ROOT = "."
uvicorn backend.api_server:app --reload --host 0.0.0.0 --port 8000

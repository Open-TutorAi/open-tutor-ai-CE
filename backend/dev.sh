export FRONTEND_BUILD_DIR="$(pwd)/../build"
PORT="${PORT:-8080}"
uvicorn open_tutorai.main:app --port $PORT --host 0.0.0.0 --forwarded-allow-ips '*' --reload

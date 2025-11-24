# Chuẩn bị môi trường
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt

# Database & migration (PostgreSQL + Neo4j cho KG)
docker compose up -d
alembic upgrade head   # tạo bảng plant_lib + kg_* cho chat/pipeline

# Run API
uvicorn app.main:app --reload

# API chính
- Public thư viện cây/bệnh: GET /crops, GET /diseases, GET /diseases/{id}
- Đăng ký KG (chat): POST /kg/users
- Đăng nhập lấy session: POST /kg/sessions
- Chat (text + optional image_path): POST /kg/query

# Cấu hình KG qua env (ví dụ)
KG_DATABASE__URL=postgresql+psycopg2://plantlib_user:plantlib123@localhost:5434/plant_lib
KG_NEO4J__URL=neo4j://localhost:7687
KG_NEO4J__USERNAME=neo4j
KG_NEO4J__PASSWORD=pass
KG_GEMINI__API_KEYS=key1,key2

# Lệnh dọn Docker (tuỳ chọn)
for /F "tokens=*" %i in ('docker ps -q') do docker stop %i
for /F "tokens=*" %i in ('docker ps -aq') do docker rm -f %i
for /F "tokens=*" %i in ('docker volume ls -q') do docker volume rm %i
for /F "tokens=*" %i in ('docker images -aq') do docker rmi -f %i
docker network prune -f
docker builder prune -a -f

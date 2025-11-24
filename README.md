# Input env
DATABASE_URL=postgresql+psycopg2://plantlib_user:plantlib123@db:5432/plant_lib

KG_NEO4J__URL=

KG_NEO4J__USERNAME=

KG_NEO4J__PASSWORD=

KG_GEMINI__API_KEYS=

KG_GEMINI__CHAT_MODEL=models/gemini-2.5-flash-lite

KG_EMBEDDING__TEXT_MODEL=bkai-foundation-models/vietnamese-bi-encoder

KG_EMBEDDING__IMAGE_MODEL=openai/clip-vit-large-patch14

KG_CACHE__TTL_HOURS=24

KG_CACHE__SESSION_TTL_HOURS=168

NEXT_PUBLIC_API_URL=http://localhost:8000

# Set-up web
docker compose up -d --build 

# Run 
docker compose up -d

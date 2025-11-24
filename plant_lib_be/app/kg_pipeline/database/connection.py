from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.kg_pipeline.config import settings, get_logger
from app.kg_pipeline.database.models import Base

logger = get_logger(__name__)


class DatabaseConnection:
    def __init__(self):
        self.engine = create_engine(
            settings.database.url,
            pool_pre_ping=True,
            pool_recycle=3600,
            echo=False,
            future=True,
        )
        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine,
        )
        logger.info(f"KG DB connection ready: {settings.database.url.split('@')[-1]}")

    def create_tables(self):
        Base.metadata.create_all(bind=self.engine)
        logger.info("KG tables ensured")

    def drop_tables(self):
        Base.metadata.drop_all(bind=self.engine)
        logger.warning("KG tables dropped")

    def get_session(self):
        return self.SessionLocal()

    def test_connection(self) -> bool:
        try:
            with self.get_session() as session:
                session.execute(text("SELECT 1"))
            logger.info("KG DB ping successful")
            return True
        except Exception as exc:
            logger.error(f"KG DB ping failed: {exc}")
            return False


db_connection = DatabaseConnection()

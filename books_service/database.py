import os
from sqlmodel import create_engine, SQLModel, Session

# La URL viene de una variable de entorno (la inyectamos desde docker-compose)
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://booksuser:bookspass@localhost:5432/booksdb",
)

engine = create_engine(DATABASE_URL, echo=True)


def init_db():
    """Crea las tablas si no existen."""
    SQLModel.metadata.create_all(engine)


def get_session():
    """Dependencia de FastAPI: abre una sesión por request y la cierra al terminar."""
    with Session(engine) as session:
        yield session
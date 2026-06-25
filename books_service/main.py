import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Depends
from sqlmodel import Session, select
from sqlalchemy.exc import OperationalError

from database import init_db, get_session
from models import Book, BookCreate, BookUpdate

@asynccontextmanager
async def lifespan(app: FastAPI):
    for intento in range(10):
        try:
            init_db()
            break
        except OperationalError:
            print(f"DB no lista, reintento {intento + 1}/10...")
            time.sleep(3)
    yield


app = FastAPI(title="Books Service", lifespan=lifespan)


@app.get("/health")
def health():
    return {"status": "ok", "service": "books"}


# ---- READ ----
@app.get("/books", response_model=list[Book])
def list_books(session: Session = Depends(get_session)):
    return session.exec(select(Book)).all()


@app.get("/books/{book_id}", response_model=Book)
def get_book(book_id: int, session: Session = Depends(get_session)):
    book = session.get(Book, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Libro no encontrado")
    return book


# ---- CREATE ----
@app.post("/books", response_model=Book, status_code=201)
def create_book(data: BookCreate, session: Session = Depends(get_session)):
    book = Book.model_validate(data)
    session.add(book)
    session.commit()
    session.refresh(book)
    return book


# ---- UPDATE ----
@app.patch("/books/{book_id}", response_model=Book)
def update_book(book_id: int, data: BookUpdate, session: Session = Depends(get_session)):
    book = session.get(Book, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Libro no encontrado")
    # Solo actualiza los campos que el cliente envió (exclude_unset)
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(book, key, value)
    session.add(book)
    session.commit()
    session.refresh(book)
    return book


# ---- DELETE ----
@app.delete("/books/{book_id}", status_code=204)
def delete_book(book_id: int, session: Session = Depends(get_session)):
    book = session.get(Book, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Libro no encontrado")
    session.delete(book)
    session.commit()
    return None
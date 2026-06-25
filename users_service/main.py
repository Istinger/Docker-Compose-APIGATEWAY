import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Depends
from sqlmodel import Session, select
from sqlalchemy.exc import OperationalError, IntegrityError

from database import init_db, get_session
from models import User, UserCreate, UserUpdate


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


app = FastAPI(title="Users Service", lifespan=lifespan)


@app.get("/health")
def health():
    return {"status": "ok", "service": "users"}


# ---- READ ----
@app.get("/users", response_model=list[User])
def list_users(session: Session = Depends(get_session)):
    return session.exec(select(User)).all()


@app.get("/users/{user_id}", response_model=User)
def get_user(user_id: int, session: Session = Depends(get_session)):
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return user


# ---- CREATE ----
@app.post("/users", response_model=User, status_code=201)
def create_user(data: UserCreate, session: Session = Depends(get_session)):
    user = User.model_validate(data)
    session.add(user)
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise HTTPException(status_code=409, detail="El email ya está registrado")
    session.refresh(user)
    return user


# ---- UPDATE ----
@app.patch("/users/{user_id}", response_model=User)
def update_user(user_id: int, data: UserUpdate, session: Session = Depends(get_session)):
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(user, key, value)
    session.add(user)
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise HTTPException(status_code=409, detail="El email ya está registrado")
    session.refresh(user)
    return user


# ---- DELETE ----
@app.delete("/users/{user_id}", status_code=204)
def delete_user(user_id: int, session: Session = Depends(get_session)):
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    session.delete(user)
    session.commit()
    return None

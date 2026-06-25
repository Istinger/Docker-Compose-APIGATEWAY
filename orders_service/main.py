import os
import time
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI, HTTPException, Depends
from sqlmodel import Session, select
from sqlalchemy.exc import OperationalError

from database import init_db, get_session
from models import Order, OrderCreate, OrderUpdate

# URLs de los otros servicios (inyectadas por docker-compose).
# Apuntan al nombre de servicio + puerto INTERNO 8000.
USERS_URL = os.getenv("USERS_SERVICE_URL", "http://users_service:8000")
BOOKS_URL = os.getenv("BOOKS_SERVICE_URL", "http://books_service:8000")


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


app = FastAPI(title="Orders Service", lifespan=lifespan)


# ---- Helpers: validación contra los otros servicios ----
async def _verificar_existe(client: httpx.AsyncClient, url: str, entidad: str):
    try:
        resp = await client.get(url, timeout=5.0)
    except httpx.RequestError:
        # El otro servicio no respondió (caído, red, etc.)
        raise HTTPException(
            status_code=503,
            detail=f"El servicio de {entidad} no está disponible",
        )
    if resp.status_code == 404:
        raise HTTPException(status_code=404, detail=f"{entidad} no encontrado")
    if resp.status_code != 200:
        raise HTTPException(
            status_code=502,
            detail=f"Respuesta inesperada del servicio de {entidad}",
        )


@app.get("/health")
def health():
    return {"status": "ok", "service": "orders"}


# ---- READ ----
@app.get("/orders", response_model=list[Order])
def list_orders(session: Session = Depends(get_session)):
    return session.exec(select(Order)).all()


@app.get("/orders/{order_id}", response_model=Order)
def get_order(order_id: int, session: Session = Depends(get_session)):
    order = session.get(Order, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Orden no encontrada")
    return order


# ---- CREATE (con validación service-to-service) ----
@app.post("/orders", response_model=Order, status_code=201)
async def create_order(data: OrderCreate, session: Session = Depends(get_session)):
    async with httpx.AsyncClient() as client:
        # 1. ¿Existe el usuario?
        await _verificar_existe(
            client, f"{USERS_URL}/users/{data.user_id}", "Usuario"
        )
        # 2. ¿Existe el libro?
        await _verificar_existe(
            client, f"{BOOKS_URL}/books/{data.book_id}", "Libro"
        )

    # 3. Si ambos existen, creamos la orden
    order = Order.model_validate(data)
    session.add(order)
    session.commit()
    session.refresh(order)
    return order


# ---- UPDATE ----
@app.patch("/orders/{order_id}", response_model=Order)
def update_order(order_id: int, data: OrderUpdate, session: Session = Depends(get_session)):
    order = session.get(Order, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Orden no encontrada")
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(order, key, value)
    session.add(order)
    session.commit()
    session.refresh(order)
    return order


# ---- DELETE ----
@app.delete("/orders/{order_id}", status_code=204)
def delete_order(order_id: int, session: Session = Depends(get_session)):
    order = session.get(Order, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Orden no encontrada")
    session.delete(order)
    session.commit()
    return None

#--Get all orders by user 
@app.get("/orders/user/{user_id}", response_model=list[Order])
def orders_by_user(user_id: int, session: Session = Depends(get_session)):
    return session.exec(select(Order).where(Order.user_id == user_id)).all()
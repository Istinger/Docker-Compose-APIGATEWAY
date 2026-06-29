# Biblioteca Virtual — Microservicios con FastAPI, PostgreSQL y Nginx

Práctica de **Sistemas Distribuidos** — Universidad Politécnica Salesiana (UPS).

Sistema de biblioteca virtual construido con una arquitectura de **microservicios**. Tres servicios independientes (libros, usuarios y órdenes), cada uno con su propia base de datos PostgreSQL, orquestados con **Docker Compose** y expuestos al exterior a través de un **API Gateway (Nginx)**.

---

## Arquitectura

```
                          ┌─────────────── red interna (biblioteca-net) ───────────────┐
                          │                                                            │
  CLIENTE ──:80──▶ NGINX ─┼──/api/books/────▶ books_service:8000 ──▶ books-db:5432    │
  (curl / navegador)      │                                                            │
                          ├──/api/users/────▶ users_service:8000 ──▶ users-db:5432    │
                          │                                                            │
                          └──/api/orders/───▶ orders_service:8000 ─▶ orders-db:5432   │
                                                     │                                  │
                                                     │ (valida user y book)            │
                                                     ├──▶ users_service:8000           │
                                                     └──▶ books_service:8000           │
                          └────────────────────────────────────────────────────────────┘
```

- **Un único punto de entrada**: el cliente solo accede por el puerto **80** (Nginx). Los microservicios no se exponen directamente en producción.
- **Database-per-service**: cada microservicio es dueño de su propia base de datos. No comparten esquema ni tablas; el aislamiento es real.
- **Comunicación service-to-service**: `orders_service` valida contra `users_service` y `books_service` (vía HTTP con `httpx`) antes de crear una orden.

---

## Microservicios

| Servicio | Dominio | Puerto host (dev) | Puerto interno | Base de datos |
|----------|---------|-------------------|----------------|---------------|
| `books_service`  | Gestión de libros   | 8001 | 8000 | `books-db`  |
| `users_service`  | Gestión de usuarios | 8002 | 8000 | `users-db`  |
| `orders_service` | Gestión de órdenes  | 8003 | 8000 | `orders-db` |
| `nginx`          | API Gateway         | 80   | 80   | —           |

> Los puertos de host (8001–8003) son una **comodidad de desarrollo** (acceso directo + Swagger). En la configuración de producción se eliminan y todo el tráfico entra solo por el gateway (puerto 80).

**Stack por servicio:** FastAPI · SQLModel · psycopg2 · Uvicorn · (orders también usa `httpx`).

---

## Estructura del proyecto

```
Docker-Compose-APIGATEWAY/
├── docker-compose.yml          # Orquestación de todos los servicios
├── .env                        # Credenciales y config (NO se sube a Git)
├── .env.example                # Plantilla de variables (sí se sube)
├── .gitignore
├── README.md
│
├── nginx/
│   └── nginx.conf              # Configuración del API Gateway
│
├── books_service/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── main.py                 # Endpoints CRUD
│   ├── database.py             # Conexión y sesión de la DB
│   └── models.py               # Modelos SQLModel (Book, BookCreate, BookUpdate)
│
├── users_service/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── main.py
│   ├── database.py
│   └── models.py               # User, UserCreate, UserUpdate
│
└── orders_service/
    ├── Dockerfile
    ├── requirements.txt
    ├── main.py                 # CRUD + validación service-to-service
    ├── database.py
    └── models.py               # Order, OrderCreate, OrderUpdate
```

---

## Requisitos previos

- Docker y Docker Compose instalados.
- Puerto **80** libre en el host (que no haya otro Nginx/Apache corriendo).
- `curl` para las pruebas (incluido por defecto en la mayoría de distros Linux).

---

## Configuración: variables de entorno

Las credenciales **no van hardcodeadas** en `docker-compose.yml`. Se centralizan en un archivo `.env` en la raíz, que Docker Compose lee automáticamente e interpola con la sintaxis `${VARIABLE}`.

### `.env` (no subir a Git)

```bash
# Books
BOOKS_DB=booksdb
BOOKS_USER=booksuser
BOOKS_PASSWORD=bookspass_cambiame

# Users
USERS_DB=usersdb
USERS_USER=usersuser
USERS_PASSWORD=userspass_cambiame

# Orders
ORDERS_DB=ordersdb
ORDERS_USER=ordersuser
ORDERS_PASSWORD=orderspass_cambiame
```

### `.gitignore`

```
.env
__pycache__/
*.pyc
```

Se sube un `.env.example` con las claves pero sin valores reales, para que cualquiera sepa qué variables definir.

---

## Cómo levantar el proyecto

```bash
# Construir e iniciar todo
docker compose up --build

# En segundo plano
docker compose up --build -d

# Ver el estado de los contenedores
docker compose ps

# Ver logs (de un servicio concreto)
docker compose logs -f nginx
docker compose logs -f orders_service

# Detener
docker compose down

# Detener Y borrar volúmenes (se pierden los datos de las DB)
docker compose down -v
```

---

## Uso de la API (a través del Gateway)

Todo el tráfico entra por el puerto **80** con el prefijo `/api/<servicio>/`. Nginx quita el prefijo y reenvía al microservicio correspondiente.

> La "doble palabra" (`/api/books/books`) es correcta: el primer `/api/books/` es el **prefijo de enrutamiento** de Nginx; el segundo `/books` es el **endpoint real** de FastAPI.

### Books

```bash
# Health
curl http://localhost/api/books/health

# Crear
curl -X POST http://localhost/api/books/books \
  -H "Content-Type: application/json" \
  -d '{"title": "El Aleph", "author": "Borges", "year": 1949, "stock": 5}'

# Listar / obtener / actualizar / eliminar
curl http://localhost/api/books/books
curl http://localhost/api/books/books/1
curl -X PATCH http://localhost/api/books/books/1 -H "Content-Type: application/json" -d '{"stock": 3}'
curl -i -X DELETE http://localhost/api/books/books/1
```

### Users

```bash
curl -X POST http://localhost/api/users/users \
  -H "Content-Type: application/json" \
  -d '{"name": "Joss", "email": "joss@ups.edu.ec"}'

curl http://localhost/api/users/users
```

### Orders (con validación service-to-service)

```bash
# Orden válida → 201 (orders valida que el user y el book existan)
curl -i -X POST http://localhost/api/orders/orders \
  -H "Content-Type: application/json" \
  -d '{"user_id": 1, "book_id": 1, "quantity": 2}'

# Usuario inexistente → 404 "Usuario no encontrado"
curl -i -X POST http://localhost/api/orders/orders \
  -H "Content-Type: application/json" \
  -d '{"user_id": 999, "book_id": 1, "quantity": 1}'
```

---

## Documentación interactiva (Swagger)

FastAPI genera documentación automática. Mientras los puertos de desarrollo estén expuestos:

```
http://localhost:8001/docs    # books
http://localhost:8002/docs    # users
http://localhost:8003/docs    # orders
```

> Swagger **no** se sirve a través de Nginx con la configuración actual, porque el gateway solo enruta `/api/<servicio>/`. Para exponerlo por el gateway haría falta configurar `root_path="/api/books"` (etc.) en cada `FastAPI(...)`. En desarrollo es más simple acceder por el puerto directo.

---

## Endpoints por servicio

Todos los servicios siguen el mismo patrón CRUD:

| Método | Ruta (interna FastAPI) | Acción |
|--------|------------------------|--------|
| `GET`    | `/health`        | Estado del servicio |
| `GET`    | `/<recurso>`     | Listar todos |
| `GET`    | `/<recurso>/{id}`| Obtener uno |
| `POST`   | `/<recurso>`     | Crear |
| `PATCH`  | `/<recurso>/{id}`| Actualizar parcial |
| `DELETE` | `/<recurso>/{id}`| Eliminar |

Donde `<recurso>` es `books`, `users` u `orders`.

---


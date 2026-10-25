# Hearth & Co. — React + Django shop

A port of the Spring Boot + vanilla-JS shop to **Django REST framework** and **React (Vite)**.
The HTTP API is unchanged (same paths, camelCase JSON, `{"error": "..."}` bodies, status codes and headers),
so the original contract and `curl` examples still apply.

```
backend/    Django 5.2 + DRF       -> http://localhost:8000
frontend/   React 19 + Vite        -> http://localhost:5173  (proxies /api to Django)
```

## Run it

Needs Python 3.10+ and Node 20.19+ / 22.12+.

**1. Backend**
```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_shop                      # demo products (skipped if any exist)
SHOP_ADMIN_PASSWORD='something-long' python manage.py runserver
```
`SHOP_ADMIN_USER` defaults to `admin`. If `SHOP_ADMIN_PASSWORD` is unset, a random one is generated and printed
once in the startup log (development only; every server process would invent its own).

**2. Frontend** (second terminal)
```bash
cd frontend
npm install
npm run dev
```

**3. Tests** (backend)
```bash
cd backend && python manage.py test
```

## Configuration (environment variables)

| Variable | Default | Purpose |
|---|---|---|
| `SHOP_ADMIN_USER` / `SHOP_ADMIN_PASSWORD` | `admin` / random | Admin account (HTTP Basic) |
| `DJANGO_DEBUG` | `1` | Set `0` in production |
| `DJANGO_SECRET_KEY` | dev key | **Required** when `DJANGO_DEBUG=0` |
| `DJANGO_ALLOWED_HOSTS` | `localhost,127.0.0.1` | Comma-separated |
| `CORS_ALLOWED_ORIGINS` | Vite/localhost origins | Only needed if the UI is on another origin than the API |
| `DB_ENGINE` | `sqlite` | `mysql` to use MySQL 8 (`pip install mysqlclient`) |
| `DB_NAME` `DB_USER` `DB_PASSWORD` `DB_HOST` `DB_PORT` | `shop` `root` `` `127.0.0.1` `3306` | MySQL settings |
| `VITE_PROXY_TARGET` (frontend) | `http://localhost:8000` | Where the dev server forwards `/api` |
| `VITE_API_URL` (frontend, build time) | `/api` | Call an API on another origin |

With MySQL, create the database first (`CREATE DATABASE shop CHARACTER SET utf8mb4;`). Django, unlike the Spring
setup, does not create it for you.

## API

| Endpoint | Access |
|---|---|
| `GET /api/products?q=term`, `GET /api/products/{id}` | public |
| `POST /api/orders` (needs `Idempotency-Key` header) | public |
| `POST /api/products`, `PUT/DELETE /api/products/{id}` | **admin** |
| `GET /api/orders` | **admin** |

Admin requests use HTTP Basic auth:
```bash
curl -u admin:$SHOP_ADMIN_PASSWORD -X POST localhost:8000/api/products -H 'Content-Type: application/json' \
  -d '{"name":"Tea Towel","price":12.00,"stock":30,"category":"Kitchen","imageUrl":"https://example.com/t.jpg"}'
curl -u admin:$SHOP_ADMIN_PASSWORD localhost:8000/api/orders
```
Missing/wrong credentials -> `401 {"error":"Authentication required."}` (no `WWW-Authenticate` header, so browsers
never show a login dialog). The API is stateless: no sessions, cookies or CSRF middleware.

### Placing an order and retrying safely
```
POST /api/orders
Idempotency-Key: <8-64 chars: letters, digits, - or _ ; a UUID works>
{ "customerName", "email", "address", "items":[{ "productId", "quantity" }] }
```
| Situation | Result |
|---|---|
| First request with a key | `201`, order created, stock decremented |
| Same key and same order again | `200`, the original order, header `Idempotent-Replayed: true`, stock untouched |
| Same key, different order | `422` |
| Two requests with the same key at once | one creates the order; the other waits and returns it |
| Failed attempt (400 unknown product, 409 out of stock) | nothing saved, **including the key** |
| Missing/malformed key | `400` |

"Same order" is judged on meaning: trimmed name and address, case-insensitive email, items merged per product.
A unique index on `Order.idempotency_key` enforces it across server processes. Prices and stock always come from
the database; stock is checked and decremented in one transaction with `SELECT ... FOR UPDATE` row locks, taken in
ascending product-id order so concurrent orders can't deadlock.

## Where things went

| Spring Boot | Django / React |
|---|---|
| `model/*.java` | `backend/shop/models.py` |
| `service/OrderService.java` | `backend/shop/services.py` |
| `web/*Controller.java`, `ApiErrors` | `views.py`, `serializers.py`, `errors.py` |
| `SecurityConfig` | `auth.py` (+ `REST_FRAMEWORK` in `settings.py`) |
| `WebConfig` (CORS) | `django-cors-headers` in `settings.py` |
| `DataSeeder` | `manage.py seed_shop` |
| `frontend/app.js` | `frontend/src/` — `lib/` (api, cart, idempotency), `hooks/`, `components/`, `App.jsx` |
| `frontend/style.css` | `frontend/src/styles.css` (unchanged) |

## Differences from the original

- **DB default is SQLite** so it runs with no setup. SQLite has no row locks (`select_for_update` is a no-op);
  it is configured with `transaction_mode: IMMEDIATE`, so concurrent orders are serialised instead. Use MySQL
  (or Postgres) for real row-level locking.
- `DELETE /api/products/{id}` on a missing id returns `404` (Spring returned `204`).
- `PUT` on a product that omits `description`, `category` or `imageUrl` keeps the stored value (Spring nulled it).
- Validation errors also carry a `fields` object alongside the same `error` message.
- `imageUrl` must be `http(s)://` with no whitespace.
- Unknown API paths return `404` (Spring answered `401/403` via `denyAll`).
- Demo data is loaded by `seed_shop` rather than automatically at startup.

## Production notes

- `npm run build` writes `frontend/dist`. Serve it from the same origin as `/api` (e.g. nginx), or build with
  `VITE_API_URL` and set `CORS_ALLOWED_ORIGINS`.
- Run Django with a real server (`pip install gunicorn`; `gunicorn config.wsgi`), `DJANGO_DEBUG=0`,
  `DJANGO_SECRET_KEY`, `DJANGO_ALLOWED_HOSTS`, and an explicit `SHOP_ADMIN_PASSWORD`.
- Use HTTPS: Basic auth sends the password on every admin request.

## Not included (same as the original)
Payments, customer accounts, an admin UI, rate limiting / lockout on the admin login.

# SimpleShop — React + Django

A deliberately small e-commerce app for learning full-stack development.

## Features
- React/Vite single-page storefront
- Django REST-style JSON endpoints
- SQLite database (no separate database server required)
- Product search and category filtering
- Local cart persistence
- Checkout creates an Order and OrderItems
- Inventory is decremented server-side
- Django admin for products/orders

## Run with Docker
```bash
docker compose up --build
```
Open http://localhost:5173 and Django admin at http://localhost:8000/admin/.

## Run without Docker
Backend:
```bash
cd backend
python -m venv .venv
# activate the venv
pip install -r requirements.txt
python manage.py migrate
python seed.py
python manage.py runserver
```
Frontend in another terminal:
```bash
cd frontend
npm install
npm run dev
```

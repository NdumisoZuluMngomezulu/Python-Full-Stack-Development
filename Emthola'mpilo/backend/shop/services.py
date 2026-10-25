"""
Placing an order exactly once per Idempotency-Key.

  - Same key, same request   -> the original order is returned (replayed=True); no stock is touched.
  - Same key, different one  -> 422, because the client is reusing a key for something else.
  - Two simultaneous requests with the same key -> one creates the order; the other blocks on the unique index
    and then gets the first one's order.
  - Only successful orders are remembered. A failed attempt (unknown product, out of stock) rolls back completely,
    including the key, so the client can retry with the same key.

Prices and stock always come from the database, never from the client.
"""
import hashlib
import re
from dataclasses import dataclass
from decimal import Decimal

from django.db import IntegrityError, OperationalError, transaction

from .errors import ApiError
from .models import Order, OrderItem, Product

KEY_PATTERN = re.compile(r"[A-Za-z0-9_-]{8,64}")

# MySQL: 1205 = lock wait timeout, 1213 = deadlock victim.
_MYSQL_LOCK_ERRORS = {1205, 1213}


@dataclass(frozen=True)
class PlacedOrder:
    order: Order
    replayed: bool  # True when the key had already produced this order and we returned it instead of creating another


def place_order(key: str | None, data: dict) -> PlacedOrder:
    if not key or not KEY_PATTERN.fullmatch(key):
        raise ApiError(400, "Idempotency-Key header is required (8-64 characters: letters, digits, - or _).")

    wanted = _merge(data["items"])
    digest = _fingerprint(data, wanted)

    prior = _find_by_key(key)
    if prior is not None:
        return _replay(prior, digest)

    # The duplicate-key error must be caught OUTSIDE the transaction it poisons, so the atomic block is the
    # innermost thing in this try.
    try:
        with transaction.atomic():
            order = _create(key, digest, data, wanted)
        return PlacedOrder(order, replayed=False)
    except (IntegrityError, OperationalError) as exc:
        # A concurrent request with the same key won the race (or we were picked as a deadlock victim).
        winner = _find_by_key(key)
        if winner is not None:
            return _replay(winner, digest)
        if isinstance(exc, OperationalError) and _is_lock_conflict(exc):
            raise ApiError(409, "Your order is still being processed. Please try again in a moment.") from exc
        raise


def _create(key: str, digest: str, data: dict, wanted: dict[int, int]) -> Order:
    """
    The order row (with its unique key) is inserted FIRST, so a duplicate request blocks there before it can touch
    stock. Each product row is then locked (SELECT ... FOR UPDATE) before its stock is checked. Lines are merged per
    product and locked in ascending id order so concurrent orders can't deadlock.
    """
    order = Order.objects.create(
        customer_name=data["customerName"],
        email=data["email"],
        address=data["address"],
        total=Decimal("0.00"),
        idempotency_key=key,
        request_hash=digest,
    )

    total = Decimal("0.00")
    items: list[OrderItem] = []
    for product_id, quantity in wanted.items():  # ascending id order
        product = Product.objects.select_for_update().filter(pk=product_id).first()
        if product is None:
            raise ApiError(400, f"Unknown product {product_id}")
        if product.stock < quantity:
            raise ApiError(409, f"Not enough stock for {product.name}")
        product.stock -= quantity
        product.save(update_fields=["stock"])
        items.append(OrderItem(
            order=order,
            product_id=product.pk,
            product_name=product.name,
            quantity=quantity,
            unit_price=product.price,
        ))
        total += product.price * quantity

    OrderItem.objects.bulk_create(items)
    order.total = total
    order.save(update_fields=["total"])
    return order


def _find_by_key(key: str) -> Order | None:
    return Order.objects.prefetch_related("items").filter(idempotency_key=key).first()


def _replay(existing: Order, digest: str) -> PlacedOrder:
    if existing.request_hash != digest:
        raise ApiError(422, "This Idempotency-Key was already used for a different order.")
    return PlacedOrder(existing, replayed=True)


def _merge(lines: list[dict]) -> dict[int, int]:
    """Duplicate product lines are summed; sorting gives a stable, ascending lock order."""
    wanted: dict[int, int] = {}
    for line in lines:
        wanted[line["productId"]] = wanted.get(line["productId"], 0) + line["quantity"]
    return dict(sorted(wanted.items()))


def _fingerprint(data: dict, wanted: dict[int, int]) -> str:
    """Hash of the request's meaning (not its formatting): trimmed text, lower-cased email, merged sorted lines."""
    parts = [data["customerName"].strip(), data["email"].strip().lower(), data["address"].strip()]
    parts += [f"{product_id}:{quantity}" for product_id, quantity in wanted.items()]
    # Length-prefix each field so ("ab","c") and ("a","bc") can never hash the same.
    canonical = "".join(f"{len(p)}:{p};" for p in parts)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _is_lock_conflict(exc: OperationalError) -> bool:
    code = exc.args[0] if exc.args else None
    if isinstance(code, int):
        return code in _MYSQL_LOCK_ERRORS
    return "locked" in str(exc).lower()  # SQLite: "database is locked"

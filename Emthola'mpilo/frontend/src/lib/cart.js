const CART_KEY = "cart";

/** Cart shape: { [productId: string]: quantity } */
export function readCart() {
  try {
    const c = JSON.parse(localStorage.getItem(CART_KEY) || "{}");
    if (!c || typeof c !== "object" || Array.isArray(c)) return {};
    return Object.fromEntries(Object.entries(c).filter(([, q]) => Number.isInteger(q) && q > 0));
  } catch {
    return {};
  }
}

export function writeCart(cart) {
  try { localStorage.setItem(CART_KEY, JSON.stringify(cart)); } catch { /* storage full or blocked: cart lives in memory only */ }
}

/** Make the cart agree with the catalogue: drop deleted/sold-out items, cap quantities at stock. */
export function reconcileCart(cart, products) {
  const byId = new Map(products.map((p) => [String(p.id), p]));
  const next = { ...cart };
  let changed = false;
  for (const [id, q] of Object.entries(cart)) {
    const p = byId.get(id);
    if (!p || p.stock < 1) { delete next[id]; changed = true; }   // deleted or sold out
    else if (q > p.stock) { next[id] = p.stock; changed = true; } // more than is left
  }
  return { cart: next, changed };
}

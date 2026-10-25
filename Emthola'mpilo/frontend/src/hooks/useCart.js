import { useCallback, useRef, useState } from "react";
import { readCart, writeCart } from "../lib/cart.js";

/**
 * Cart state persisted to localStorage. `cartRef` always holds the latest cart, so async code (checkout, catalogue
 * refresh) never works from a stale render's copy.
 */
export function useCart() {
  const [cart, setCart] = useState(readCart);
  const cartRef = useRef(cart);

  const commit = useCallback((next) => {
    cartRef.current = next;
    setCart(next);
    writeCart(next);
  }, []);

  /** Add or remove `delta` of a product, never going above its stock; reaching zero removes the line. */
  const change = useCallback((product, delta) => {
    const id = String(product.id);
    const q = Math.min((cartRef.current[id] || 0) + delta, product.stock);
    const next = { ...cartRef.current };
    if (q <= 0) delete next[id]; else next[id] = q;
    commit(next);
  }, [commit]);

  return { cart, cartRef, commit, change };
}

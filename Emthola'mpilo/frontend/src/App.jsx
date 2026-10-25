import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import CartDrawer from "./components/CartDrawer.jsx";
import Filters from "./components/Filters.jsx";
import Header from "./components/Header.jsx";
import ProductGrid from "./components/ProductGrid.jsx";
import { useCart } from "./hooks/useCart.js";
import { useCatalog } from "./hooks/useCatalog.js";
import { createOrder } from "./lib/api.js";
import { reconcileCart } from "./lib/cart.js";
import { money } from "./lib/format.js";
import { clearAttempt, orderKeyFor } from "./lib/idempotency.js";

export default function App() {
  const [searchText, setSearchText] = useState("");
  const [query, setQuery] = useState("");
  const [category, setCategory] = useState("All");
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [showCheckout, setShowCheckout] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const submittingRef = useRef(false); // synchronous guard: state would lag behind a fast double submit
  const [message, setMessage] = useState({ text: "", err: false });

  const { all, products, failed, loading, syncAll, reloadSearch } = useCatalog(query);
  const { cart, cartRef, commit, change } = useCart();

  const say = useCallback((text, err = false) => setMessage({ text, err }), []);

  // Debounce the search box.
  useEffect(() => {
    const t = setTimeout(() => setQuery(searchText.trim()), 250);
    return () => clearTimeout(t);
  }, [searchText]);

  /** Reload the catalogue, fix the cart to match it, and refresh any open search. Resolves true if the cart changed. */
  const refresh = useCallback(async () => {
    let changed = false;
    try {
      const list = await syncAll();
      const r = reconcileCart(cartRef.current, list);
      if (r.changed) { commit(r.cart); changed = true; }
    } catch { /* the grid shows the connection error */ }
    reloadSearch();
    return changed;
  }, [syncAll, reloadSearch, commit, cartRef]);

  // First load.
  useEffect(() => {
    let alive = true;
    syncAll()
      .then((list) => {
        if (!alive) return;
        const r = reconcileCart(cartRef.current, list);
        if (r.changed) {
          commit(r.cart);
          say("Some items in your cart are no longer available, so we updated it.", true);
        }
      })
      .catch(() => { /* the grid shows the connection error */ });
    return () => { alive = false; };
  }, [syncAll, commit, cartRef, say]);

  // --- derived data -----------------------------------------------------------------------------------------
  const categories = useMemo(() => ["All", ...new Set(all.map((p) => p.category).filter(Boolean))], [all]);
  const activeCategory = categories.includes(category) ? category : "All";
  const visible = useMemo(
    () => products.filter((p) => activeCategory === "All" || p.category === activeCategory),
    [products, activeCategory],
  );

  const byId = useMemo(() => new Map(all.map((p) => [String(p.id), p])), [all]);
  const rows = useMemo(
    () => Object.entries(cart).map(([id, q]) => ({ p: byId.get(id), q })).filter((r) => r.p),
    [cart, byId],
  );
  const count = rows.reduce((n, r) => n + r.q, 0);
  const total = rows.reduce((t, r) => t + r.p.price * r.q, 0);

  // An empty cart closes the checkout form, so adding something later starts from the "Checkout" button again.
  useEffect(() => { if (rows.length === 0) setShowCheckout(false); }, [rows.length]);

  // --- actions ----------------------------------------------------------------------------------------------
  const addToCart = (product) => { change(product, 1); setDrawerOpen(true); };

  async function placeOrder(e) {
    e.preventDefault();
    if (submittingRef.current) return; // ignore double clicks / double Enter
    const items = Object.entries(cartRef.current)
      .map(([productId, quantity]) => ({ productId: Number(productId), quantity }))
      .sort((a, b) => a.productId - b.productId);
    if (!items.length) return;

    const form = e.currentTarget;
    const details = Object.fromEntries(new FormData(form));
    const key = orderKeyFor({ f: details, items });

    submittingRef.current = true;
    setSubmitting(true);
    say("Placing your order…");
    try {
      const order = await createOrder(key, { ...details, items });
      clearAttempt();
      commit({});
      form.reset();
      setShowCheckout(false);
      say(`Order #${order.id} placed. Total ${money(order.total)}.`);
      await refresh();
    } catch (err) {
      if (err.network) {
        // We can't know whether the server got the order. Leave the cart and key untouched: pressing the button
        // again retries with the same key, and the server returns the original order if it was already placed.
        say("We couldn't confirm your order because of a connection problem. Press Place order again; it won't be placed twice.", true);
      } else {
        if (err.status === 422) clearAttempt(); // key clashed with a different order: start fresh next time
        // Stock or catalogue probably changed: re-sync so the cart and grid show the truth.
        const adjusted = await refresh();
        say(err.message + (adjusted ? " We've updated your cart to match what's available." : ""), true);
      }
    } finally {
      submittingRef.current = false;
      setSubmitting(false);
    }
  }

  return (
    <>
      <Header search={searchText} onSearch={setSearchText} count={count} onOpenCart={() => setDrawerOpen(true)} />
      <main>
        <h1>Things made to be used every day.</h1>
        <Filters categories={categories} active={activeCategory} onPick={setCategory} />
        <ProductGrid products={visible} loading={loading} failed={failed} onAdd={addToCart} />
      </main>
      <CartDrawer
        open={drawerOpen}
        rows={rows}
        total={total}
        showForm={showCheckout && rows.length > 0}
        submitting={submitting}
        message={message}
        onClose={() => setDrawerOpen(false)}
        onChange={change}
        onStartCheckout={() => setShowCheckout(true)}
        onSubmit={placeOrder}
      />
    </>
  );
}

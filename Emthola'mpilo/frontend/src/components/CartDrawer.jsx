import { money } from "../lib/format.js";

export default function CartDrawer({
  open, rows, total, showForm, submitting, message,
  onClose, onChange, onStartCheckout, onSubmit,
}) {
  return (
    <>
      <aside id="drawer" className={"drawer" + (open ? " open" : "")} aria-hidden={!open}>
        <div className="drawer-head">
          <h2>Your cart</h2>
          <button onClick={onClose} aria-label="Close cart">Close</button>
        </div>

        <ul className="cart-items">
          {rows.length ? rows.map(({ p, q }) => (
            <li key={p.id}>
              <span>{p.name}</span>
              <span>{money(p.price * q)}</span>
              <span className="qty">
                <button aria-label="Remove one" onClick={() => onChange(p, -1)}>−</button>
                {q}
                <button aria-label="Add one" onClick={() => onChange(p, 1)}>+</button>
              </span>
            </li>
          )) : <li>Your cart is empty. Add something from the shop.</li>}
        </ul>

        <p className="total">Total <strong>{money(total)}</strong></p>

        {/* Kept mounted (just hidden) so typed details survive closing the cart, as in the original. */}
        <form id="checkout" hidden={!showForm} onSubmit={onSubmit}>
          <input name="customerName" placeholder="Full name" required />
          <input name="email" type="email" placeholder="Email" required />
          <textarea name="address" placeholder="Delivery address" rows={2} required />
          <button className="primary" type="submit" disabled={submitting}>Place order</button>
        </form>

        {rows.length > 0 && !showForm && (
          <button className="primary" onClick={onStartCheckout}>Checkout</button>
        )}

        <p className={"msg" + (message.err ? " err" : "")} role="status">{message.text}</p>
      </aside>
      <div className="scrim" hidden={!open} onClick={onClose} />
    </>
  );
}

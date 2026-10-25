import { money, safeUrl } from "../lib/format.js";

export default function ProductCard({ product: p, onAdd }) {
  const img = safeUrl(p.imageUrl);
  const soldOut = p.stock < 1;
  return (
    <article className="card">
      {img && <img src={img} alt={p.name} loading="lazy" />}
      <div>
        <h3>{p.name}</h3>
        <p>{p.description}</p>
        <span className="price">{money(p.price)}</span>
        {p.stock > 0 && p.stock < 10 && <span className="low">Only {p.stock} left</span>}
        <button disabled={soldOut} onClick={() => onAdd(p)}>{soldOut ? "Sold out" : "Add to cart"}</button>
      </div>
    </article>
  );
}

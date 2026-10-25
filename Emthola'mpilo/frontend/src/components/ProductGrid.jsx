import ProductCard from "./ProductCard.jsx";

export default function ProductGrid({ products, loading, failed, onAdd }) {
  let content = null;
  if (failed) {
    content = <p className="msg err">Can't reach the shop server. Start the backend on port 8000 and refresh.</p>;
  } else if (loading) {
    content = null;
  } else if (!products.length) {
    content = <p>No products match. Try a different search.</p>;
  } else {
    content = products.map((p) => <ProductCard key={p.id} product={p} onAdd={onAdd} />);
  }
  return <div id="grid" className="grid" aria-live="polite">{content}</div>;
}

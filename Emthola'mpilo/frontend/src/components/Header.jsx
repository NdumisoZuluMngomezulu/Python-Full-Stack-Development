export default function Header({ search, onSearch, count, onOpenCart }) {
  return (
    <header className="top">
      <a className="brand" href="/">Hearth &amp; Co.</a>
      <input
        id="search"
        type="search"
        placeholder="Search products"
        aria-label="Search products"
        value={search}
        onChange={(e) => onSearch(e.target.value)}
      />
      <button id="cartBtn" className="cart-btn" onClick={onOpenCart}>Cart ({count})</button>
    </header>
  );
}

export default function Filters({ categories, active, onPick }) {
  return (
    <div id="filters" className="filters">
      {categories.map((c) => (
        <button key={c} aria-pressed={c === active} onClick={() => onPick(c)}>{c}</button>
      ))}
    </div>
  );
}

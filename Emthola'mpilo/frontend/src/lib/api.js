// Same-origin "/api" by default (Vite proxies it to Django in dev). Set VITE_API_URL to call another origin.
const API = import.meta.env.VITE_API_URL || "/api";

/** Resolves with parsed JSON. Rejects with an Error carrying `.status`, or `.network = true` if the server is unreachable. */
export async function api(path, opts = {}) {
  let res;
  try {
    res = await fetch(API + path, {
      ...opts,
      headers: { "Content-Type": "application/json", ...opts.headers },
    });
  } catch {
    throw Object.assign(new Error("Can't reach the shop server."), { network: true });
  }
  const data = res.status === 204 ? null : await res.json().catch(() => ({}));
  if (!res.ok) {
    throw Object.assign(new Error(data?.error || "Something went wrong. Try again."), { status: res.status });
  }
  return data;
}

export const listProducts = (q = "") => api("/products" + (q ? "?q=" + encodeURIComponent(q) : ""));

export const createOrder = (idempotencyKey, order) =>
  api("/orders", { method: "POST", headers: { "Idempotency-Key": idempotencyKey }, body: JSON.stringify(order) });

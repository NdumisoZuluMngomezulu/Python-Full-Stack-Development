// One Idempotency-Key per intended order, reused on every retry of the same order.
// The key survives a reload (localStorage). It is replaced when the order's contents change, and cleared once the
// order succeeds. If a request was processed but the response got lost, retrying with the same key returns the
// original order instead of creating a second one.
const ATTEMPT = "orderAttempt";

function newKey() {
  if (crypto.randomUUID) return crypto.randomUUID();
  return Array.from(crypto.getRandomValues(new Uint8Array(16)), (b) => b.toString(16).padStart(2, "0")).join("");
}

// Small non-cryptographic hash, so no customer details are kept in localStorage.
function hashStr(s) {
  let h1 = 0xdeadbeef, h2 = 0x41c6ce57;
  for (let i = 0; i < s.length; i++) {
    const c = s.charCodeAt(i);
    h1 = Math.imul(h1 ^ c, 2654435761);
    h2 = Math.imul(h2 ^ c, 1597334677);
  }
  h1 = Math.imul(h1 ^ (h1 >>> 16), 2246822507) ^ Math.imul(h2 ^ (h2 >>> 13), 3266489909);
  h2 = Math.imul(h2 ^ (h2 >>> 16), 2246822507) ^ Math.imul(h1 ^ (h1 >>> 13), 3266489909);
  return (h2 >>> 0).toString(16) + (h1 >>> 0).toString(16);
}

/** The key for this exact order (same details + same items => same key). */
export function orderKeyFor(payload) {
  const sig = hashStr(JSON.stringify(payload));
  let attempt = null;
  try { attempt = JSON.parse(localStorage.getItem(ATTEMPT) || "null"); } catch { /* ignore */ }
  if (!attempt || attempt.sig !== sig || typeof attempt.key !== "string") {
    attempt = { key: newKey(), sig };
    try { localStorage.setItem(ATTEMPT, JSON.stringify(attempt)); } catch { /* ignore */ }
  }
  return attempt.key;
}

export function clearAttempt() {
  try { localStorage.removeItem(ATTEMPT); } catch { /* ignore */ }
}

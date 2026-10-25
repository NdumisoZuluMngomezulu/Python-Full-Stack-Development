import { useCallback, useEffect, useState } from "react";
import { listProducts } from "../lib/api.js";

/**
 * `all` is the full catalogue: category filters and the cart always read from it.
 * `products` is what the grid shows: `all`, or the search results for `query`.
 */
export function useCatalog(query) {
  const [all, setAll] = useState([]);
  const [loaded, setLoaded] = useState(false);
  const [syncFailed, setSyncFailed] = useState(false);
  const [results, setResults] = useState(null);
  const [searchFailed, setSearchFailed] = useState(false);
  const [reload, setReload] = useState(0);

  /** Reload the full catalogue. Resolves with the list; rejects (and flags the failure) if the server is unreachable. */
  const syncAll = useCallback(async () => {
    try {
      const list = await listProducts();
      setAll(list);
      setLoaded(true);
      setSyncFailed(false);
      return list;
    } catch (err) {
      setSyncFailed(true);
      throw err;
    }
  }, []);

  // Search. The cleanup makes a late response from an older query harmless.
  useEffect(() => {
    setSearchFailed(false);
    if (!query) { setResults(null); return undefined; }
    let stale = false;
    listProducts(query)
      .then((list) => { if (!stale) setResults(list); })
      .catch(() => { if (!stale) setSearchFailed(true); });
    return () => { stale = true; };
  }, [query, reload]);

  const reloadSearch = useCallback(() => setReload((n) => n + 1), []);

  const failed = query ? searchFailed : syncFailed;
  const loading = !query && !loaded && !syncFailed;
  const products = query ? (results ?? all) : all;

  return { all, products, failed, loading, syncAll, reloadSearch };
}

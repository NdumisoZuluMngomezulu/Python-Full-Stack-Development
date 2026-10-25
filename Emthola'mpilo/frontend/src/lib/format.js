export const money = (n) => "$" + Number(n).toFixed(2);

/** Only http(s) image URLs are ever rendered. */
export const safeUrl = (u) => (/^https?:\/\//i.test(u || "") ? u : "");

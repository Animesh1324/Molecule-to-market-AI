/**
 * Currency display preference: which unit numbers are shown in, and whether
 * large figures use Indian (Crore/Lakh) or Western (Million/Billion)
 * grouping. Purely a display transform — every underlying value from the API
 * stays exactly what the backend computed; nothing here recalculates a
 * figure, it only reformats how one is written.
 *
 * A single global preference (like the theme), not per-field, because a
 * brand manager reading the whole app wants one consistent convention, not a
 * mix of $M and ₹Cr on the same screen.
 */

export type CurrencyDisplay = 'inr-cr' | 'inr-plain' | 'usd';

const STORAGE_KEY = 'brandplan-currency-display';

export function getCurrencyPreference(): CurrencyDisplay {
  if (typeof window === 'undefined') return 'inr-cr';
  const stored = window.localStorage.getItem(STORAGE_KEY);
  if (stored === 'inr-cr' || stored === 'inr-plain' || stored === 'usd') return stored;
  return 'inr-cr';
}

export function setCurrencyPreference(pref: CurrencyDisplay): void {
  try {
    window.localStorage.setItem(STORAGE_KEY, pref);
  } catch {
    // Preference simply will not persist.
  }
}

/**
 * Indian digit grouping: 1,23,45,678 rather than 12,345,678. `decimals`
 * controls how many fractional digits survive — 0 for whole-rupee amounts,
 * 1-2 for a Crore/Lakh figure where the fractional part is the whole point
 * (₹2.99 L is meaningfully different from ₹3 L). toFixed(0) on the raw value
 * would silently truncate that fraction before grouping ever saw it.
 */
function formatIndianGrouping(value: number, decimals = 0): string {
  const negative = value < 0;
  const [intPart, decPart] = Math.abs(value).toFixed(decimals).split('.');
  const lastThree = intPart.slice(-3);
  const rest = intPart.slice(0, -3);
  const grouped = rest ? rest.replace(/\B(?=(\d{2})+(?!\d))/g, ',') + ',' + lastThree : lastThree;
  return (negative ? '-' : '') + grouped + (decPart ? '.' + decPart : '');
}

/**
 * Format a value already in INR into the chosen Indian display convention.
 * `inr-cr` divides into Crore (1,00,00,000) with one decimal, appropriate for
 * the large market-size and forecast figures this app deals in; `inr-plain`
 * keeps the raw rupee amount with Indian digit grouping, appropriate for
 * per-patient or per-pack prices too small to usefully express in Crore.
 */
export function formatINR(value: number, display: CurrencyDisplay, compact = true): string {
  // Crore only once the figure is at least ~10 lakh (1,000,000) — below that,
  // dividing by a crore and rounding to one decimal collapses a real value
  // like ₹2,98,800 to "₹0.0 Cr", which reads as nothing rather than a small
  // number. Lakh is the right unit for that range.
  if (display === 'inr-cr' && compact && Math.abs(value) >= 1000000) {
    return `₹${formatIndianGrouping(value / 10000000, 1)} Cr`;
  }
  if (display === 'inr-cr' && compact && Math.abs(value) >= 1000) {
    return `₹${formatIndianGrouping(value / 100000, 2)} L`;
  }
  return `₹${formatIndianGrouping(value)}`;
}

/** USD_TO_INR is a fixed planning rate, not a live feed — precision here
 * would be false confidence for a forecasting tool where the real inputs
 * (adoption curves, epidemiology) are already planning heuristics. Update
 * this constant directly if a materially different rate matters to a plan;
 * it is not meant to track daily FX movement.
 */
export const USD_TO_INR_PLANNING_RATE = 83;

/**
 * Format a USD figure under the current preference — converted to INR display
 * if that's selected, using the fixed planning rate above, with the
 * conversion stated so a reader can tell it's a display convenience, not a
 * separately-sourced figure.
 */
export function formatCurrencyFromUSD(usdValue: number, display: CurrencyDisplay): string {
  if (display === 'usd') {
    return `$${usdValue.toLocaleString('en-US', { maximumFractionDigits: 0 })}`;
  }
  return formatINR(usdValue * USD_TO_INR_PLANNING_RATE, display);
}

/** Format an INR figure under the current preference — converted to USD
 * display if that's selected, using the same fixed planning rate.
 */
export function formatCurrencyFromINR(inrValue: number, display: CurrencyDisplay): string {
  if (display === 'usd') {
    return `$${(inrValue / USD_TO_INR_PLANNING_RATE).toLocaleString('en-US', { maximumFractionDigits: 0 })}`;
  }
  return formatINR(inrValue, display);
}

/**
 * Market-extract figures (IQVIA/IMS/PharmaTrac) are stored already expressed
 * in Crore — this converts back to raw rupees first so the same three-way
 * switch (Crore/Lakh, plain rupees, USD) applies to them consistently with
 * every other currency figure in the app.
 */
export function formatCurrencyFromCrore(valueInCrore: number, display: CurrencyDisplay): string {
  return formatCurrencyFromINR(valueInCrore * 10_000_000, display);
}

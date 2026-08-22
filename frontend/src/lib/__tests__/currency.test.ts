/**
 * The rounding-to-zero bug this pins down: a value under ~10 lakh, formatted
 * in Crore with one decimal, rounds to "0.0 Cr" — a real figure disappearing
 * into nothing. Found live: "Net Patient-Year Cost" at ₹2,98,800 showed as
 * "₹0 Cr" before this test existed.
 */
import {
  formatINR,
  formatCurrencyFromUSD,
  formatCurrencyFromINR,
  formatCurrencyFromCrore,
  USD_TO_INR_PLANNING_RATE,
} from '../currency';

describe('formatINR', () => {
  it('never collapses a real sub-crore value to zero', () => {
    expect(formatINR(298800, 'inr-cr')).not.toBe('₹0 Cr');
    expect(formatINR(298800, 'inr-cr')).not.toContain('0.0 Cr');
  });

  it('uses Lakh (2 decimals) for values between 1,000 and ~10 lakh', () => {
    expect(formatINR(298800, 'inr-cr')).toBe('₹2.99 L');
    expect(formatINR(50000, 'inr-cr')).toBe('₹0.50 L');
  });

  it('uses Crore (1 decimal) once a value reaches 10 lakh', () => {
    expect(formatINR(1000000, 'inr-cr')).toBe('₹0.1 Cr');
    expect(formatINR(447267910000, 'inr-cr')).toBe('₹44,726.8 Cr');
  });

  it('uses plain rupees with Indian grouping below 1,000', () => {
    expect(formatINR(500, 'inr-cr')).toBe('₹500');
  });

  it('inr-plain always uses Indian digit grouping, never Cr/L', () => {
    expect(formatINR(12345678, 'inr-plain')).toBe('₹1,23,45,678');
    expect(formatINR(298800, 'inr-plain')).toBe('₹2,98,800');
  });

  it('handles negative values without breaking the sign or grouping', () => {
    expect(formatINR(-298800, 'inr-plain')).toBe('₹-2,98,800');
  });
});

describe('currency conversion round trips', () => {
  it('formatCurrencyFromUSD converts using the fixed planning rate', () => {
    const result = formatCurrencyFromINR(3600 * USD_TO_INR_PLANNING_RATE, 'inr-cr');
    expect(formatCurrencyFromUSD(3600, 'inr-cr')).toBe(result);
  });

  it('formatCurrencyFromUSD passes through untouched when display is usd', () => {
    expect(formatCurrencyFromUSD(3600, 'usd')).toBe('$3,600');
  });

  it('formatCurrencyFromCrore converts back to raw rupees before formatting', () => {
    // 1 Cr = 1,00,00,000 rupees, so 0.5 Cr in USD should equal that many
    // rupees converted, not 0.5 treated as raw rupees.
    const direct = formatCurrencyFromINR(0.5 * 10_000_000, 'usd');
    expect(formatCurrencyFromCrore(0.5, 'usd')).toBe(direct);
  });

  it('a round trip through Crore and back to USD stays proportional', () => {
    const usdMillions = 53887.7 * 1_000_000; // matches the live figure found in testing
    const inr = usdMillions * USD_TO_INR_PLANNING_RATE;
    const backToUsd = formatCurrencyFromCrore(inr / 10_000_000, 'usd');
    expect(backToUsd).toBe(`$${Math.round(usdMillions).toLocaleString('en-US')}`);
  });
});

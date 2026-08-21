/** @type {import('tailwindcss').Config} */

// Design tokens lifted from animesh-portfolio: navy + gold on warm neutrals,
// Inter for body, DM Serif Display for headings.
//
// Rather than rewrite every component, the existing scales are *redefined* to
// the portfolio palette. `slate-*` becomes the warm neutral / navy ramp and
// `brand-*` becomes gold, so `bg-slate-900` and `text-brand-500` — already used
// across every panel — now render the portfolio look with no markup churn.
const navy = {
  50: '#F7F8FA',   // --c-off
  100: '#EDF0F5',  // --c-light
  200: '#E4E8EF',  // --c-border
  300: '#c9d2e0',
  400: '#8898aa',  // --c-muted
  500: '#4a5568',  // --c-mid
  600: '#37476b',
  700: '#2d5080',  // --c-navy-3
  800: '#243d63',  // --c-navy-2
  850: '#1f3556',
  900: '#1B2F4E',  // --c-navy
  950: '#14243c',
};

const gold = {
  50: '#fdfaf0',
  100: '#faf3dc',
  200: '#f3e5b4',
  300: '#e9d183',
  400: '#d4ae45',  // --c-gold-2
  500: '#B8962E',  // --c-gold
  600: '#9c7d24',
  700: '#7c631d',
  800: '#5f4c18',
  900: '#493a14',
  950: '#2b220b',
};

module.exports = {
  // Class strategy: the ThemeProvider toggles `dark` on <html>, so the same
  // markup renders in either kit without duplicate component trees.
  darkMode: 'class',
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        brand: gold,
        navy,
        slate: navy,
        pharma: {
          teal: '#2d5080',
          slate: '#1B2F4E',
          card: '#243d63',
          emerald: '#4a7c59',
          crimson: '#a13d3d',
          amber: '#B8962E',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
        display: ['"DM Serif Display"', '"Playfair Display"', 'Georgia', 'serif'],
        mono: ['"JetBrains Mono"', 'ui-monospace', 'SFMono-Regular', 'monospace'],
      },
      borderRadius: {
        sm: '10px',      // --r-sm
        DEFAULT: '10px',
        lg: '16px',      // --r
        xl: '16px',
        '2xl': '24px',   // --r-lg
        '3xl': '28px',
      },
      boxShadow: {
        s1: '0 1px 3px rgba(0,0,0,.06), 0 1px 2px rgba(0,0,0,.04)',
        s2: '0 4px 24px rgba(27,47,78,.08)',
        s3: '0 12px 48px rgba(27,47,78,.12)',
        s4: '0 24px 64px rgba(27,47,78,.16)',
      },
      transitionTimingFunction: {
        portfolio: 'cubic-bezier(.16, 1, .3, 1)',
      },
    },
  },
  plugins: [],
};

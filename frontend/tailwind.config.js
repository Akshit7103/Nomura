/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './pages/**/*.{js,jsx}',
    './components/**/*.{js,jsx}',
    './app/**/*.{js,jsx}',
  ],
  theme: {
    extend: {
      colors: {
        /* ── App surface ── */
        surface: '#f4f6fa',

        /* ── Sidebar ── */
        sidebar: {
          DEFAULT: '#101828',
          hover:   '#1d2939',
          active:  '#1d2939',
          border:  '#1d2939',
          text:    '#98a2b3',
        },

        /* ── Brand blue ── */
        brand: {
          50:  '#eff4ff',
          100: '#d1e0ff',
          200: '#a4bcfd',
          300: '#6d9bf8',
          400: '#4582f5',
          500: '#2356d4',  /* primary */
          600: '#1a47b8',
          700: '#143997',
          800: '#102e7a',
          900: '#0c2261',
        },

        /* ── Neutral (cool grey, slightly blue-tinted) ── */
        neutral: {
          25:  '#fcfcfd',
          50:  '#f9fafb',
          75:  '#f5f7fa',
          100: '#f2f4f7',
          150: '#eaecf0',
          200: '#d0d5dd',
          300: '#98a2b3',
          400: '#667085',
          500: '#475467',
          600: '#344054',
          700: '#1d2939',
          800: '#101828',
          900: '#0c111d',
        },

        /* ── Semantic ── */
        success: { DEFAULT: '#039855', light: '#ecfdf3', border: '#abefc6', text: '#027a48' },
        warning: { DEFAULT: '#dc6803', light: '#fffaeb', border: '#fedf89', text: '#b54708' },
        danger:  { DEFAULT: '#d92d20', light: '#fff1f0', border: '#fecdca', text: '#b42318' },
      },

      fontFamily: {
        sans: ['Inter', 'var(--font-inter)', '-apple-system', 'BlinkMacSystemFont', 'sans-serif'],
        mono: ['"JetBrains Mono"', '"Fira Code"', '"SF Mono"', 'monospace'],
      },

      fontSize: {
        '2xs': ['0.625rem', { lineHeight: '0.875rem' }],
        xs:    ['0.75rem',  { lineHeight: '1.125rem' }],
        sm:    ['0.8125rem',{ lineHeight: '1.25rem'  }],
        base:  ['0.875rem', { lineHeight: '1.375rem' }],
        lg:    ['1rem',     { lineHeight: '1.5rem'   }],
        xl:    ['1.125rem', { lineHeight: '1.625rem' }],
        '2xl': ['1.25rem',  { lineHeight: '1.75rem'  }],
      },

      boxShadow: {
        card:    '0 1px 2px rgba(16,24,40,0.06), 0 1px 3px rgba(16,24,40,0.1)',
        'card-md':'0 4px 6px -2px rgba(16,24,40,0.03), 0 12px 16px -4px rgba(16,24,40,0.08)',
        'card-lg':'0 8px 8px -4px rgba(16,24,40,0.03), 0 20px 24px -4px rgba(16,24,40,0.08)',
      },

      borderRadius: {
        sm:  '4px',
        DEFAULT: '6px',
        md:  '8px',
        lg:  '10px',
        xl:  '12px',
        '2xl':'16px',
      },
    },
  },
  plugins: [],
};

/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        bg:    '#0a0a0b',
        panel: '#131316',
        card:  '#1a1a1f',
        line:  '#26262e',
        muted: '#6b6b78',
        text:  '#e8e8ed',
        blood: '#b91c1c',
        rust:  '#a16207',
        ghost: '#a3a3a3'
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
        mono: ['ui-monospace', 'SFMono-Regular', 'Menlo', 'monospace']
      }
    }
  },
  plugins: []
};

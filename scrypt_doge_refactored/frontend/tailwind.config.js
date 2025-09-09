/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'slate-950': '#020617',
        'emerald-400': '#34d399',
        'rose-500': '#f43f5e',
      },
      borderRadius: {
        'DEFAULT': '6px',
      }
    },
  },
  plugins: [],
  darkMode: 'class',
}
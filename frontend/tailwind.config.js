/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx,ts,tsx}"],
  theme: {
    extend: {
      colors: {
        leaf: {
          50: "#edf9f1",
          100: "#d3f0dc",
          500: "#2f9e5c",
          700: "#1f6b3d",
          900: "#103923"
        }
      },
      boxShadow: {
        soft: "0 12px 28px rgba(16, 57, 35, 0.10)"
      }
    }
  },
  plugins: []
};


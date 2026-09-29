export default {
  content: ["./index.html", "./src/**/*.{vue,js}"],
  theme: {
    extend: {
      fontFamily: { sans: ["Inter", "Cairo", "ui-sans-serif", "system-ui", "sans-serif"] },
      colors: {
        brand: { 50: "#eef4ff", 100: "#dbe6ff", 200: "#bcd0ff", 500: "#2f6bff", 600: "#1f55e6", 700: "#1a45b8", 800: "#163a96" },
      },
    },
  },
  plugins: [],
}

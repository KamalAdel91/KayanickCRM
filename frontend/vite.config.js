import { defineConfig } from "vite"
import vue from "@vitejs/plugin-vue"
import path from "path"

export default defineConfig({
  plugins: [vue()],
  resolve: { alias: { "@": path.resolve(__dirname, "src") } },
  build: { outDir: "../kayanick_crm/public/frontend", emptyOutDir: true, target: "es2015" },
})

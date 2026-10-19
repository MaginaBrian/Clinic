import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

const api = { target: process.env.VITE_API_URL || "http://localhost:8000", changeOrigin: true };

export default defineConfig({
  plugins: [react()],
  server: { proxy: { "/doctors": api, "/appointments": api, "/patients": api } },
});

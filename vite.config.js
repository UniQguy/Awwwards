import { defineConfig } from "vite";
import { resolve } from "path";

export default defineConfig({
  base: "/static/dist/",
  build: {
    manifest: true,
    outDir: resolve(__dirname, "static/dist"),
    emptyOutDir: false,
    rollupOptions: {
      input: {
        main: resolve(__dirname, "frontend/js/main.js"),
        editorial: resolve(__dirname, "frontend/js/editorial.js"),
        styles: resolve(__dirname, "frontend/css/main.css"),
      },
      output: {
        entryFileNames: "js/[name]-[hash].js",
        chunkFileNames: "js/[name]-[hash].js",
        assetFileNames: (assetInfo) => {
          if (assetInfo.name && assetInfo.name.endsWith(".css")) {
            return "css/[name]-[hash][extname]";
          }
          return "assets/[name]-[hash][extname]";
        },
      },
    },
  },
  server: {
    port: 5173,
    origin: "http://localhost:5173",
  },
});

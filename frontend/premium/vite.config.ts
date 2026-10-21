import { defineConfig } from 'vite'

export default defineConfig({
  base: '/assets/centrochange_core/premium/',
  build: {
    outDir: '../../app/centrochange_core/centrochange_core/public/premium',
    emptyOutDir: true,
    rollupOptions: {
      input: 'src/main.tsx',
      output: { entryFileNames: 'app.js', assetFileNames: 'app.[ext]' }
    }
  },
  server: { port: 5182, strictPort: true }
})

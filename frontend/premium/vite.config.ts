import { defineConfig } from 'vite'

export default defineConfig({
  base: '/assets/centrochange_core/premium/',
  oxc: { jsx: { runtime: 'automatic' } },
  build: {
    outDir: '../../app/centrochange_core/centrochange_core/public/premium',
    emptyOutDir: true,
    rollupOptions: {
      input: { app: 'src/main.tsx', public: 'src/public.tsx' },
      output: { entryFileNames: '[name].js', chunkFileNames: '[name]-[hash].js', assetFileNames: 'app.[ext]' }
    }
  },
  server: { port: 5182, strictPort: true }
})

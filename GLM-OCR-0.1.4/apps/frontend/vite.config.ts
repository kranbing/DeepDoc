import { defineConfig, loadEnv } from 'vite'
import { devtools } from '@tanstack/devtools-vite'
import viteReact from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

import { tanstackRouter } from '@tanstack/router-plugin/vite'
import { fileURLToPath, URL } from 'node:url'

// https://vitejs.dev/config/
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  /** GLM-OCR FastAPI（上传 /api/v1/tasks/*），与 apps/backend/Dockerfile 默认 8000 一致，勿与 vLLM 推理端口混用 */
  const proxyTarget = env.VITE_PROXY_TARGET || 'http://127.0.0.1:8000'

  return {
    plugins: [
      devtools(),
      tanstackRouter({
        target: 'react',
        autoCodeSplitting: true,
      }),
      viteReact(),
      tailwindcss(),
    ],
    resolve: {
      alias: {
        '@': fileURLToPath(new URL('./src', import.meta.url)),
      },
    },
    server: {
      // 监听所有地址，方便其他设备访问
      host: '0.0.0.0',
      // 代理后端请求，避免跨域和连接问题
      proxy: {
        '/api': {
          target: proxyTarget,
          changeOrigin: true,
          // 大文件 / 慢速上传：默认代理超时过短易出现 write ECONNABORTED
          timeout: 600_000,
          proxyTimeout: 600_000,
          // 不重写路径，保持 /api/v1/...
          rewrite: (path) => path,
        },
      },
    },
  }
})

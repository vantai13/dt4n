import { fileURLToPath, URL } from 'node:url'
import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'

// ---------------------------------------------------------------------------
// vite.config.js — Cấu hình dev server + PROXY sang Ditto.
//
// VẤN ĐỀ file này giải quyết (xem Lesson 3.2, Phần 2.3):
//   - Browser chạy dashboard ở localhost:5173; Ditto ở localhost:8080.
//     Khác cổng = khác origin -> browser CHẶN request (CORS).
//   - Không muốn nhét user/password Ditto vào code frontend (lộ mật khẩu).
//
// GIẢI PHÁP: proxy. Browser gọi '/ditto/...' (CÙNG origin -> không CORS).
//   Vite âm thầm chuyển tiếp sang Ditto :8080, tự gắn Basic Auth ở tầng server
//   (server-to-server, không bị luật browser ràng buộc). Mật khẩu KHÔNG lọt
//   xuống browser -> đúng pattern "backend-for-frontend" của production.
// ---------------------------------------------------------------------------

export default defineConfig(({ mode }) => {
  // Đọc biến môi trường từ file .env (KHÔNG hardcode host/mật khẩu vào code).
  const env = loadEnv(mode, process.cwd(), '')

  const DITTO_URL  = env.DITTO_URL  || 'http://localhost:8080'
  const DITTO_USER = env.DITTO_USER || 'ditto'
  const DITTO_PASS = env.DITTO_PASSWORD || 'ditto'
  const DITTO_PRE_AUTH = env.DITTO_PRE_AUTH || `nginx:${DITTO_USER}`

  // Tạo chuỗi Basic Auth: "Basic base64(user:pass)". Đây là cách HTTP mã hóa
  // cặp user/pass để gửi trong header Authorization (KHÔNG phải mã hóa bảo mật,
  // chỉ là encode -> vì thế mới cần giấu ở tầng server, không phơi ra browser).
  const basicAuth = 'Basic ' + Buffer.from(`${DITTO_USER}:${DITTO_PASS}`).toString('base64')

  return {
    plugins: [vue()],

    resolve: {
      // Cho phép viết '@/components/...' thay vì đường dẫn tương đối dài dòng.
      alias: { '@': fileURLToPath(new URL('./src', import.meta.url)) },
    },

    server: {
      host: 'localhost',
      port: 5173,

      proxy: {
        // Mọi request browser gửi tới '/ditto/...' sẽ được chuyển tiếp sang Ditto.
        '/ditto': {
          target: DITTO_URL,        // đích thật: http://localhost:8080
          changeOrigin: true,       // sửa header Host cho khớp đích (Ditto cần)
          // Bỏ tiền tố '/ditto' trước khi gửi đi:
          //   browser gọi  /ditto/api/2/search/things
          //   Ditto nhận   /api/2/search/things
          rewrite: (path) => path.replace(/^\/ditto/, ''),
          configure: (proxy) => {
            // Gắn auth ở tầng proxy -> browser không cần biết mật khẩu.
            // Authorization dùng khi đi qua nginx :8080.
            // x-ditto-pre-authenticated dùng được khi trỏ thẳng gateway :8081
            // trong môi trường lab, nơi nginx đang bị lỗi.
            proxy.on('proxyReq', (proxyReq) => {
              proxyReq.setHeader('Authorization', basicAuth)
              proxyReq.setHeader('x-ditto-pre-authenticated', DITTO_PRE_AUTH)
            })
          },
        },
      },
    },
  }
})

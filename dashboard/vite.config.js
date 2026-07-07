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

  // TỰ PHÁT HIỆN chế độ bypass: chỉ khi trỏ THẲNG gateway (cổng 8081) mới gửi
  // x-ditto-pre-authenticated. Khi đi qua nginx (8080), theo Ditto docs client
  // KHÔNG được tự set header đó — nginx là bên DUY NHẤT set nó. Gửi thừa có thể
  // bị nginx từ chối (security hardening coi là giả mạo).
  const isBypass = /:8081(\/|$)/.test(DITTO_URL)

  // Hàm gắn auth đúng theo chế độ -> dùng chung cho cả 2 đường proxy (DRY).
  function attachAuth(proxyReq) {
    if (isBypass) {
      // Bypass gateway :8081 (dev/lab, khi nginx lỗi) -> tự đóng vai nginx.
      proxyReq.setHeader('x-ditto-pre-authenticated', DITTO_PRE_AUTH)
    } else {
      // Chuẩn: qua nginx :8080 -> chỉ gửi Basic Auth, để nginx tự set pre-auth.
      proxyReq.setHeader('Authorization', basicAuth)
    }
  }

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
        // ⚠️ THỨ TỰ QUAN TRỌNG: '/ditto-sse' PHẢI đứng TRƯỚC '/ditto'.
        // Vì Vite khớp proxy theo TIỀN TỐ (startsWith) và dùng cái khớp ĐẦU TIÊN.
        // Chuỗi '/ditto-sse/...' cũng bắt đầu bằng '/ditto', nên nếu '/ditto'
        // đứng trước, nó sẽ NUỐT luôn request SSE -> rewrite sai -> 404 -> OFFLINE.
        // Nguyên tắc: prefix CỤ THỂ hơn (dài hơn) phải xét TRƯỚC prefix tổng quát.

        // === Đường SSE (streaming, kết nối sống lâu, không buffer/timeout) ===
        '/ditto-sse': {
          target: DITTO_URL,
          changeOrigin: true,
          rewrite: (path) => path.replace(/^\/ditto-sse/, ''),
          timeout: 0,
          proxyTimeout: 0,
          configure: (proxy) => {
            proxy.on('proxyReq', (proxyReq) => {
              attachAuth(proxyReq)
              proxyReq.setHeader('X-Accel-Buffering', 'no')   // nginx đừng đệm SSE
              proxyReq.setHeader('Cache-Control', 'no-cache')
            })
          },
        },

        // === Đường request THƯỜNG (fetch, Search API) ===
        '/ditto': {
          target: DITTO_URL,        // đích thật (nginx :8080, hoặc gateway :8081 khi bypass)
          changeOrigin: true,       // sửa header Host cho khớp đích
          rewrite: (path) => path.replace(/^\/ditto/, ''),
          configure: (proxy) => {
            proxy.on('proxyReq', (proxyReq) => {
              attachAuth(proxyReq)
            })
          },
        },
      },
    },
  }
})
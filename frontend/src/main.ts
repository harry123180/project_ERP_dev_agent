import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import 'element-plus/theme-chalk/dark/css-vars.css'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'
import zhTw from './locale/zh-tw'

import App from './App.vue'
import router from './router'
import './styles/index.scss'
import { useAuthStore } from '@/stores/auth'

const app = createApp(App)

// Use Pinia for state management
const pinia = createPinia()
app.use(pinia)

// Initialize authentication state from localStorage
const authStore = useAuthStore()
authStore.initializeAuth()

// Use Vue Router
app.use(router)

// Use Element Plus with Traditional Chinese locale
app.use(ElementPlus, {
  locale: zhTw
})

// Register all Element Plus icons
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component)
}

app.mount('#app')
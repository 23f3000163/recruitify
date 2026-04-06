import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import './styles/theme.css'
import './main.css'
import './auth.css'

createApp(App).use(router).mount('#app')

if (import.meta.env.PROD && 'serviceWorker' in navigator) {
	window.addEventListener('load', () => {
		navigator.serviceWorker.register('/sw.js').catch(() => {
			// Fail open: app must continue to work even if service worker registration fails.
		})
	})
}
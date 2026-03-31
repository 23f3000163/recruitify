<template>
<footer>

  <!-- Newsletter row -->
  <div class="footer-newsletter">
    <div class="fn-inner">
      <div class="fn-text">
        <h4>Get notified about new drives</h4>
        <p>We'll alert you when new companies are verified and drives go live.</p>
      </div>
      <div class="fn-form">
        <input class="fn-input" type="email" placeholder="your@email.com"/>
        <button class="fn-btn">Subscribe</button>
      </div>
    </div>
  </div>

  <!-- 5-column grid -->
  <div class="footer-grid">

    <!-- Brand column -->
    <div>
      <div class="fb-brand">
        <div class="fb-logo-mark">
          <svg width="16" height="16" viewBox="0 0 18 18" fill="none">
            <path d="M3 14L9 4L15 14" stroke="rgba(255,255,255,.65)" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>
            <path d="M5.5 10.5h7" stroke="rgba(255,255,255,.65)" stroke-width="2.5" stroke-linecap="round"/>
          </svg>
        </div>
        <span class="fb-name">Recruitify</span>
      </div>
      <p class="fb-desc">The complete campus placement management platform — structured, transparent, and built for how placements actually work. MAD-II Project.</p>
      <div class="fb-built">
        <span class="fb-built-label">Built with</span>
        <span class="fb-chip">Flask</span>
        <span class="fb-chip">Vue.js</span>
        <span class="fb-chip">Redis</span>
        <span class="fb-chip">Celery</span>
        <span class="fb-chip">SQLite</span>
      </div>
      <div class="fb-social">
        <a class="fb-social-btn" href="#" @click.prevent>G</a>
        <a class="fb-social-btn" href="#" @click.prevent>in</a>
        <a class="fb-social-btn" href="#" @click.prevent>gh</a>
      </div>
    </div>

    <div>
      <div class="footer-col-title">Platform</div>
      <ul class="footer-links">
        <li><a href="#" @click.prevent>How It Works</a></li>
        <li><a href="#" @click.prevent>Features</a></li>
        <li><a href="#" @click.prevent>Tech Stack</a></li>
        <li><a href="#" @click.prevent>Changelog</a></li>
        <li><a href="#" @click.prevent>API Docs</a></li>
      </ul>
    </div>

    <div>
      <div class="footer-col-title">Students</div>
      <ul class="footer-links">
        <li><a href="/register/student" @click.prevent="go('/register/student')">Register</a></li>
        <li><a href="/login" @click.prevent="go('/login')">Login</a></li>
        <li><a href="#" @click.prevent>Browse Drives</a></li>
        <li><a href="#" @click.prevent>Track Status</a></li>
        <li><a href="#" @click.prevent>Resume Tips</a></li>
      </ul>
    </div>

    <div>
      <div class="footer-col-title">Companies</div>
      <ul class="footer-links">
        <li><a href="/register/company" @click.prevent="go('/register/company')">Register</a></li>
        <li><a href="#" @click.prevent>Verification</a></li>
        <li><a href="#" @click.prevent>Post a Drive</a></li>
        <li><a href="#" @click.prevent>HR Dashboard</a></li>
        <li><a href="#" @click.prevent>Support</a></li>
      </ul>
    </div>

    <div>
      <div class="footer-col-title">Legal</div>
      <ul class="footer-links">
        <li><a href="#" @click.prevent>Privacy Policy</a></li>
        <li><a href="#" @click.prevent>Terms of Use</a></li>
        <li><a href="#" @click.prevent>Cookie Policy</a></li>
        <li><a href="#" @click.prevent>Contact</a></li>
        <li><a href="#" @click.prevent>Report Issue</a></li>
      </ul>
    </div>

  </div>

  <!-- Bottom bar -->
  <div class="footer-bottom">
    <div class="fb-copy">© 2025 Recruitify · MAD-II Project · Modern Application Development II</div>
    <div class="fb-status">
      <div class="fb-status-dot"></div>
      All systems operational
    </div>
    <ul class="fb-bottom-links">
      <li><a href="#" @click.prevent>Privacy</a></li>
      <li><a href="#" @click.prevent>Terms</a></li>
      <li><a href="#" @click.prevent>Support</a></li>
    </ul>
  </div>

</footer>
</template>

<script setup>
import { useRouter } from 'vue-router'

const router = useRouter()
const go = (path) => router.push(path)
</script>

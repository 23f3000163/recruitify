<template>
  <div
    class="landing-view"
    :style="{ '--mx': mouseX + 'px', '--my': mouseY + 'px' }"
  >
    <div class="cursor-glow"></div>
    <div class="scroll-bar" :style="{ width: scrollProgress + '%' }"></div>

    <Navbar :scrolled="isNavbarScrolled" />
    <HeroSection />


<!-- ══════════════════════════════════════════════
     DUAL MARQUEE
══════════════════════════════════════════════ -->
<div class="marquee-wrap">
  <div class="marquee-label">Admin-Verified Hiring Partners</div>

  <div class="marquee-row">
    <div class="marquee-track mq-fwd">
      <div class="mq-item"><div class="mq-dot" style="background:#4285F4"></div>Google</div>
      <div class="mq-item"><div class="mq-dot" style="background:#00A4EF"></div>Microsoft</div>
      <div class="mq-item"><div class="mq-dot" style="background:#FF9900"></div>Amazon</div>
      <div class="mq-item"><div class="mq-dot" style="background:#0052CC"></div>Infosys</div>
      <div class="mq-item"><div class="mq-dot" style="background:#1A9FE0"></div>TCS</div>
      <div class="mq-item"><div class="mq-dot" style="background:#5F32A7"></div>Wipro</div>
      <div class="mq-item"><div class="mq-dot" style="background:#A100FF"></div>Accenture</div>
      <div class="mq-item"><div class="mq-dot" style="background:#86BC25"></div>Deloitte</div>
      <div class="mq-item"><div class="mq-dot" style="background:#006CB7"></div>IBM</div>
      <div class="mq-item"><div class="mq-dot" style="background:#0F6CBD"></div>Cognizant</div>
      <!-- Duplicate for seamless loop -->
      <div class="mq-item"><div class="mq-dot" style="background:#4285F4"></div>Google</div>
      <div class="mq-item"><div class="mq-dot" style="background:#00A4EF"></div>Microsoft</div>
      <div class="mq-item"><div class="mq-dot" style="background:#FF9900"></div>Amazon</div>
      <div class="mq-item"><div class="mq-dot" style="background:#0052CC"></div>Infosys</div>
      <div class="mq-item"><div class="mq-dot" style="background:#1A9FE0"></div>TCS</div>
      <div class="mq-item"><div class="mq-dot" style="background:#5F32A7"></div>Wipro</div>
      <div class="mq-item"><div class="mq-dot" style="background:#A100FF"></div>Accenture</div>
      <div class="mq-item"><div class="mq-dot" style="background:#86BC25"></div>Deloitte</div>
      <div class="mq-item"><div class="mq-dot" style="background:#006CB7"></div>IBM</div>
      <div class="mq-item"><div class="mq-dot" style="background:#0F6CBD"></div>Cognizant</div>
    </div>
  </div>

  <div class="marquee-row">
    <div class="marquee-track mq-rev">
      <div class="mq-item"><div class="mq-dot" style="background:#E31837"></div>Razorpay</div>
      <div class="mq-item"><div class="mq-dot" style="background:#00B4D8"></div>Flipkart</div>
      <div class="mq-item"><div class="mq-dot" style="background:#00BAF2"></div>Paytm</div>
      <div class="mq-item"><div class="mq-dot" style="background:#1DB954"></div>CRED</div>
      <div class="mq-item"><div class="mq-dot" style="background:#FC8019"></div>Swiggy</div>
      <div class="mq-item"><div class="mq-dot" style="background:#E53935"></div>Zomato</div>
      <div class="mq-item"><div class="mq-dot" style="background:#5F259F"></div>PhonePe</div>
      <div class="mq-item"><div class="mq-dot" style="background:#00A1E4"></div>Salesforce</div>
      <div class="mq-item"><div class="mq-dot" style="background:#E31837"></div>Razorpay</div>
      <div class="mq-item"><div class="mq-dot" style="background:#00B4D8"></div>Flipkart</div>
      <div class="mq-item"><div class="mq-dot" style="background:#00BAF2"></div>Paytm</div>
      <div class="mq-item"><div class="mq-dot" style="background:#1DB954"></div>CRED</div>
      <div class="mq-item"><div class="mq-dot" style="background:#FC8019"></div>Swiggy</div>
      <div class="mq-item"><div class="mq-dot" style="background:#E53935"></div>Zomato</div>
      <div class="mq-item"><div class="mq-dot" style="background:#5F259F"></div>PhonePe</div>
      <div class="mq-item"><div class="mq-dot" style="background:#00A1E4"></div>Salesforce</div>
    </div>
  </div>
</div>

<!-- ══════════════════════════════════════════════
     STATS
══════════════════════════════════════════════ -->
<div class="stats-section" id="statsSection" ref="statsSection">
  <div class="stats-grid">
    <div class="stat-cell">
      <div class="stat-num s-green"><span class="counter">{{ counters[0].value }}</span><span class="stat-suf">+</span></div>
      <div class="stat-label">Placements Confirmed</div>
      <div class="stat-delta">Across verified placement records</div>
    </div>
    <div class="stat-cell">
      <div class="stat-num s-blue"><span class="counter">{{ counters[1].value }}</span><span class="stat-suf">+</span></div>
      <div class="stat-label">Approved Companies</div>
      <div class="stat-delta">Actively hiring through Recruitify</div>
    </div>
    <div class="stat-cell">
      <div class="stat-num"><span class="counter">{{ counters[2].value }}</span><span class="stat-suf">+</span></div>
      <div class="stat-label">Approved Drives</div>
      <div class="stat-delta">Open and recently completed opportunities</div>
    </div>
    <div class="stat-cell">
      <div class="stat-num"><span class="counter">{{ counters[3].value }}</span><span class="stat-suf">+</span></div>
      <div class="stat-label">Latest Month Placements</div>
      <div class="stat-delta">Generated from public monthly trend data</div>
    </div>
  </div>
</div>

<!-- ══════════════════════════════════════════════
     WHO IS THIS FOR
══════════════════════════════════════════════ -->
<section class="section" id="who">
  <div class="s-inner">
    <div class="s-eyebrow reveal" v-reveal>Who Is This For</div>
    <h2 class="s-h reveal" v-reveal>Built for every stakeholder<br><em>in the placement process.</em></h2>
    <p class="s-p reveal" v-reveal>Three completely separate, role-scoped experiences on one platform — each designed around a specific user's exact workflow and responsibilities.</p>

    <div class="who-grid">

      <!-- Student -->
      <div class="who-card reveal reveal-d1" v-reveal>
        <div class="wc-icon">👨‍🎓</div>
        <div class="wc-title">Students</div>
        <div class="wc-sub">Self-register, browse, apply, and track</div>
        <ul class="wc-list">
          <li class="wc-li"><div class="wc-check ck-b">✓</div>See only drives you qualify for — CGPA, branch, year auto-checked at the API level</li>
          <li class="wc-li"><div class="wc-check ck-b">✓</div>One-click apply with database-level duplicate application prevention</li>
          <li class="wc-li"><div class="wc-check ck-b">✓</div>Track every application: Applied → Shortlisted → Interview → Selected</li>
          <li class="wc-li"><div class="wc-check ck-b">✓</div>Get notified at every status change — automatically</li>
          <li class="wc-li"><div class="wc-check ck-b">✓</div>Upload resume, view placement history, download offer letters</li>
        </ul>
        <div class="wc-cta">
          <a href="/register/student" class="wc-link" @click.prevent="go('/register/student')">Register as Student →</a>
          <span class="wc-count">500+ placed</span>
        </div>
      </div>

      <!-- Company -->
      <div class="who-card reveal reveal-d2" v-reveal>
        <div class="wc-icon">🏢</div>
        <div class="wc-title">Companies</div>
        <div class="wc-sub">Post drives, review applicants, hire talent</div>
        <ul class="wc-list">
          <li class="wc-li"><div class="wc-check ck-g">✓</div>Register HR profile and get admin-verified before accessing any student data</li>
          <li class="wc-li"><div class="wc-check ck-g">✓</div>Post drives with full eligibility criteria, salary, and application deadline</li>
          <li class="wc-li"><div class="wc-check ck-g">✓</div>View only pre-screened, eligible applicants for each drive</li>
          <li class="wc-li"><div class="wc-check ck-g">✓</div>Shortlist, schedule interviews, and issue selections in one smooth flow</li>
          <li class="wc-li"><div class="wc-check ck-g">✓</div>Manage drive status (Active/Closed) and view application analytics</li>
        </ul>
        <div class="wc-cta">
          <a href="/register/company" class="wc-link" @click.prevent="go('/register/company')">Register Company →</a>
          <span class="wc-count">80+ companies</span>
        </div>
      </div>

      <!-- Admin -->
      <div class="who-card reveal reveal-d3" v-reveal>
        <div class="wc-icon">🛡</div>
        <div class="wc-title">Admin (TPO)</div>
        <div class="wc-sub">Full system control, pre-created account</div>
        <ul class="wc-list">
          <li class="wc-li"><div class="wc-check ck-i">✓</div>Pre-created secure login — no registration page for the admin role</li>
          <li class="wc-li"><div class="wc-check ck-i">✓</div>Approve or reject every company and every drive before it goes live</li>
          <li class="wc-li"><div class="wc-check ck-i">✓</div>Search students and companies by name, roll number, or contact</li>
          <li class="wc-li"><div class="wc-check ck-i">✓</div>Blacklist or deactivate any user with reason logging and notifications</li>
          <li class="wc-li"><div class="wc-check ck-i">✓</div>Full analytics, CSV exports, and a complete activity audit trail</li>
        </ul>
        <div class="wc-cta">
          <a href="/login" class="wc-link" @click.prevent="go('/login')">Admin Login →</a>
          <span class="wc-count">Full system access</span>
        </div>
      </div>

    </div>
  </div>
</section>

<!-- SVG connector -->
<div class="svg-connector">
  <svg viewBox="0 0 160 50" fill="none" xmlns="http://www.w3.org/2000/svg">
    <path d="M80 0 C80 20 50 30 50 50" stroke="rgba(37,99,235,.4)" stroke-width="1" stroke-dasharray="4 4"/>
    <path d="M80 0 C80 20 110 30 110 50" stroke="rgba(5,150,105,.4)" stroke-width="1" stroke-dasharray="4 4"/>
    <circle cx="80" cy="0" r="3" fill="rgba(37,99,235,.4)"/>
  </svg>
</div>

<!-- ══════════════════════════════════════════════
     ROLE TOGGLE DEMO
══════════════════════════════════════════════ -->
<section class="section-alt">
  <div class="s-inner">
    <div class="s-eyebrow reveal" v-reveal>Interactive Demo</div>
    <h2 class="s-h reveal" v-reveal>See each dashboard<br><em>before you register.</em></h2>

    <div class="demo-tabs reveal" v-reveal>
      <button class="demo-tab" :class="{ active: demoRole === 'student' }" @click="demoRole = 'student'">👨‍🎓 Student View</button>
      <button class="demo-tab" :class="{ active: demoRole === 'company' }" @click="demoRole = 'company'">🏢 Company View</button>
      <button class="demo-tab" :class="{ active: demoRole === 'admin' }" @click="demoRole = 'admin'">🛡 Admin View</button>
    </div>

    <div class="demo-panels">

      <!-- Student -->
      <div class="demo-panel" :class="{ active: demoRole === 'student' }" id="dpanel-student">
        <div class="reveal-l" v-reveal>
          <h3 class="dp-title">Student Dashboard</h3>
          <p class="dp-desc">A personalized view showing only the drives you qualify for, real-time application tracking, interview schedule, and your complete placement history — all in one clean, role-scoped dashboard.</p>
          <div class="dp-features">
            <div class="dp-feat"><div class="dp-feat-icon">🎯</div>Auto-filtered eligible drives only</div>
            <div class="dp-feat"><div class="dp-feat-icon">📋</div>Full status pipeline: Applied → Placed</div>
            <div class="dp-feat"><div class="dp-feat-icon">🔔</div>Real-time in-app notifications</div>
            <div class="dp-feat"><div class="dp-feat-icon">📊</div>Personal placement statistics</div>
          </div>
        </div>
        <div class="dp-visual reveal-r" v-reveal>
          <div class="dpv-head">📊 My Applications</div>
          <div class="dpv-body">
            <div class="dpv-row"><span>Google — SWE Intern</span><span class="dpv-badge" style="background:var(--green-lt);color:var(--green);border:1px solid rgba(5,150,105,.2)">Offer Received 🎉</span></div>
            <div class="dpv-row"><span>Microsoft — Product Analyst</span><span class="dpv-badge" style="background:#F5F3FF;color:#7C3AED;border:1px solid rgba(124,58,237,.2)">Interviewing</span></div>
            <div class="dpv-row"><span>Amazon — Cloud Engineer</span><span class="dpv-badge" style="background:var(--amber-lt);color:var(--amber);border:1px solid rgba(217,119,6,.2)">Shortlisted</span></div>
            <div class="dpv-row"><span>Infosys — Systems Engineer</span><span class="dpv-badge" style="background:var(--blue-lt);color:var(--blue);border:1px solid var(--border-b)">Applied</span></div>
          </div>
        </div>
      </div>

      <!-- Company -->
      <div class="demo-panel" :class="{ active: demoRole === 'company' }" id="dpanel-company">
        <div>
          <h3 class="dp-title">Company Dashboard</h3>
          <p class="dp-desc">A complete recruitment console — post drives with eligibility criteria, review pre-screened applicants, shortlist, schedule interviews, and track hiring progress end-to-end.</p>
          <div class="dp-features">
            <div class="dp-feat"><div class="dp-feat-icon">📝</div>Create drives with full eligibility settings</div>
            <div class="dp-feat"><div class="dp-feat-icon">👥</div>View only pre-screened eligible applicants</div>
            <div class="dp-feat"><div class="dp-feat-icon">⚡</div>Shortlist, interview, select — one flow</div>
            <div class="dp-feat"><div class="dp-feat-icon">📈</div>Drive analytics and application funnel</div>
          </div>
        </div>
        <div class="dp-visual">
          <div class="dpv-head">💼 Drive Applicants — SWE Intern</div>
          <div class="dpv-body">
            <div class="dpv-row"><span>Rahul Sharma · CGPA 9.2</span><span class="dpv-badge" style="background:var(--amber-lt);color:var(--amber);border:1px solid rgba(217,119,6,.2)">Shortlisted</span></div>
            <div class="dpv-row"><span>Ananya Iyer · CGPA 8.7</span><span class="dpv-badge" style="background:#F5F3FF;color:#7C3AED;border:1px solid rgba(124,58,237,.2)">Interview Set</span></div>
            <div class="dpv-row"><span>Priya Sharma · CGPA 9.1</span><span class="dpv-badge" style="background:var(--green-lt);color:var(--green);border:1px solid rgba(5,150,105,.2)">Selected ✓</span></div>
            <div class="dpv-row"><span>Arjun Mehta · CGPA 8.1</span><span class="dpv-badge" style="background:var(--blue-lt);color:var(--blue);border:1px solid var(--border-b)">Under Review</span></div>
          </div>
        </div>
      </div>

      <!-- Admin -->
      <div class="demo-panel" :class="{ active: demoRole === 'admin' }" id="dpanel-admin">
        <div>
          <h3 class="dp-title">Admin Dashboard</h3>
          <p class="dp-desc">The TPO's complete control centre — system-wide placement statistics, pending approvals, user management, blacklist controls, and a full audit log of every action taken on the platform.</p>
          <div class="dp-features">
            <div class="dp-feat"><div class="dp-feat-icon">🏢</div>Approve / reject companies and drives</div>
            <div class="dp-feat"><div class="dp-feat-icon">📊</div>System-wide placement analytics</div>
            <div class="dp-feat"><div class="dp-feat-icon">🚫</div>Blacklist and deactivate users</div>
            <div class="dp-feat"><div class="dp-feat-icon">📁</div>CSV exports and monthly reports</div>
          </div>
        </div>
        <div class="dp-visual">
          <div class="dpv-head">🛡 Pending Approvals</div>
          <div class="dpv-body">
            <div class="dpv-row"><span>Flipkart — Company Registration</span><span class="dpv-badge" style="background:var(--amber-lt);color:var(--amber);border:1px solid rgba(217,119,6,.2)">⏳ Pending</span></div>
            <div class="dpv-row"><span>Razorpay — Drive: SDE-II</span><span class="dpv-badge" style="background:var(--amber-lt);color:var(--amber);border:1px solid rgba(217,119,6,.2)">⏳ Pending</span></div>
            <div class="dpv-row"><span>CRED — Company Registration</span><span class="dpv-badge" style="background:var(--green-lt);color:var(--green);border:1px solid rgba(5,150,105,.2)">✓ Approved</span></div>
            <div class="dpv-row"><span>Paytm — Drive: Data Analyst</span><span class="dpv-badge" style="background:var(--red-lt);color:var(--red);border:1px solid rgba(220,38,38,.2)">✗ Rejected</span></div>
          </div>
        </div>
      </div>

    </div>
  </div>
</section>

<!-- ══════════════════════════════════════════════
     BEFORE / AFTER
══════════════════════════════════════════════ -->
<section class="section">
  <div class="s-inner">
    <div class="center-text">
      <div class="s-eyebrow reveal" v-reveal>The Difference</div>
      <h2 class="s-h reveal" v-reveal>Before Recruitify vs <em>After.</em></h2>
    </div>

    <div class="ba-grid reveal" v-reveal>
      <div class="ba-col ba-before">
        <div class="ba-head before">
          <div class="ba-head-icon">😰</div>
          <div class="ba-head-title">Without Recruitify</div>
        </div>
        <div class="ba-item bad"><span class="ba-x">✗</span><div class="ba-text"><strong>Email chaos</strong>Drives sent by email. Students miss deadlines. TPO chases everyone manually.</div></div>
        <div class="ba-item bad"><span class="ba-x">✗</span><div class="ba-text"><strong>Spreadsheet hell</strong>Applications tracked in Excel. No real-time updates. Errors everywhere.</div></div>
        <div class="ba-item bad"><span class="ba-x">✗</span><div class="ba-text"><strong>No eligibility check</strong>Students apply to drives they can't qualify for. Companies waste time reviewing.</div></div>
        <div class="ba-item bad"><span class="ba-x">✗</span><div class="ba-text"><strong>Unverified companies</strong>Any company can contact students. No vetting. A potential safety risk.</div></div>
        <div class="ba-item bad"><span class="ba-x">✗</span><div class="ba-text"><strong>Zero transparency</strong>Students have no idea where their application stands. No updates at all.</div></div>
      </div>
      <div class="ba-divider"><div class="ba-vs-label">vs</div></div>
      <div class="ba-col ba-after">
        <div class="ba-head after">
          <div class="ba-head-icon">✅</div>
          <div class="ba-head-title">With Recruitify</div>
        </div>
        <div class="ba-item good"><span class="ba-chk">✓</span><div class="ba-text"><strong>Structured portal</strong>All drives in one place. Deadlines visible. One-click apply. Zero missed chances.</div></div>
        <div class="ba-item good"><span class="ba-chk">✓</span><div class="ba-text"><strong>Real-time database</strong>Every application tracked live. Status updates instant. Always accurate.</div></div>
        <div class="ba-item good"><span class="ba-chk">✓</span><div class="ba-text"><strong>Auto eligibility</strong>Students only see drives they qualify for. Enforced at the API level, every request.</div></div>
        <div class="ba-item good"><span class="ba-chk">✓</span><div class="ba-text"><strong>Admin-verified only</strong>Every company manually approved before interacting with any student data.</div></div>
        <div class="ba-item good"><span class="ba-chk">✓</span><div class="ba-text"><strong>Full transparency</strong>Applied → Shortlisted → Interview → Offer → Placed. Students notified every step.</div></div>
      </div>
    </div>
  </div>
</section>

<!-- ══════════════════════════════════════════════
     FEATURES BENTO
══════════════════════════════════════════════ -->
<section class="section-alt" id="features">
  <div class="s-inner">
    <div class="s-eyebrow reveal" v-reveal>Features</div>
    <h2 class="s-h reveal" v-reveal>Built around real placement<br><em>workflows, not assumptions.</em></h2>
    <p class="s-p reveal" v-reveal>Every feature derives from the actual pain points of students, company HR teams, and placement officers — not guesswork.</p>

    <div class="feat-bento reveal" v-reveal>

      <div class="feat-cell f-span3 f-tint">
        <div class="feat-icon">🔐</div>
        <div class="feat-title">Role-Based Access Control</div>
        <p class="feat-desc">Admin, Company, and Student each get completely separate dashboards. Permissions enforced at every API endpoint via JWT token decorators — @student_required, @company_required, @admin_required. A student can never see company data.</p>
        <div class="feat-tags">
          <span class="feat-tag">@student_required</span>
          <span class="feat-tag">@company_required</span>
          <span class="feat-tag">@admin_required</span>
          <span class="feat-tag">JWT · PyJWT</span>
        </div>
      </div>

      <div class="feat-cell f-span3">
        <div class="feat-icon">✅</div>
        <div class="feat-title">Automatic Eligibility Filtering</div>
        <p class="feat-desc">Every drive has a CGPA cutoff, eligible_branches (JSON list), and eligible_years (JSON list). All three conditions are checked server-side before returning drives or accepting an application. Cannot be bypassed from the frontend.</p>
        <div class="feat-tags">
          <span class="feat-tag">CGPA check</span>
          <span class="feat-tag">JSON branch filter</span>
          <span class="feat-tag">Year filter</span>
          <span class="feat-tag">Duplicate prevention</span>
        </div>
      </div>

      <div class="feat-cell f-span2">
        <div class="feat-icon">🏢</div>
        <div class="feat-title">Company Verification</div>
        <p class="feat-desc">approval_status enum: pending → approved → rejected. Admin manually approves each company before they can post any drive or view any student data.</p>
      </div>

      <div class="feat-cell f-span2">
        <div class="feat-icon">📊</div>
        <div class="feat-title">Live Placement Analytics</div>
        <p class="feat-desc">Real-time stats: total placed, by branch, by company. Application funnels, average package, highest offer — all on the admin dashboard.</p>
      </div>

      <div class="feat-cell f-span2">
        <div class="feat-icon">🔔</div>
        <div class="feat-title">Smart Notifications</div>
        <p class="feat-desc">Automatic in-app notifications at every status change — shortlisted, interview scheduled, selected, rejected. No manual updates ever needed.</p>
      </div>

      <div class="feat-cell f-span4 f-dark">
        <div class="feat-icon">⚡</div>
        <div class="feat-title">Background Jobs — Celery + Redis</div>
        <p class="feat-desc">Three automated jobs: daily interview reminders via Celery Beat, monthly HTML/PDF placement reports auto-generated on the 1st of each month, and user-triggered async CSV export that runs in the background — user notified via in-app notification when ready.</p>
        <div class="feat-tags">
          <span class="feat-tag">Celery Beat</span>
          <span class="feat-tag">Redis broker</span>
          <span class="feat-tag">Async CSV export</span>
          <span class="feat-tag">crontab scheduling</span>
        </div>
      </div>

      <div class="feat-cell f-span2">
        <div class="feat-icon">🗄</div>
        <div class="feat-title">Redis Caching</div>
        <p class="feat-desc">Drives list, admin stats, and user profiles cached with configurable TTL. Cache auto-invalidated on data change. Dramatically reduces DB load and response time.</p>
        <div class="feat-tags">
          <span class="feat-tag">TTL: 1 hour</span>
          <span class="feat-tag">Auto invalidation</span>
        </div>
      </div>

    </div>
  </div>
</section>

<!-- ══════════════════════════════════════════════
     APPLICATION PIPELINE TIMELINE
══════════════════════════════════════════════ -->
<section class="section" id="pipeline">
  <div class="s-inner">
    <div class="s-eyebrow reveal" v-reveal>Application Journey</div>
    <h2 class="s-h reveal" v-reveal>Every stage tracked,<br><em>nothing lost.</em></h2>
    <p class="s-p reveal" v-reveal>From the moment a student applies to the final placement confirmation — every status is recorded, timestamped, and visible in real time to the student, company, and admin.</p>

    <div class="pipe-track" id="pipelineTrack" ref="pipelineTrack">
      <div class="pipe-progress" id="pipelineProgress" :class="{ go: pipelineProgressGo }"></div>
      <div class="pipe-stages">
        <div class="pipe-stage">
          <div class="pipe-icon done">📝</div>
          <div class="pipe-stage-label">Applied</div>
          <div class="pipe-stage-count">{{ funnelCountLabel(publicFunnel.applied) }}</div>
        </div>
        <div class="pipe-stage">
          <div class="pipe-icon done">👁</div>
          <div class="pipe-stage-label">Under Review</div>
          <div class="pipe-stage-count">{{ funnelCountLabel(publicFunnel.shortlisted) }}</div>
        </div>
        <div class="pipe-stage">
          <div class="pipe-icon active">⭐</div>
          <div class="pipe-stage-label">Shortlisted</div>
          <div class="pipe-stage-count">{{ funnelCountLabel(publicFunnel.interview) }}</div>
        </div>
        <div class="pipe-stage">
          <div class="pipe-icon">🎤</div>
          <div class="pipe-stage-label">Interviewed</div>
          <div class="pipe-stage-count">{{ funnelCountLabel(publicFunnel.offered) }}</div>
        </div>
        <div class="pipe-stage">
          <div class="pipe-icon">🎉</div>
          <div class="pipe-stage-label">Placed</div>
          <div class="pipe-stage-count">{{ funnelCountLabel(publicFunnel.placed) }}</div>
        </div>
      </div>
    </div>
  </div>
</section>

<!-- ══════════════════════════════════════════════
     TECH STACK
══════════════════════════════════════════════ -->
<section class="section-alt">
  <div class="s-inner">
    <div class="center-text">
      <div class="s-eyebrow reveal" v-reveal>Tech Stack</div>
      <h2 class="s-h reveal" v-reveal>Built with <em>battle-tested</em> technology.</h2>
    </div>
    <div class="tech-grid reveal" v-reveal>
      <div class="tech-item"><div class="tech-emoji">🐍</div><div class="tech-name">Flask 3.0</div><div class="tech-role">Backend API</div></div>
      <div class="tech-item"><div class="tech-emoji">💚</div><div class="tech-name">Vue.js 3</div><div class="tech-role">Frontend SPA</div></div>
      <div class="tech-item"><div class="tech-emoji">🗃</div><div class="tech-name">SQLAlchemy</div><div class="tech-role">ORM + SQLite</div></div>
      <div class="tech-item"><div class="tech-emoji">🔴</div><div class="tech-name">Redis</div><div class="tech-role">Cache + Broker</div></div>
      <div class="tech-item"><div class="tech-emoji">⚙️</div><div class="tech-name">Celery</div><div class="tech-role">Background Jobs</div></div>
      <div class="tech-item"><div class="tech-emoji">🔑</div><div class="tech-name">JWT</div><div class="tech-role">Authentication</div></div>
      <div class="tech-item"><div class="tech-emoji">⚡</div><div class="tech-name">Vite 5</div><div class="tech-role">Build Tool</div></div>
      <div class="tech-item"><div class="tech-emoji">🎨</div><div class="tech-name">Bootstrap 5</div><div class="tech-role">UI Framework</div></div>
    </div>
  </div>
</section>

<!-- ══════════════════════════════════════════════
     TESTIMONIALS
══════════════════════════════════════════════ -->
<section class="section">
  <div class="s-inner">
    <div class="s-eyebrow reveal" v-reveal>Testimonials</div>
    <h2 class="s-h reveal" v-reveal>What students, companies,<br><em>and admins say.</em></h2>

    <div class="testi-grid">
      <div class="testi-card reveal reveal-d1" v-reveal>
        <div class="testi-stars">★★★★★</div>
        <p class="testi-quote">"The auto-eligibility filter changed everything. I only saw drives I could actually apply for — no irrelevant listings, no wasted time. Got placed at Google in under 3 weeks."</p>
        <div class="testi-author">
          <div class="testi-av" style="background:linear-gradient(135deg,#2563EB,#1D4ED8)">JS</div>
          <div>
            <div class="testi-name">Jayesh Singh</div>
            <div class="testi-role">CSE Year 4 · Placed at Google, ₹42 LPA</div>
          </div>
        </div>
      </div>

      <div class="testi-card reveal reveal-d2" v-reveal>
        <div class="testi-stars">★★★★★</div>
        <p class="testi-quote">"Managing 300+ applications across 4 drives used to take our HR team a full week. With Recruitify, it's a morning's work. The shortlisting interface is excellent."</p>
        <div class="testi-author">
          <div class="testi-av" style="background:linear-gradient(135deg,#059669,#047857)">MR</div>
          <div>
            <div class="testi-name">Meera Rajan</div>
            <div class="testi-role">HR Lead · Microsoft India</div>
          </div>
        </div>
      </div>

      <div class="testi-card reveal reveal-d3" v-reveal>
        <div class="testi-stars">★★★★★</div>
        <p class="testi-quote">"Company approvals, drive management, blacklist controls, full analytics, CSV exports — all in one dashboard. This is exactly what a placement portal should be."</p>
        <div class="testi-author">
          <div class="testi-av" style="background:linear-gradient(135deg,#D97706,#B45309)">PK</div>
          <div>
            <div class="testi-name">Prof. P. Kumar</div>
            <div class="testi-role">Training & Placement Officer</div>
          </div>
        </div>
      </div>
    </div>
  </div>
</section>

<!-- ══════════════════════════════════════════════
     CTA
══════════════════════════════════════════════ -->
<section class="section-alt">
  <div class="s-inner">
    <div class="cta-box reveal" v-reveal>
      <h2 class="cta-title">Ready to run placements<br>the <em>right way?</em></h2>
      <p class="cta-sub">Join the students, companies, and administrators who trust Recruitify for a placement process that is structured, transparent, and fully tracked from application to offer.</p>
      <div class="cta-buttons">
        <a href="/register/student" class="btn-cta-white" @click.prevent="go('/register/student')">
          Get Started as Student →
        </a>
        <a href="/register/company" class="btn-cta-ghost" @click.prevent="go('/register/company')">Register Company</a>
      </div>
      <div class="cta-checks">
        <span class="cta-check">Admin-verified companies</span>
        <span class="cta-check">Auto eligibility check</span>
        <span class="cta-check">Real-time tracking</span>
        <span class="cta-check">Interview scheduling</span>
        <span class="cta-check">CSV exports</span>
        <span class="cta-check">Full audit trail</span>
      </div>
    </div>
  </div>
</section>

<!-- ══════════════════════════════════════════════
     FOOTER
══════════════════════════════════════════════ -->

    <Footer />

    <button class="scroll-top-btn" :class="{ visible: showScrollTop }" @click="scrollTop">
      <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
        <path d="M4 10l4-4 4 4" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
      </svg>
    </button>
  </div>
</template>

<script>
import Navbar from '../components/layout/Navbar.vue'
import Footer from '../components/layout/Footer.vue'
import HeroSection from '../components/landing/HeroSection.vue'
import { adminApi } from '../api/api'

function createEmptyPublicDashboard() {
  return {
    highlights: {
      total_students: 0,
      approved_companies: 0,
      approved_drives: 0,
      placements_confirmed: 0,
      latest_month_placements: 0
    },
    placement_trends: [],
    application_funnel: {
      applied: 0,
      shortlisted: 0,
      interview: 0,
      offered: 0,
      placed: 0,
      rejected: 0,
      total: 0
    },
    job_demand_by_skills: [],
    meta: {
      months: 6
    }
  }
}

export default {
  name: 'LandingView',
  components: {
    Navbar,
    Footer,
    HeroSection
  },
  data() {
    return {
      demoRole: 'student',
      scrollProgress: 0,
      showScrollTop: false,
      isNavbarScrolled: false,
      mouseX: 50,
      mouseY: 50,
      pipelineProgressGo: false,
      counters: [
        { target: 500, value: 0 },
        { target: 80, value: 0 },
        { target: 200, value: 0 },
        { target: 95, value: 0 }
      ],
      publicDashboard: createEmptyPublicDashboard(),
      scrollRafId: null,
      counterObserver: null,
      pipelineObserver: null,
      onScroll: null,
      onMouseMove: null
    }
  },
  computed: {
    publicFunnel() {
      return this.publicDashboard?.application_funnel || {}
    }
  },
  directives: {
    reveal: {
      mounted(el) {
        const observer = new IntersectionObserver((entries) => {
          entries.forEach((entry) => {
            if (entry.isIntersecting) {
              entry.target.classList.add('in')
              observer.unobserve(entry.target)
            }
          })
        }, { threshold: 0.1 })

        observer.observe(el)
        el.__revealObserver = observer
      },
      unmounted(el) {
        el.__revealObserver?.disconnect()
      }
    }
  },
  mounted() {
    this.onMouseMove = (e) => {
      this.mouseX = e.clientX
      this.mouseY = e.clientY
    }

    this.onScroll = () => {
      if (this.scrollRafId !== null) {
        return
      }

      this.scrollRafId = requestAnimationFrame(() => {
        this.scrollRafId = null
        const scrolled = window.scrollY
        const maxScroll = document.documentElement.scrollHeight - window.innerHeight
        this.scrollProgress = maxScroll > 0 ? (scrolled / maxScroll) * 100 : 0
        this.showScrollTop = scrolled > 450
        this.isNavbarScrolled = scrolled > 30
      })
    }

    window.addEventListener('mousemove', this.onMouseMove, { passive: true })
    window.addEventListener('scroll', this.onScroll, { passive: true })
    this.onScroll()

    this.counterObserver = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          this.counters.forEach((counter, index) => {
            this.animateCounter(index, counter.target)
          })
          this.counterObserver?.disconnect()
        }
      })
    }, { threshold: 0.3 })

    if (this.$refs.statsSection) {
      this.counterObserver.observe(this.$refs.statsSection)
    }

    this.pipelineObserver = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          this.pipelineProgressGo = true
          this.pipelineObserver?.disconnect()
        }
      })
    }, { threshold: 0.4 })

    if (this.$refs.pipelineTrack) {
      this.pipelineObserver.observe(this.$refs.pipelineTrack)
    }

    this.fetchPublicDashboard()
  },
  beforeUnmount() {
    if (this.onMouseMove) {
      window.removeEventListener('mousemove', this.onMouseMove)
    }
    if (this.onScroll) {
      window.removeEventListener('scroll', this.onScroll)
    }
    if (this.scrollRafId !== null) {
      cancelAnimationFrame(this.scrollRafId)
      this.scrollRafId = null
    }
    this.counterObserver?.disconnect()
    this.pipelineObserver?.disconnect()
  },
  methods: {
    async fetchPublicDashboard(months = 6) {
      try {
        const response = await adminApi.getPublicLandingDashboard({ months })
        const payload = response?.data?.data || {}
        const fallback = createEmptyPublicDashboard()

        this.publicDashboard = {
          highlights: payload.highlights || fallback.highlights,
          placement_trends: Array.isArray(payload.placement_trends) ? payload.placement_trends : [],
          application_funnel: payload.application_funnel || fallback.application_funnel,
          job_demand_by_skills: Array.isArray(payload.job_demand_by_skills)
            ? payload.job_demand_by_skills
            : [],
          meta: payload.meta || fallback.meta
        }

        this.syncCountersFromPublicData()
      } catch (error) {
        this.publicDashboard = createEmptyPublicDashboard()
        this.syncCountersFromPublicData()
      }
    },
    syncCountersFromPublicData() {
      const highlights = this.publicDashboard?.highlights || {}
      const targets = [
        Number(highlights.placements_confirmed || 0),
        Number(highlights.approved_companies || 0),
        Number(highlights.approved_drives || 0),
        Number(highlights.latest_month_placements || 0)
      ]

      this.counters = this.counters.map((counter, index) => ({
        ...counter,
        target: targets[index]
      }))

      const shouldAnimateImmediately = this.counters.some((counter) => Number(counter.value || 0) > 0)
      if (shouldAnimateImmediately) {
        this.counters.forEach((counter, index) => {
          this.animateCounter(index, counter.target, 900, Number(counter.value || 0))
        })
      }
    },
    funnelCountLabel(value) {
      return `${Number(value || 0).toLocaleString()} students`
    },
    go(path) {
      this.$router.push(path)
    },
    animateCounter(index, target, duration = 2000, fromValue = 0) {
      let start = null
      const step = (timestamp) => {
        if (!start) {
          start = timestamp
        }
        const progress = Math.min((timestamp - start) / duration, 1)
        const eased = 1 - Math.pow(1 - progress, 4)
        const nextValue = fromValue + ((target - fromValue) * eased)
        this.counters[index].value = Math.floor(nextValue)
        if (progress < 1) {
          requestAnimationFrame(step)
        } else {
          this.counters[index].value = target
        }
      }
      requestAnimationFrame(step)
    },
    scrollTop() {
      window.scrollTo({ top: 0, behavior: 'smooth' })
    }
  }
}
</script>

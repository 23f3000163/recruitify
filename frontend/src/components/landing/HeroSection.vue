<template>
<section class="hero">

  <!-- Gradient mesh -->
  <div class="hero-mesh">
    <div class="mesh-blob blob-1"></div>
    <div class="mesh-blob blob-2"></div>
    <div class="mesh-blob blob-3"></div>
  </div>
  <div class="hero-dots"></div>

  <!-- Floating data cards -->
  <div class="hero-floats">
    <div class="hfc hfc-1">
      <div class="hfc-label">Placements Today</div>
      <div class="hfc-val g">89</div>
      <div class="hfc-sub up">↑ 24% vs yesterday</div>
    </div>
    <div class="hfc hfc-2">
      <div class="hfc-label">Active Drives</div>
      <div class="hfc-val b">18</div>
      <div class="hfc-sub" style="color:var(--t3)">Across 12 companies</div>
    </div>
    <div class="hfc hfc-3">
      <div class="hfc-notif">
        <div class="hfc-n-ico">🎉</div>
        <div>
          <div class="hfc-n-title">Arjun Sharma selected at Google</div>
          <div class="hfc-n-sub">SWE Intern · ₹42 LPA · 3 min ago</div>
        </div>
      </div>
    </div>
  </div>

  <!-- Hero text -->
  <div class="hero-content">

    <h1 class="hero-h1">
      <span class="h1-line-1">Campus Placements.</span>
      <div class="h1-line-2">
        <span class="h1-word-italic">Finally</span>
        <span class="h1-word-accent">Organized.</span>
      </div>
    </h1>

    <p class="hero-sub">
      Recruitify replaces the spreadsheet chaos of campus recruitment with a structured, role-based system — verified companies, automatic eligibility checks, and complete tracking from first application to final placement offer.
    </p>

    <div class="hero-btns">
      <a href="/register/student" class="btn-primary" @click.prevent="go('/register/student')">
        Start as Student
        <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
          <path d="M3 8h10M9 4l4 4-4 4" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
      </a>
      <a href="/register/company" class="btn-secondary" @click.prevent="go('/register/company')">Register Company</a>
    </div>

    <div class="hero-trust">
      <div class="trust-avs">
        <div class="trust-av" style="background:linear-gradient(135deg,#2563EB,#1D4ED8)">JS</div>
        <div class="trust-av" style="background:linear-gradient(135deg,#059669,#047857)">PR</div>
        <div class="trust-av" style="background:linear-gradient(135deg,#D97706,#B45309)">AM</div>
        <div class="trust-av" style="background:linear-gradient(135deg,#DC2626,#B91C1C)">SK</div>
        <div class="trust-av" style="background:linear-gradient(135deg,#7C3AED,#6D28D9)">VR</div>
      </div>
      <div class="trust-txt"><strong>500+ students</strong> placed this year</div>
      <div class="trust-divider"></div>
      <div class="trust-stat">
        <div class="t-n">80+</div>
        <div class="t-l">Verified companies</div>
      </div>
      <div class="trust-divider"></div>
      <div class="trust-stat">
        <div class="t-n">95%</div>
        <div class="t-l">Placement rate</div>
      </div>
    </div>

  </div>

  <!-- Browser mockup -->
  <div class="hero-mockup">
    <div class="browser-frame">

      <!-- Browser chrome -->
      <div class="browser-bar">
        <div class="browser-dots">
          <div class="b-dot b-red"></div>
          <div class="b-dot b-yel"></div>
          <div class="b-dot b-grn"></div>
        </div>
        <div class="browser-url">app.recruitify.in/student/dashboard</div>
      </div>

      <!-- Dashboard -->
      <div class="dashboard">

        <!-- Sidebar -->
        <div class="db-side">
          <div class="dbs-brand">
            <div class="dbs-logo">R</div>
            <div class="dbs-name">Recruitify</div>
          </div>
          <div class="dbs-sect">Main</div>
          <div class="dbs-item active"><div class="dbs-dot"></div>Dashboard</div>
          <div class="dbs-item"><div class="dbs-dot"></div>Placement Drives<span class="dbs-badge">18</span></div>
          <div class="dbs-item"><div class="dbs-dot"></div>My Applications</div>
          <div class="dbs-item"><div class="dbs-dot"></div>Notifications<span class="dbs-badge">3</span></div>
          <div class="dbs-sect">Profile</div>
          <div class="dbs-item"><div class="dbs-dot"></div>My Profile</div>
          <div class="dbs-item"><div class="dbs-dot"></div>Resume</div>
          <div class="dbs-item"><div class="dbs-dot"></div>History</div>
          <div class="dbs-user">
            <div class="dbs-av">AS</div>
            <div>
              <div class="dbs-name2">Arjun Sharma</div>
              <div class="dbs-role">CSE · Year 4 · CGPA 9.1</div>
            </div>
          </div>
        </div>

        <!-- Main content -->
        <div class="db-main">
          <div class="dbm-greet">
            <div class="dbm-gl">
              <h3>Good morning, Arjun</h3>
              <p>3 new eligible drives added today · Tuesday, March 2025</p>
            </div>
            <div class="dbm-gr"><div class="live-dot"></div>Live · 18 drives open</div>
          </div>

          <div class="dbm-stats">
            <div class="dbm-stat"><div class="dbm-stat-n clr-blue">6</div><div class="dbm-stat-l">Applied</div><div class="dbm-stat-d up">↑ 2 this week</div></div>
            <div class="dbm-stat"><div class="dbm-stat-n clr-amber">2</div><div class="dbm-stat-l">Shortlisted</div><div class="dbm-stat-d up">↑ 1 new</div></div>
            <div class="dbm-stat"><div class="dbm-stat-n clr-indigo">1</div><div class="dbm-stat-l">Interviewing</div><div class="dbm-stat-d" style="color:var(--t3)">Google SWE</div></div>
            <div class="dbm-stat"><div class="dbm-stat-n clr-green">1</div><div class="dbm-stat-l">Offer</div><div class="dbm-stat-d up">₹42 LPA 🎉</div></div>
          </div>

          <div class="dbm-cols">
            <!-- Drives panel -->
            <div class="db-panel">
              <div class="db-panel-head">
                <span class="dph-title">Eligible Drives</span>
                <span class="dph-badge">18 live</span>
              </div>
              <div class="drive-row"><div class="dr-logo" style="background:linear-gradient(135deg,#1A73E8,#34A853)">G</div><div class="dr-info"><div class="dr-title">Software Engineer Intern</div><div class="dr-meta">₹12 LPA · CSE,ECE · CGPA≥8.0 · Apr 15</div></div><div class="dr-tag tag-hot">🔥 Hot</div></div>
              <div class="drive-row"><div class="dr-logo" style="background:linear-gradient(135deg,#00A4EF,#7FBA00)">MS</div><div class="dr-info"><div class="dr-title">Product Analyst — Azure</div><div class="dr-meta">₹18 LPA · All branches · CGPA≥7.5 · Apr 20</div></div><div class="dr-tag tag-open">Open</div></div>
              <div class="drive-row"><div class="dr-logo" style="background:linear-gradient(135deg,#FF9900,#232F3E)">A</div><div class="dr-info"><div class="dr-title">Cloud Support Engineer</div><div class="dr-meta">₹22 LPA · CSE · CGPA≥8.5 · Apr 12</div></div><div class="dr-tag tag-new">New</div></div>
            </div>

            <!-- Right panels -->
            <div class="db-right-col">
              <!-- Donut chart -->
              <div class="db-chart-card">
                <div class="dcc-head">Placement Progress</div>
                <div class="donut-row">
                  <div class="donut"><span class="donut-val">95%</span></div>
                  <div class="donut-legend">
                    <div class="dl-item"><div class="dl-dot" style="background:var(--blue)"></div><div class="dl-label">Placed</div><div class="dl-val" style="color:var(--blue)">95%</div></div>
                    <div class="dl-item"><div class="dl-dot" style="background:var(--amber)"></div><div class="dl-label">In progress</div><div class="dl-val" style="color:var(--amber)">3%</div></div>
                    <div class="dl-item"><div class="dl-dot" style="background:var(--t4)"></div><div class="dl-label">Pending</div><div class="dl-val">2%</div></div>
                  </div>
                </div>
              </div>
              <!-- Mini pipeline -->
              <div class="db-pipe-card">
                <div class="dpc-head">Your Status — Google</div>
                <div class="mini-pipe">
                  <div class="mp-step"><div class="mp-dot mpd-done"></div><div class="mp-label">Applied</div><div class="mp-val mpv-done">✓</div></div>
                  <div class="mp-step"><div class="mp-dot mpd-done"></div><div class="mp-label">Shortlisted</div><div class="mp-val mpv-done">✓</div></div>
                  <div class="mp-step"><div class="mp-dot mpd-active"></div><div class="mp-label">Interview</div><div class="mp-val mpv-active">Today 3 PM</div></div>
                  <div class="mp-step"><div class="mp-dot mpd-wait"></div><div class="mp-label">Offer</div><div class="mp-val mpv-wait">—</div></div>
                  <div class="mp-step"><div class="mp-dot mpd-wait"></div><div class="mp-label">Placed</div><div class="mp-val mpv-wait">—</div></div>
                </div>
              </div>
            </div>

          </div><!-- /dbm-cols -->
        </div><!-- /db-main -->
      </div><!-- /dashboard -->
    </div><!-- /browser-frame -->
  </div><!-- /hero-mockup -->

</section>
</template>

<script>
export default {
  name: 'HeroSection',
  methods: {
    go(path) {
      this.$router.push(path)
    }
  }
}
</script>

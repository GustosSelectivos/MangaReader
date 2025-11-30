<template>
  <section class="welcome-hero">
    <div class="hero-inner">
      <div class="hero-text">
        <h1>Welcome to MangaSite</h1>
        <p class="lead">Read, browse and enjoy your favorite manga — fast, clean and distraction free.</p>
        <div class="hero-actions">
          <router-link class="btn primary" to="/library">Browse Library</router-link>
          <router-link class="btn ghost" to="/about">Learn more</router-link>
        </div>
      </div>
      <div class="hero-art">
        <img src="/assets/demo/Cover_MW001.webp" alt="cover" />
      </div>
    </div>
  </section>
</template>

<script setup>
// simple presentational component
</script>

<style scoped>
.welcome-hero { background: linear-gradient(180deg, rgba(255,255,255,0.02), transparent); padding:36px; border-radius:8px }
.hero-inner { display:flex; gap:24px; align-items:center; justify-content:space-between }
.hero-text h1 { margin:0 0 8px; font-size:28px }
.lead { margin:0 0 16px; color:var(--muted) }
.hero-actions { display:flex; gap:12px }
.btn { padding:10px 16px; border-radius:8px; text-decoration:none; color:var(--text); display:inline-block }
.btn.primary { background:var(--accent); color:#042022 }
.btn.ghost { background:transparent; border:1px solid rgba(255,255,255,0.06); color:var(--muted) }
.hero-art img { width:220px; height:300px; object-fit:cover; border-radius:8px }

@media(max-width:720px){ .hero-inner{flex-direction:column-reverse; align-items:flex-start} .hero-art img{width:180px;height:250px}}
</style>

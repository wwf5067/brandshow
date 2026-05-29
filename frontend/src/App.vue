<template>
  <el-config-provider :locale="zhCn">
    <div class="app-shell">
      <header class="app-header">
        <div class="header-inner">
          <router-link to="/" class="logo">
            <span class="logo-icon">📊</span>
            <span class="logo-text">BrandShow</span>
          </router-link>
          <nav class="header-nav">
            <router-link to="/">品牌榜单</router-link>
            <router-link to="/admin">管理后台</router-link>
          </nav>
        </div>
      </header>
      <main class="app-main">
        <router-view />
      </main>
    </div>
  </el-config-provider>
</template>

<script setup>
import zhCn from 'element-plus/es/locale/lang/zh-cn'
</script>

<style>
* { box-sizing: border-box; margin: 0; padding: 0; }

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  background: #f0f2f5;
  color: #1a1a2e;
}

.app-shell { min-height: 100vh; display: flex; flex-direction: column; }

.app-header {
  background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
  box-shadow: 0 2px 12px rgba(0,0,0,0.3);
  position: sticky;
  top: 0;
  z-index: 100;
}

.header-inner {
  max-width: 1280px;
  margin: 0 auto;
  padding: 0 24px;
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.logo {
  display: flex;
  align-items: center;
  gap: 10px;
  text-decoration: none;
  color: #fff;
}
.logo-icon { font-size: 24px; }
.logo-text { font-size: 20px; font-weight: 700; letter-spacing: 1px; }

.header-nav { display: flex; gap: 24px; }
.header-nav a {
  color: rgba(255,255,255,0.75);
  text-decoration: none;
  font-size: 14px;
  transition: color 0.2s;
}
.header-nav a:hover,
.header-nav a.router-link-active { color: #fff; }

.app-main {
  flex: 1;
  max-width: 1280px;
  margin: 0 auto;
  width: 100%;
  padding: 16px;
}

/* ── 移动端适配 ── */
@media (max-width: 640px) {
  .header-inner { padding: 0 16px; height: 52px; }
  .logo-text { font-size: 17px; }
  .header-nav { gap: 16px; }
  .header-nav a { font-size: 13px; }
  .app-main { padding: 12px; }
}
</style>

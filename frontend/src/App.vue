<template>
  <div class="app-shell">
    <aside class="sidebar">
      <div class="brand">
        <span class="brand-mark">茶</span>
        <div>
          <strong>奶茶采购</strong>
          <small>原料与库存中心</small>
        </div>
      </div>
      <nav class="nav-list">
        <RouterLink v-for="item in navItems" :key="item.path" :to="item.path">
          {{ item.label }}
        </RouterLink>
      </nav>
    </aside>
    <main class="main-panel">
      <RouterView />
    </main>
  </div>
</template>

<script setup>
const navItems = [
  { path: '/', label: '工作台' },
  { path: '/inventory', label: '库存预警' },
  { path: '/orders', label: '采购订单' },
  { path: '/suppliers', label: '供应商' },
  { path: '/records', label: '出入库记录' }
]
</script>

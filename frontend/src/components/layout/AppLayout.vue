<template>
  <a-layout class="app-layout">
    <AppHeader />
    <a-layout>
      <AppSidebar />
      <a-layout-content class="content">
        <div class="content-wrapper">
          <slot />
        </div>
      </a-layout-content>
    </a-layout>
  </a-layout>
</template>

<script setup lang="ts">
import AppHeader from './AppHeader.vue'
import AppSidebar from './AppSidebar.vue'
</script>

<style scoped>
.app-layout {
  height: 100vh;
  overflow: hidden;
}

.app-layout :deep(.ant-layout-has-sider) {
  flex: 1;
  overflow: hidden;
}

.content {
  margin: 24px;
  padding: 24px;
  background: #fff;
  min-height: 0;
  overflow-y: auto;
}

.content-wrapper {
  max-width: 1200px;
  margin: 0 auto;
}
</style>

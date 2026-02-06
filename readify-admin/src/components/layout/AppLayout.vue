<template>
  <el-container class="app-layout" direction="vertical">
    <TopHeader class="layout-header" />
    <el-container class="layout-body">
      <LeftSidebar class="layout-sidebar" />
      <el-main class="main-content">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup lang="ts">
import LeftSidebar from './LeftSidebar.vue'
import TopHeader from './TopHeader.vue'
</script>

<style scoped>
.app-layout {
  height: 100vh;
  width: 100%;
  overflow: hidden;
}

.layout-header {
  flex-shrink: 0;
}

.layout-body {
  min-height: 0;
  flex: 1;
}

.layout-sidebar {
  flex-shrink: 0;
}

.main-content {
  background-color: #f5f7fa;
  padding: 20px;
  min-width: 0;
}
</style>

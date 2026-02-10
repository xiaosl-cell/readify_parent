<template>
  <el-aside width="220px" class="sidebar">
    <div class="logo">
      <h2>Readify Admin</h2>
    </div>
    <el-menu
      :default-active="currentRoute"
      router
      background-color="rgb(237, 239, 250)"
      text-color="#606266"
      active-text-color="#409eff"
    >
      <el-menu-item index="/dashboard">
        <el-icon><DataBoard /></el-icon>
        <span>仪表盘</span>
      </el-menu-item>
      <el-menu-item index="/users">
        <el-icon><User /></el-icon>
        <span>用户管理</span>
      </el-menu-item>
      <el-menu-item index="/roles">
        <el-icon><UserFilled /></el-icon>
        <span>角色管理</span>
      </el-menu-item>
      <el-menu-item index="/permissions">
        <el-icon><Lock /></el-icon>
        <span>权限管理</span>
      </el-menu-item>
    </el-menu>
  </el-aside>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { DataBoard, User, UserFilled, Lock } from '@element-plus/icons-vue'

const route = useRoute()
const currentRoute = computed(() => route.path)
</script>

<style scoped>
.sidebar {
  background-color: rgb(237, 239, 250);
  height: 100%;
  border-right: 1px solid #e8eaf0;
}

.logo {
  height: 64px;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: rgb(237, 239, 250);
  border-bottom: 1px solid #e8eaf0;
}

.logo h2 {
  font-size: 20px;
  font-weight: 600;
  margin: 0;
  background: linear-gradient(135deg, #2c3e50 0%, #3498db 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.el-menu {
  border-right: none;
}

.el-menu-item:hover {
  background-color: rgba(64, 158, 255, 0.08) !important;
}

.el-menu-item.is-active {
  background-color: rgba(64, 158, 255, 0.12) !important;
}
</style>

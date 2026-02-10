<template>
  <el-aside width="220px" class="sidebar">
    <div class="logo">
      <h2>Readify Admin</h2>
    </div>
    <el-menu
      :default-active="currentRoute"
      router
      background-color="#304156"
      text-color="#bfcbd9"
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
  background-color: #304156;
  height: 100vh;
}

.logo {
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: #263445;
}

.logo h2 {
  color: #fff;
  font-size: 18px;
  margin: 0;
}

.el-menu {
  border-right: none;
}
</style>

<template>
  <el-header class="header">
    <div class="header-left">
      <span class="page-title">{{ pageTitle }}</span>
    </div>
    <div class="header-right">
      <el-dropdown @command="handleCommand">
        <span class="user-dropdown">
          <el-avatar :size="32" icon="UserFilled" />
          <span class="username">{{ username }}</span>
          <el-icon><ArrowDown /></el-icon>
        </span>
        <template #dropdown>
          <el-dropdown-menu>
            <el-dropdown-item command="logout">退出登录</el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>
    </div>
  </el-header>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useStore } from 'vuex'
import { ArrowDown } from '@element-plus/icons-vue'

const route = useRoute()
const router = useRouter()
const store = useStore()

const pageTitle = computed(() => (route.meta.title as string) || 'Readify Admin')
const username = computed(() => store.getters.username || 'Admin')

const handleCommand = (command: string) => {
  if (command === 'logout') {
    store.dispatch('logout')
    router.push('/login')
  }
}
</script>

<style scoped>
.header {
  height: 60px;
  width: 100%;
  background-color: #fff;
  display: flex;
  align-items: center;
  justify-content: space-between;
  box-shadow: 0 1px 4px rgba(0, 21, 41, 0.08);
  padding: 0 20px;
}

.page-title {
  font-size: 22px;
  font-weight: 600;
  color: #333;
}

.user-dropdown {
  display: flex;
  align-items: center;
  cursor: pointer;
}

.username {
  margin: 0 8px;
  color: #333;
}
</style>

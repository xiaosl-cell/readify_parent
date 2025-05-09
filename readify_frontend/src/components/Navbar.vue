<template>
  <div class="navbar">
    <div class="nav-left">
      <h1 class="logo">Readify</h1>
      <div v-if="projectName" class="divider"></div>
      <h2 v-if="projectName" class="project-title">{{ projectName }}</h2>
      <div class="nav-links">
        <router-link to="/home" class="nav-link">首页</router-link>
        <router-link to="/about" class="nav-link">关于</router-link>
      </div>
    </div>
    <div class="nav-right">
      <el-dropdown @command="handleCommand">
        <span class="user-profile">
          <el-avatar :size="32" :icon="UserFilled" />
          <span class="username">{{ username }}</span>
          <el-icon class="el-icon--right"><CaretBottom /></el-icon>
        </span>
        <template #dropdown>
          <el-dropdown-menu>
            <el-dropdown-item command="profile">个人信息</el-dropdown-item>
            <el-dropdown-item command="settings">设置</el-dropdown-item>
            <el-dropdown-item divided command="logout">退出登录</el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>
    </div>
  </div>
</template>

<script lang="ts" setup>
import { computed } from 'vue'
import { useStore } from 'vuex'
import { useRouter } from 'vue-router'
import { ElMessageBox } from 'element-plus'
import { UserFilled, CaretBottom } from '@element-plus/icons-vue'
import { removeToken } from '@/utils/auth'

const props = defineProps({
  projectName: {
    type: String,
    default: ''
  }
})

const store = useStore()
const router = useRouter()
const username = computed(() => store.state.user?.username || '用户')

// 处理用户菜单命令
const handleCommand = async (command: string) => {
  switch (command) {
    case 'logout':
      await ElMessageBox.confirm(
        '确定要退出登录吗？',
        '提示',
        {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning'
        }
      )
      store.dispatch('logout')
      removeToken()
      router.push('/login')
      break
  }
}
</script>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700&family=Montserrat:wght@600&display=swap');

.navbar {
  width: 100%;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 32px;
  height: 64px;
  background-color: rgb(237, 239, 250);
  position: sticky;
  top: 0;
  z-index: 100;
}

.nav-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.logo {
  font-size: 32px;
  color: #2c3e50;
  margin: 0;
  font-weight: 600;
  font-family: 'Montserrat', sans-serif;
  letter-spacing: -1px;
  background: linear-gradient(135deg, #2c3e50 0%, #3498db 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  transition: all 0.3s ease;
}

.logo:hover {
  transform: scale(1.02);
  background: linear-gradient(135deg, #3498db 0%, #2c3e50 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.divider {
  width: 2px;
  height: 28px;
  background: linear-gradient(to bottom, rgba(44, 62, 80, 0.1), rgba(52, 152, 219, 0.1));
  margin: 0 8px;
}

.nav-left .project-title {
  font-size: 22px;
  color: #000000;
  margin: 0;
  font-weight: 600;
  font-family: 'Montserrat', sans-serif;
  letter-spacing: -0.5px;
}

.nav-links {
  display: flex;
  margin-left: 24px;
}

.nav-link {
  color: #606266;
  text-decoration: none;
  padding: 0 16px;
  font-size: 14px;
  transition: all 0.3s;
}

.nav-link:hover, .router-link-active {
  color: #409EFF;
}

.nav-right {
  display: flex;
  align-items: center;
}

.user-profile {
  display: flex;
  align-items: center;
  cursor: pointer;
  padding: 8px;
  border-radius: 4px;
  transition: background-color 0.3s;
}

.user-profile:hover {
  background-color: #f5f7fa;
}

.username {
  margin: 0 8px;
  font-size: 14px;
  color: #606266;
}
</style> 
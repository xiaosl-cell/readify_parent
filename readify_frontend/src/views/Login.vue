<template>
  <div class="login-container">
    <div class="login-content">
      <div class="login-left">
        <div class="welcome-text">
          <h2>欢迎使用</h2>
          <h1>Readify</h1>
          <p>您的个人阅读管理助手</p>
        </div>
        <div class="decoration-image"></div>
      </div>
      <div class="login-right">
        <div class="login-box">
          <h1>登录</h1>
          <el-form :model="form" :rules="rules" ref="formRef" label-position="top">
            <el-form-item prop="username">
              <el-input v-model="form.username" placeholder="请输入用户名">
                <template #prefix>
                  <el-icon><User /></el-icon>
                </template>
              </el-input>
            </el-form-item>
            <el-form-item prop="password">
              <el-input v-model="form.password" type="password" placeholder="请输入密码" @keyup.enter="handleLogin">
                <template #prefix>
                  <el-icon><Lock /></el-icon>
                </template>
              </el-input>
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="handleLogin" :loading="loading" class="submit-btn">登录</el-button>
              <div class="register-link">
                还没有账号？<el-button link @click="$router.push('/register')">立即注册</el-button>
              </div>
            </el-form-item>
          </el-form>
        </div>
      </div>
    </div>
  </div>
</template>

<script lang="ts" setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useStore } from 'vuex'
import { ElMessage } from 'element-plus'
import { User, Lock } from '@element-plus/icons-vue'
import { login } from '../api/auth'
import { setToken } from '@/utils/auth'

const router = useRouter()
const store = useStore()
const formRef = ref()
const loading = ref(false)

const form = reactive({
  username: '',
  password: ''
})

const rules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 20, message: '用户名长度在 3 到 20 个字符', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, max: 20, message: '密码长度在 6 到 20 个字符', trigger: 'blur' }
  ]
}

const handleLogin = async () => {
  if (!formRef.value) return
  
  await formRef.value.validate()
  
  try {
    loading.value = true
    const res = await login(form)
    store.dispatch('login', res.data)
    setToken(res.data.token)
    ElMessage.success('登录成功')
    router.push('/home')
  } catch (error) {
    console.error('Login failed:', error)
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-container {
  width: 100%;
  height: 100%;
  display: flex;
  justify-content: center;
  align-items: center;
  overflow: hidden;
  border-radius: 16px;
}

.login-content {
  width: 100%;
  height: 100%;
  display: flex;
  background: #fff;
  border-radius: 16px;
  overflow: hidden;
}

.login-left {
  width: 50%;
  position: relative;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 40px;
  color: #fff;
  display: flex;
  flex-direction: column;
}

.welcome-text {
  position: relative;
  z-index: 1;
  padding-top: 15vh;
}

.welcome-text h1 {
  font-size: 48px;
  margin: 16px 0;
  font-weight: 600;
}

.welcome-text h2 {
  font-size: 24px;
  font-weight: 400;
  opacity: 0.9;
}

.welcome-text p {
  font-size: 18px;
  opacity: 0.8;
  margin-top: 16px;
}

.decoration-image {
  position: absolute;
  bottom: 0;
  left: 0;
  width: 100%;
  height: 60%;
  background-image: url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNjAwIiBoZWlnaHQ9IjYwMCIgdmlld0JveD0iMCAwIDYwMCA2MDAiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+CiAgPHBhdGggZmlsbD0ibm9uZSIgc3Ryb2tlPSJyZ2JhKDI1NSwgMjU1LCAyNTUsIDAuMikiIHN0cm9rZS13aWR0aD0iMiIgZD0iTTMwMCAzMDBtLTE1MCAwYTE1MCAxNTAgMCAxIDAgMzAwIDBhMTUwIDE1MCAwIDEgMC0zMDAgMHoiLz4KICA8cGF0aCBmaWxsPSJub25lIiBzdHJva2U9InJnYmEoMjU1LCAyNTUsIDI1NSwgMC4yKSIgc3Ryb2tlLXdpZHRoPSIyIiBkPSJNMzAwIDMwMG0tMTAwIDBhMTAwIDEwMCAwIDEgMCAyMDAgMGExMDAgMTAwIDAgMSAwLTIwMCAweiIvPgogIDxwYXRoIGZpbGw9Im5vbmUiIHN0cm9rZT0icmdiYSgyNTUsIDI1NSwgMjU1LCAwLjIpIiBzdHJva2Utd2lkdGg9IjIiIGQ9Ik0zMDAgMzAwbTUwIDBhNTAgNTAgMCAxIDAgMTAwIDBhNTAgNTAgMCAxIDAtMTAwIDB6Ii8+Cjwvc3ZnPg==');
  background-repeat: no-repeat;
  background-position: center bottom;
  background-size: contain;
  opacity: 0.2;
}

.login-right {
  width: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40px;
  background: #fff;
}

.login-box {
  width: 100%;
  max-width: 360px;
}

.login-box h1 {
  text-align: center;
  color: #333;
  margin-bottom: 30px;
  font-size: 28px;
  font-weight: 500;
}

.submit-btn {
  width: 100%;
  padding: 12px 0;
  font-size: 16px;
  margin-top: 10px;
  border-radius: 8px;
}

.register-link {
  text-align: center;
  margin-top: 20px;
  color: #666;
}

:deep(.el-form-item) {
  margin-bottom: 20px;
}

:deep(.el-form-item__label) {
  font-size: 14px;
  color: #606266;
  line-height: 40px;
  padding: 0 12px 0 0;
}

:deep(.el-input__wrapper) {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
  border-radius: 8px;
}

:deep(.el-input__inner) {
  height: 40px;
  line-height: 40px;
}

:deep(.el-button--link) {
  font-size: 14px;
  padding-left: 3px;
  padding-right: 3px;
}
</style> 
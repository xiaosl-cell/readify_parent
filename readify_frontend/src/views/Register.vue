<template>
  <div class="register-container">
    <div class="register-content">
      <div class="register-left">
        <div class="welcome-text">
          <h2>欢迎加入</h2>
          <h1>Readify</h1>
          <p>开启您的阅读之旅</p>
        </div>
        <div class="decoration-image"></div>
      </div>
      <div class="register-right">
        <div class="register-box">
          <h1>注册</h1>
          <el-form :model="form" :rules="rules" ref="formRef" label-width="80px">
            <el-form-item label="用户名" prop="username">
              <el-input v-model="form.username" placeholder="请输入用户名">
                <template #prefix>
                  <el-icon><User /></el-icon>
                </template>
              </el-input>
            </el-form-item>
            <el-form-item label="密码" prop="password">
              <el-input v-model="form.password" type="password" placeholder="请输入密码">
                <template #prefix>
                  <el-icon><Lock /></el-icon>
                </template>
              </el-input>
            </el-form-item>
            <el-form-item label="确认密码" prop="confirmPassword">
              <el-input v-model="form.confirmPassword" type="password" placeholder="请再次输入密码" @keyup.enter="handleRegister">
                <template #prefix>
                  <el-icon><Lock /></el-icon>
                </template>
              </el-input>
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="handleRegister" :loading="loading" class="submit-btn">注册</el-button>
              <div class="login-link">
                已有账号？<el-button link @click="$router.push('/login')">立即登录</el-button>
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
import { ElMessage } from 'element-plus'
import { User, Lock } from '@element-plus/icons-vue'
import { register } from '../api/auth'

const router = useRouter()
const formRef = ref()
const loading = ref(false)

const form = reactive({
  username: '',
  password: '',
  confirmPassword: ''
})

const validatePass = (rule: any, value: string, callback: Function) => {
  if (value === '') {
    callback(new Error('请再次输入密码'))
  } else if (value !== form.password) {
    callback(new Error('两次输入密码不一致'))
  } else {
    callback()
  }
}

const rules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 20, message: '用户名长度在 3 到 20 个字符', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, max: 20, message: '密码长度在 6 到 20 个字符', trigger: 'blur' }
  ],
  confirmPassword: [
    { required: true, message: '请再次输入密码', trigger: 'blur' },
    { validator: validatePass, trigger: 'blur' }
  ]
}

const handleRegister = async () => {
  if (!formRef.value) return
  
  await formRef.value.validate()
  
  try {
    loading.value = true
    const res = await register({
      username: form.username,
      password: form.password
    })
    ElMessage.success('注册成功')
    router.push('/login')
  } catch (error) {
    console.error('Register failed:', error)
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.register-container {
  width: 100%;
  height: 100%;
  display: flex;
  justify-content: center;
  align-items: center;
  overflow: hidden;
  border-radius: 16px;
}

.register-content {
  width: 100%;
  height: 100%;
  display: flex;
  background: #fff;
  border-radius: 16px;
  overflow: hidden;
}

.register-left {
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

.register-right {
  width: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40px;
  background: #fff;
}

.register-box {
  width: 100%;
  max-width: 360px;
}

.register-box h1 {
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

.login-link {
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
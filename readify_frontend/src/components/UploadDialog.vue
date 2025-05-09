<template>
  <el-dialog
    v-model="dialogVisible"
    :title="`上传文件到 ${projectName}`"
    width="480px"
    class="upload-dialog"
  >
    <template #header>
      <div class="upload-dialog-header">
        <div class="upload-dialog-title">
          <span class="project-title">{{ projectName }}</span>
          <span class="upload-label">书源上传</span>
        </div>
      </div>
    </template>
    <el-upload
      class="upload-area"
      drag
      :action="uploadUrl"
      :headers="uploadHeaders"
      :before-upload="beforeUpload"
      :on-success="handleUploadSuccess"
      :on-error="handleUploadError"
      name="file"
      accept=".pdf,.doc,.docx,.txt"
    >
      <el-icon class="upload-icon"><Upload /></el-icon>
      <div class="upload-text">
        <h3>点击或拖拽文件到此处上传</h3>
        <p class="upload-hint">支持 PDF、Word、TXT 格式文件</p>
      </div>
    </el-upload>
  </el-dialog>
</template>

<script lang="ts" setup>
import { ref, computed, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { Upload } from '@element-plus/icons-vue'

const props = defineProps<{
  visible: boolean
  projectId: number
  projectName: string
  uploadHeaders: Record<string, string>
}>()

const emit = defineEmits<{
  (e: 'update:visible', visible: boolean): void
  (e: 'success'): void
}>()

const dialogVisible = ref(props.visible)

// 监听visible属性变化
watch(() => props.visible, (newVal) => {
  dialogVisible.value = newVal
})

// 监听dialogVisible变化，同步回父组件
watch(dialogVisible, (newVal) => {
  emit('update:visible', newVal)
})

// 上传URL
const uploadUrl = computed(() => `/api/projects/${props.projectId}/files`)

// 上传前的验证
const beforeUpload = (file: File) => {
  const isLt10M = file.size / 1024 / 1024 < 10
  if (!isLt10M) {
    ElMessage.error('文件大小不能超过 10MB!')
    return false
  }
  return true
}

// 上传成功的回调
const handleUploadSuccess = (response: any) => {
  if (response.code === '200') {
    ElMessage.success('文件上传成功')
    dialogVisible.value = false
    emit('success')
  } else {
    ElMessage.error(response.message || '上传失败')
  }
}

// 上传失败的回调
const handleUploadError = (error: any) => {
  ElMessage.error('文件上传失败')
}
</script>

<style scoped>
.upload-dialog :deep(.el-dialog__header) {
  margin: 0;
  padding: 28px 32px 24px;
  border-bottom: 1px solid #f0f0f0;
  background: linear-gradient(135deg, #f8f9fa 0%, #ffffff 100%);
}

.upload-dialog-header {
  width: 100%;
}

.upload-dialog-title {
  display: flex;
  align-items: baseline;
  gap: 16px;
}

.project-title {
  color: #303133;
  font-weight: 600;
  font-size: 24px;
  font-family: 'Montserrat', sans-serif;
  background: linear-gradient(135deg, #409EFF 0%, #2c3e50 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  padding: 2px 0;
}

.upload-label {
  color: #909399;
  font-weight: normal;
  font-size: 15px;
  position: relative;
  top: 1px;
}

.upload-dialog :deep(.el-dialog__headerbtn) {
  top: 32px;
  right: 32px;
}

.upload-area {
  width: 100%;
}

.upload-area :deep(.el-upload) {
  width: 100%;
}

.upload-area :deep(.el-upload-dragger) {
  width: 100%;
  height: 240px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  border: 2px dashed #e4e7ed;
  border-radius: 12px;
  background: #f8faff;
  transition: all 0.3s;
}

.upload-area :deep(.el-upload-dragger:hover) {
  border-color: #409eff;
  background: #f0f7ff;
}

.upload-area :deep(.el-upload-dragger.is-dragover) {
  background: #ecf5ff;
  border-color: #409eff;
}

.upload-icon {
  font-size: 48px;
  color: #409eff;
  margin-bottom: 16px;
}

.upload-text h3 {
  font-size: 16px;
  font-weight: 500;
  color: #303133;
  margin: 0 0 8px;
}

.upload-hint {
  font-size: 14px;
  color: #909399;
  margin: 0;
}

:deep(.el-upload-list) {
  margin-top: 20px;
}

:deep(.el-upload-list__item) {
  transition: all 0.3s;
  padding: 8px 12px;
  border-radius: 6px;
}

:deep(.el-upload-list__item:hover) {
  background-color: #f5f7fa;
}

:deep(.el-upload-list__item-name) {
  color: #606266;
}

:deep(.el-upload-list__item .el-icon) {
  color: #909399;
}
</style> 
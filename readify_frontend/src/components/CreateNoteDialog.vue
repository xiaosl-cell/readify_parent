<template>
  <el-dialog
    v-model="dialogVisible"
    title="创建笔记"
    width="500px"
    class="create-note-dialog"
    :close-on-click-modal="false"
    @closed="resetForm"
  >
    <template #header>
      <div class="dialog-header">
        <div class="dialog-title">
          <span class="main-title">创建笔记</span>
          <span class="sub-title">思维导图</span>
        </div>
      </div>
    </template>
    
    <el-form ref="formRef" :model="form" :rules="rules" label-width="80px">
      <el-form-item label="标题" prop="title">
        <el-input v-model="form.title" placeholder="请输入笔记标题" />
      </el-form-item>
      
      <el-form-item label="类型" prop="type">
        <el-select v-model="form.type" placeholder="请选择笔记类型" disabled>
          <el-option label="思维导图" value="mind_map" />
        </el-select>
      </el-form-item>
      
      <el-form-item label="文件" prop="fileId">
        <el-select 
          v-model="form.fileId" 
          placeholder="请选择文件"
          :loading="loadingFiles"
        >
          <el-option
            v-for="file in files"
            :key="file.id"
            :label="file.originalName"
            :value="file.id"
          />
        </el-select>
      </el-form-item>
      
      <el-form-item label="描述" prop="description">
        <el-input
          v-model="form.description"
          type="textarea"
          rows="4"
          placeholder="请输入笔记描述"
        />
      </el-form-item>
    </el-form>
    <template #footer>
      <span class="dialog-footer">
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="submitting">
          确定
        </el-button>
      </span>
    </template>
  </el-dialog>
</template>

<script lang="ts" setup>
import { ref, reactive, defineEmits, defineExpose, onMounted, watch, inject } from 'vue'
import type { FormInstance, FormRules } from 'element-plus'
import { ElMessage } from 'element-plus'
import { getProjectFiles } from '@/api/project'
import { createMindMap, checkMindMapTitle } from '@/api/mindmap'
import type { FileVO } from '@/api/project'
import type { CreateMindMapParams } from '@/types/mindmap'

const emit = defineEmits<{
  (e: 'created'): void
}>()

// 从父组件注入projectId
const injectedProjectId = inject<Ref<number>>('projectId', ref(1))

const dialogVisible = ref(false)
const formRef = ref<FormInstance>()
const files = ref<FileVO[]>([])
const loadingFiles = ref(false)
const submitting = ref(false)

const form = reactive<CreateMindMapParams>({
  projectId: injectedProjectId.value,
  fileId: undefined as unknown as number,
  title: '',
  type: 'mind_map',
  description: ''
})

// 表单验证规则
const rules = reactive<FormRules>({
  title: [
    { required: true, message: '请输入笔记标题', trigger: 'blur' },
    { min: 2, max: 50, message: '标题长度应在2到50个字符之间', trigger: 'blur' }
  ],
  type: [
    { required: true, message: '请选择笔记类型', trigger: 'change' }
  ],
  fileId: [
    { required: true, message: '请选择文件', trigger: 'change' }
  ]
})

// 监听projectId变化，更新表单的projectId
watch(() => injectedProjectId.value, (newValue) => {
  form.projectId = newValue
  if (dialogVisible.value) {
    loadFiles()
  }
})

// 加载项目文件列表
const loadFiles = async () => {
  if (!form.projectId) return
  
  try {
    loadingFiles.value = true
    const res = await getProjectFiles(form.projectId)
    files.value = res.data || []
  } catch (error) {
    console.error('Failed to load files:', error)
    ElMessage.error('加载文件列表失败')
  } finally {
    loadingFiles.value = false
  }
}

// 打开弹窗
const open = () => {
  dialogVisible.value = true
  loadFiles()
}

// 重置表单
const resetForm = () => {
  form.fileId = undefined as unknown as number
  form.title = ''
  form.description = ''
  formRef.value?.resetFields()
}

// 检查标题是否存在
const checkTitle = async (title: string, projectId: number) => {
  try {
    const res = await checkMindMapTitle(title, projectId)
    return res.data
  } catch (error) {
    console.error('Failed to check title:', error)
    return false
  }
}

// 提交表单
const handleSubmit = async () => {
  if (!formRef.value) return
  
  await formRef.value.validate(async (valid) => {
    if (!valid) return
    
    try {
      submitting.value = true
      
      // 检查标题是否已存在
      const titleExists = await checkTitle(form.title, form.projectId)
      if (titleExists) {
        ElMessage.warning('该标题已存在，请修改后重试')
        return
      }
      
      // 提交创建请求
      const res = await createMindMap(form)
      
      if (res.code === '200') {
        ElMessage.success('创建成功')
        dialogVisible.value = false
        emit('created')
      } else {
        ElMessage.error(res.message || '创建失败')
      }
    } catch (error) {
      console.error('Failed to create mind map:', error)
      ElMessage.error('创建失败，请重试')
    } finally {
      submitting.value = false
    }
  })
}

// 暴露方法给父组件调用
defineExpose({
  open
})
</script>

<style scoped>
.create-note-dialog :deep(.el-dialog__header) {
  margin: 0;
  padding: 28px 32px 24px;
  border-bottom: 1px solid #f0f0f0;
  background: linear-gradient(135deg, #f8f9fa 0%, #ffffff 100%);
}

.dialog-header {
  width: 100%;
}

.dialog-title {
  display: flex;
  align-items: baseline;
  gap: 16px;
}

.main-title {
  color: #303133;
  font-weight: 600;
  font-size: 24px;
  font-family: 'Montserrat', sans-serif;
  background: linear-gradient(135deg, #409EFF 0%, #2c3e50 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  padding: 2px 0;
}

.sub-title {
  color: #909399;
  font-weight: normal;
  font-size: 15px;
  position: relative;
  top: 1px;
}

.create-note-dialog :deep(.el-dialog__headerbtn) {
  top: 32px;
  right: 32px;
}

.create-note-dialog :deep(.el-dialog__body) {
  padding: 24px 32px;
}

.create-note-dialog :deep(.el-form-item) {
  margin-bottom: 24px;
}

.create-note-dialog :deep(.el-form-item__label) {
  font-weight: 500;
}

.create-note-dialog :deep(.el-input__inner) {
  border-radius: 6px;
}

.create-note-dialog :deep(.el-textarea__inner) {
  border-radius: 6px;
  min-height: 100px;
}

.create-note-dialog :deep(.el-dialog__footer) {
  padding: 16px 32px 24px;
  border-top: 1px solid #f0f0f0;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

.dialog-footer .el-button {
  padding: 9px 20px;
  font-size: 14px;
  border-radius: 6px;
  transition: all 0.3s;
}

.dialog-footer .el-button:hover {
  transform: translateY(-1px);
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.1);
}

.dialog-footer .el-button:active {
  transform: translateY(0);
  box-shadow: none;
}

.dialog-footer .el-button--primary {
  --el-button-font-weight: 500;
  --el-button-border-color: #409EFF;
  --el-button-bg-color: #409EFF;
  --el-button-hover-bg-color: #66b1ff;
  --el-button-hover-border-color: #66b1ff;
}

:deep(.el-dialog) {
  margin: 0 !important;
  position: absolute !important;
  top: 50% !important;
  left: 50% !important;
  transform: translate(-50%, -50%) !important;
  max-width: 90%;
  max-height: 90vh;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 12px 32px rgba(0, 0, 0, 0.1);
}

:deep(.el-dialog__body) {
  max-height: calc(90vh - 150px);
  overflow-y: auto;
}

:deep(.el-select) {
  width: 100%;
}
</style> 
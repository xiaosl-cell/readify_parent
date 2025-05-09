<template>
  <el-dialog
    v-model="dialogVisible"
    :title="dialogType === 'create' ? '创建工程' : '编辑工程'"
    width="500px"
  >
    <el-form
      ref="projectFormRef"
      :model="projectForm"
      :rules="projectRules"
      label-width="80px"
    >
      <el-form-item label="工程名称" prop="name">
        <el-input v-model="projectForm.name" placeholder="请输入工程名称" />
      </el-form-item>
      <el-form-item label="工程描述" prop="description">
        <el-input
          v-model="projectForm.description"
          type="textarea"
          rows="3"
          placeholder="请输入工程描述"
        />
      </el-form-item>
    </el-form>
    <template #footer>
      <span class="dialog-footer">
        <el-button @click="handleCancel">取消</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="submitting">
          确定
        </el-button>
      </span>
    </template>
  </el-dialog>
</template>

<script lang="ts" setup>
import { ref, reactive, watch } from 'vue'
import type { FormInstance } from 'element-plus'
import type { ProjectVO } from '@/types/project'

const props = defineProps<{
  visible: boolean
  type: 'create' | 'edit'
  project?: ProjectVO
  submitting: boolean
}>()

const emit = defineEmits<{
  (e: 'update:visible', visible: boolean): void
  (e: 'submit', form: { id?: number, name: string, description: string }): void
  (e: 'cancel'): void
}>()

const dialogVisible = ref(props.visible)
const dialogType = ref(props.type)
const projectFormRef = ref<FormInstance>()

const projectForm = reactive({
  id: undefined as number | undefined,
  name: '',
  description: ''
})

const projectRules = {
  name: [
    { required: true, message: '请输入工程名称', trigger: 'blur' },
    { min: 2, max: 50, message: '长度在 2 到 50 个字符', trigger: 'blur' }
  ]
}

// 监听visible属性变化
watch(() => props.visible, (newVal) => {
  dialogVisible.value = newVal
})

// 监听dialogVisible变化，同步回父组件
watch(dialogVisible, (newVal) => {
  emit('update:visible', newVal)
})

// 监听type属性变化
watch(() => props.type, (newVal) => {
  dialogType.value = newVal
})

// 监听project属性变化
watch(() => props.project, (newVal) => {
  if (newVal) {
    projectForm.id = newVal.id
    projectForm.name = newVal.name
    projectForm.description = newVal.description || ''
  } else {
    projectForm.id = undefined
    projectForm.name = ''
    projectForm.description = ''
  }
}, { immediate: true })

// 取消按钮
const handleCancel = () => {
  dialogVisible.value = false
  emit('cancel')
}

// 提交表单
const handleSubmit = async () => {
  if (!projectFormRef.value) return
  
  try {
    await projectFormRef.value.validate()
    emit('submit', {
      id: projectForm.id,
      name: projectForm.name,
      description: projectForm.description
    })
  } catch (error) {
    console.error('表单验证失败:', error)
  }
}
</script>

<style scoped>
:deep(.el-dialog) {
  margin: 0 !important;
  position: absolute !important;
  top: 50% !important;
  left: 50% !important;
  transform: translate(-50%, -50%) !important;
  max-width: 90%;
  max-height: 90vh;
}

:deep(.el-dialog__body) {
  max-height: calc(90vh - 150px);
  overflow-y: auto;
}
</style> 
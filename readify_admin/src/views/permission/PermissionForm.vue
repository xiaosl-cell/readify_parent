<template>
  <el-dialog
    :model-value="visible"
    :title="permission ? '编辑权限' : '新增权限'"
    width="500px"
    @update:model-value="$emit('update:visible', $event)"
    @open="initForm"
  >
    <el-form ref="formRef" :model="form" :rules="rules" label-width="80px">
      <el-form-item label="编码" prop="code">
        <el-input v-model="form.code" placeholder="请输入权限编码，如 USER:READ" />
      </el-form-item>
      <el-form-item label="名称" prop="name">
        <el-input v-model="form.name" placeholder="请输入权限名称" />
      </el-form-item>
      <el-form-item label="模块" prop="module">
        <el-input v-model="form.module" placeholder="请输入所属模块，如 USER" />
      </el-form-item>
      <el-form-item label="描述" prop="description">
        <el-input v-model="form.description" type="textarea" placeholder="请输入权限描述" />
      </el-form-item>
      <el-form-item label="状态" prop="enabled">
        <el-switch v-model="form.enabled" />
      </el-form-item>
    </el-form>

    <template #footer>
      <el-button @click="$emit('update:visible', false)">取消</el-button>
      <el-button type="primary" :loading="loading" @click="handleSubmit">
        确定
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import { createPermission, updatePermission } from '@/api/permission'
import type { Permission } from '@/types'

const props = defineProps<{
  visible: boolean
  permission: Permission | null
}>()

const emit = defineEmits<{
  'update:visible': [value: boolean]
  success: []
}>()

const formRef = ref<FormInstance>()
const loading = ref(false)

const form = reactive({
  code: '',
  name: '',
  module: '',
  description: '',
  enabled: true
})

const rules: FormRules = {
  code: [{ required: true, message: '请输入权限编码', trigger: 'blur' }],
  name: [{ required: true, message: '请输入权限名称', trigger: 'blur' }]
}

const initForm = () => {
  if (props.permission) {
    form.code = props.permission.code
    form.name = props.permission.name
    form.module = props.permission.module || ''
    form.description = props.permission.description || ''
    form.enabled = props.permission.enabled
  } else {
    form.code = ''
    form.name = ''
    form.module = ''
    form.description = ''
    form.enabled = true
  }
}

const handleSubmit = async () => {
  if (!formRef.value) return
  await formRef.value.validate(async (valid) => {
    if (valid) {
      loading.value = true
      try {
        if (props.permission) {
          await updatePermission(props.permission.id, form)
          ElMessage.success('更新成功')
        } else {
          await createPermission(form)
          ElMessage.success('创建成功')
        }
        emit('update:visible', false)
        emit('success')
      } catch (error) {
        console.error('Failed to save permission:', error)
      } finally {
        loading.value = false
      }
    }
  })
}
</script>

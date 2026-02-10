<template>
  <el-dialog
    :model-value="visible"
    title="分配权限"
    width="600px"
    @update:model-value="$emit('update:visible', $event)"
    @open="loadPermissions"
  >
    <div v-if="role">
      <p class="role-info">角色: {{ role.name }} ({{ role.code }})</p>
      <div v-loading="loadingPermissions" class="permission-tree">
        <div v-for="(permissions, module) in permissionTree" :key="module" class="permission-module">
          <div class="module-header">{{ module }}</div>
          <el-checkbox-group v-model="selectedPermissionIds">
            <el-checkbox
              v-for="permission in permissions"
              :key="permission.id"
              :value="permission.id"
              :label="permission.id"
              class="permission-checkbox"
            >
              {{ permission.name }} ({{ permission.code }})
            </el-checkbox>
          </el-checkbox-group>
        </div>
      </div>
    </div>

    <template #footer>
      <el-button @click="$emit('update:visible', false)">取消</el-button>
      <el-button type="primary" :loading="loading" @click="handleSubmit">
        确定
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { getPermissionTree } from '@/api/permission'
import { getRolePermissions, assignPermissionsToRole } from '@/api/role'
import type { Role, Permission } from '@/types'

const props = defineProps<{
  visible: boolean
  role: Role | null
}>()

const emit = defineEmits<{
  'update:visible': [value: boolean]
  success: []
}>()

const loading = ref(false)
const loadingPermissions = ref(false)
const permissionTree = ref<Record<string, Permission[]>>({})
const selectedPermissionIds = ref<number[]>([])

const loadPermissions = async () => {
  if (!props.role) return
  loadingPermissions.value = true
  try {
    const [treeRes, rolePermissionsRes] = await Promise.all([
      getPermissionTree(),
      getRolePermissions(props.role.id)
    ])
    permissionTree.value = treeRes.data.tree
    selectedPermissionIds.value = rolePermissionsRes.data.map(p => p.id)
  } catch (error) {
    console.error('Failed to load permissions:', error)
  } finally {
    loadingPermissions.value = false
  }
}

const handleSubmit = async () => {
  if (!props.role) return
  loading.value = true
  try {
    await assignPermissionsToRole(props.role.id, selectedPermissionIds.value)
    ElMessage.success('权限分配成功')
    emit('update:visible', false)
    emit('success')
  } catch (error) {
    console.error('Failed to assign permissions:', error)
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.role-info {
  margin-bottom: 16px;
  color: #666;
}

.permission-tree {
  max-height: 400px;
  overflow-y: auto;
}

.permission-module {
  margin-bottom: 16px;
}

.module-header {
  font-weight: 600;
  margin-bottom: 8px;
  padding: 8px;
  background-color: #f5f7fa;
  border-radius: 4px;
}

.permission-checkbox {
  display: block;
  margin-left: 16px;
  margin-bottom: 8px;
}
</style>

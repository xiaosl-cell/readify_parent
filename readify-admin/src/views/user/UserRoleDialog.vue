<template>
  <el-dialog
    :model-value="visible"
    title="分配角色"
    width="500px"
    @update:model-value="$emit('update:visible', $event)"
  >
    <div v-if="user">
      <p class="user-info">用户: {{ user.username }}</p>
      <el-checkbox-group v-model="selectedRoleIds">
        <el-checkbox
          v-for="role in allRoles"
          :key="role.id"
          :value="role.id"
          :label="role.id"
          class="role-checkbox"
        >
          <div class="role-item">
            <span class="role-name">{{ role.name }}</span>
            <span class="role-code">({{ role.code }})</span>
          </div>
        </el-checkbox>
      </el-checkbox-group>
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
import { ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { assignRolesToUser } from '@/api/user'
import type { UserWithRoles, Role } from '@/types'

const props = defineProps<{
  visible: boolean
  user: UserWithRoles | null
  allRoles: Role[]
}>()

const emit = defineEmits<{
  'update:visible': [value: boolean]
  success: []
}>()

const loading = ref(false)
const selectedRoleIds = ref<number[]>([])

watch(() => props.user, (newUser) => {
  if (newUser) {
    selectedRoleIds.value = newUser.roles?.map(r => r.id) || []
  }
}, { immediate: true })

const handleSubmit = async () => {
  if (!props.user) return
  loading.value = true
  try {
    await assignRolesToUser(props.user.id, selectedRoleIds.value)
    ElMessage.success('角色分配成功')
    emit('update:visible', false)
    emit('success')
  } catch (error) {
    console.error('Failed to assign roles:', error)
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.user-info {
  margin-bottom: 16px;
  color: #666;
}

.role-checkbox {
  display: block;
  margin-bottom: 12px;
}

.role-item {
  display: inline-flex;
  align-items: center;
}

.role-name {
  font-weight: 500;
}

.role-code {
  color: #999;
  margin-left: 8px;
  font-size: 12px;
}
</style>

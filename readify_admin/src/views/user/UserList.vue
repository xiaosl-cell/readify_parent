<template>
  <div class="user-list">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>用户列表</span>
        </div>
      </template>

      <el-table :data="users" v-loading="loading" stripe>
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="username" label="用户名" />
        <el-table-column prop="email" label="邮箱" />
        <el-table-column prop="nickname" label="昵称" />
        <el-table-column label="角色" width="250">
          <template #default="{ row }">
            <el-tag v-for="role in row.roles" :key="role.id" class="role-tag" size="small">
              {{ role.name }}
            </el-tag>
            <span v-if="!row.roles?.length" class="no-role">暂无角色</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="120">
          <template #default="{ row }">
            <el-button type="primary" link @click="openRoleDialog(row)">
              分配角色
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <UserRoleDialog
      v-model:visible="roleDialogVisible"
      :user="selectedUser"
      :all-roles="allRoles"
      @success="loadUsers"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { getUsersWithRoles } from '@/api/user'
import { getAllRoles } from '@/api/role'
import type { UserWithRoles, Role } from '@/types'
import UserRoleDialog from './UserRoleDialog.vue'

const loading = ref(false)
const users = ref<UserWithRoles[]>([])
const allRoles = ref<Role[]>([])
const roleDialogVisible = ref(false)
const selectedUser = ref<UserWithRoles | null>(null)

const loadUsers = async () => {
  loading.value = true
  try {
    const res = await getUsersWithRoles()
    users.value = res.data
  } catch (error) {
    console.error('Failed to load users:', error)
  } finally {
    loading.value = false
  }
}

const loadRoles = async () => {
  try {
    const res = await getAllRoles()
    allRoles.value = res.data
  } catch (error) {
    console.error('Failed to load roles:', error)
  }
}

const openRoleDialog = (user: UserWithRoles) => {
  selectedUser.value = user
  roleDialogVisible.value = true
}

onMounted(() => {
  loadUsers()
  loadRoles()
})
</script>

<style scoped>
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.role-tag {
  margin-right: 4px;
}

.no-role {
  color: #999;
  font-size: 12px;
}
</style>

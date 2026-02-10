<template>
  <div class="role-list">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>角色列表</span>
          <el-button type="primary" @click="openCreateDialog">新增角色</el-button>
        </div>
      </template>

      <div class="search-bar">
        <el-input
          v-model="keyword"
          placeholder="搜索角色名称或编码"
          clearable
          style="width: 300px"
          @keyup.enter="loadRoles"
        >
          <template #append>
            <el-button @click="loadRoles">
              <el-icon><Search /></el-icon>
            </el-button>
          </template>
        </el-input>
      </div>

      <el-table :data="roles" v-loading="loading" stripe>
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="code" label="编码" />
        <el-table-column prop="name" label="名称" />
        <el-table-column prop="description" label="描述" />
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.enabled ? 'success' : 'danger'">
              {{ row.enabled ? '启用' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="220">
          <template #default="{ row }">
            <el-button type="primary" link @click="openEditDialog(row)">编辑</el-button>
            <el-button type="primary" link @click="openPermissionDialog(row)">分配权限</el-button>
            <el-button type="danger" link @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-pagination
        v-model:current-page="page"
        v-model:page-size="size"
        :total="total"
        :page-sizes="[10, 20, 50]"
        layout="total, sizes, prev, pager, next"
        class="pagination"
        @change="loadRoles"
      />
    </el-card>

    <RoleForm
      v-model:visible="formDialogVisible"
      :role="selectedRole"
      @success="loadRoles"
    />

    <RolePermissionDialog
      v-model:visible="permissionDialogVisible"
      :role="selectedRole"
      @success="loadRoles"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search } from '@element-plus/icons-vue'
import { getRolesPage, deleteRole } from '@/api/role'
import type { Role } from '@/types'
import RoleForm from './RoleForm.vue'
import RolePermissionDialog from './RolePermissionDialog.vue'

const loading = ref(false)
const roles = ref<Role[]>([])
const page = ref(1)
const size = ref(10)
const total = ref(0)
const keyword = ref('')
const formDialogVisible = ref(false)
const permissionDialogVisible = ref(false)
const selectedRole = ref<Role | null>(null)

const loadRoles = async () => {
  loading.value = true
  try {
    const res = await getRolesPage(page.value, size.value, keyword.value)
    roles.value = res.data.items
    total.value = res.data.total
  } catch (error) {
    console.error('Failed to load roles:', error)
  } finally {
    loading.value = false
  }
}

const openCreateDialog = () => {
  selectedRole.value = null
  formDialogVisible.value = true
}

const openEditDialog = (role: Role) => {
  selectedRole.value = role
  formDialogVisible.value = true
}

const openPermissionDialog = (role: Role) => {
  selectedRole.value = role
  permissionDialogVisible.value = true
}

const handleDelete = async (role: Role) => {
  try {
    await ElMessageBox.confirm(`确定要删除角色 "${role.name}" 吗？`, '确认删除', {
      type: 'warning'
    })
    await deleteRole(role.id)
    ElMessage.success('删除成功')
    loadRoles()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('Failed to delete role:', error)
    }
  }
}

onMounted(() => {
  loadRoles()
})
</script>

<style scoped>
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.search-bar {
  margin-bottom: 16px;
}

.pagination {
  margin-top: 16px;
  justify-content: flex-end;
}
</style>

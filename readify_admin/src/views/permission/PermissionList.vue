<template>
  <div class="permission-list">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>权限列表</span>
          <el-button type="primary" @click="openCreateDialog">新增权限</el-button>
        </div>
      </template>

      <div class="search-bar">
        <el-input
          v-model="keyword"
          placeholder="搜索权限名称、编码或模块"
          clearable
          style="width: 300px"
          @keyup.enter="loadPermissions"
        >
          <template #append>
            <el-button @click="loadPermissions">
              <el-icon><Search /></el-icon>
            </el-button>
          </template>
        </el-input>
      </div>

      <el-table :data="permissions" v-loading="loading" stripe>
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="code" label="编码" />
        <el-table-column prop="name" label="名称" />
        <el-table-column prop="module" label="模块" width="120" />
        <el-table-column prop="description" label="描述" />
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.enabled ? 'success' : 'danger'">
              {{ row.enabled ? '启用' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150">
          <template #default="{ row }">
            <el-button type="primary" link @click="openEditDialog(row)">编辑</el-button>
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
        @change="loadPermissions"
      />
    </el-card>

    <PermissionForm
      v-model:visible="formDialogVisible"
      :permission="selectedPermission"
      @success="loadPermissions"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search } from '@element-plus/icons-vue'
import { getPermissionsPage, deletePermission } from '@/api/permission'
import type { Permission } from '@/types'
import PermissionForm from './PermissionForm.vue'

const loading = ref(false)
const permissions = ref<Permission[]>([])
const page = ref(1)
const size = ref(10)
const total = ref(0)
const keyword = ref('')
const formDialogVisible = ref(false)
const selectedPermission = ref<Permission | null>(null)

const loadPermissions = async () => {
  loading.value = true
  try {
    const res = await getPermissionsPage(page.value, size.value, keyword.value)
    permissions.value = res.data.items
    total.value = res.data.total
  } catch (error) {
    console.error('Failed to load permissions:', error)
  } finally {
    loading.value = false
  }
}

const openCreateDialog = () => {
  selectedPermission.value = null
  formDialogVisible.value = true
}

const openEditDialog = (permission: Permission) => {
  selectedPermission.value = permission
  formDialogVisible.value = true
}

const handleDelete = async (permission: Permission) => {
  try {
    await ElMessageBox.confirm(`确定要删除权限 "${permission.name}" 吗？`, '确认删除', {
      type: 'warning'
    })
    await deletePermission(permission.id)
    ElMessage.success('删除成功')
    loadPermissions()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('Failed to delete permission:', error)
    }
  }
}

onMounted(() => {
  loadPermissions()
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

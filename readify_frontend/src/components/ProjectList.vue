<template>
  <div class="projects-list">
    <el-table 
      :data="projects" 
      style="width: 100%"
      @cell-click="handleTableCellClick"
    >
      <el-table-column prop="name" label="工程名称" min-width="130">
        <template #default="{ row }">
          <el-tooltip
            v-if="row.name.length > 15"
            :content="row.name"
            placement="top"
            :show-after="500"
            popper-class="custom-tooltip"
          >
            <template #content>
              <div class="tooltip-content">
                {{ row.name }}
              </div>
            </template>
            <div class="project-name-cell">
              <span class="project-name text-ellipsis">{{ row.name.slice(0, 15) + '...' }}</span>
            </div>
          </el-tooltip>
          <div v-else class="project-name-cell">
            <span class="project-name">{{ row.name }}</span>
          </div>
        </template>
      </el-table-column>
      <el-table-column prop="description" label="描述" min-width="380">
        <template #default="{ row }">
          <el-tooltip
            v-if="(row.description || '暂无描述').length > 45"
            :content="row.description || '暂无描述'"
            placement="top"
            :show-after="500"
            popper-class="custom-tooltip"
          >
            <template #content>
              <div class="tooltip-content">
                {{ row.description || '暂无描述' }}
              </div>
            </template>
            <span class="project-description-cell text-ellipsis-2">{{ (row.description || '暂无描述').slice(0, 45) + '...' }}</span>
          </el-tooltip>
          <span v-else class="project-description-cell">{{ row.description || '暂无描述' }}</span>
        </template>
      </el-table-column>
      <el-table-column prop="sourceCount" label="文档数量" width="120" align="center">
        <template #default="{ row }">
          <el-tag size="small" :type="row.sourceCount ? 'success' : 'info'">
            {{ row.sourceCount || 0 }} 个文档
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="createTime" label="创建时间" width="180" align="center">
        <template #default="{ row }">
          <span>{{ formatTime(row.createTime) }}</span>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="120" align="center">
        <template #default="{ row }">
          <div @click.stop>
            <el-dropdown trigger="click">
              <el-button type="primary" text>
                <el-icon><More /></el-icon>
              </el-button>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item @click.stop="$emit('edit', row)">编辑</el-dropdown-item>
                  <el-dropdown-item @click.stop="$emit('delete', row)" class="text-danger">
                    删除
                  </el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </div>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<script lang="ts" setup>
import { More } from '@element-plus/icons-vue'
import type { ProjectVO } from '@/types/project'

defineProps<{
  projects: ProjectVO[]
}>()

const emit = defineEmits<{
  (e: 'click', project: ProjectVO): void
  (e: 'edit', project: ProjectVO): void
  (e: 'delete', project: ProjectVO): void
}>()

// 格式化时间
const formatTime = (timestamp: number) => {
  return new Date(timestamp).toLocaleDateString()
}

// 处理表格单元格点击
const handleTableCellClick = (row: ProjectVO, column: any) => {
  // 如果点击的是操作列，不做任何处理
  if (column.label === '操作') {
    return
  }
  // 其他列使用相同的处理逻辑
  emit('click', row)
}
</script>

<style scoped>
.projects-list {
  background: #ffffff;
  border-radius: 8px;
  margin-top: 16px;
}

.project-name-cell {
  cursor: pointer;
  color: #409EFF;
  font-weight: 500;
  width: 100%;
}

.project-name-cell:hover {
  text-decoration: underline;
}

.project-description-cell {
  color: #606266;
  width: 100%;
  display: inline-block;
  line-height: 1.4;
}

:deep(.el-table) {
  border-radius: 0;
  overflow: visible;
  box-shadow: none;
}

:deep(.el-table th) {
  background: #ffffff;
  font-weight: 600;
  font-size: 15px;
  border-bottom: 1px solid #EBEEF5;
  color: #303133;
}

:deep(.el-table td) {
  border-bottom: 1px solid #EBEEF5;
}

:deep(.el-table--enable-row-hover .el-table__body tr:hover > td) {
  background-color: #fafafa;
}

:deep(.el-table::before) {
  display: none;
}

.text-ellipsis {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.text-ellipsis-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  text-overflow: ellipsis;
  word-break: break-all;
}

.text-danger {
  color: #f56c6c;
}

:deep(.custom-tooltip) {
  max-width: 300px !important;
  padding: 0 !important;
}

:deep(.custom-tooltip .el-tooltip__content) {
  padding: 0 !important;
}

.tooltip-content {
  max-width: 300px;
  padding: 8px 12px;
  font-size: 14px;
  line-height: 1.5;
  color: #ffffff;
  text-align: left;
  word-break: break-word;
  white-space: pre-wrap;
}
</style> 
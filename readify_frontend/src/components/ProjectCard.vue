<template>
  <el-card 
    class="project-card" 
    shadow="hover" 
    @click="$emit('click', project)"
    :style="{
      background: `linear-gradient(135deg, ${colorStyle.light} 0%, ${colorStyle.dark} 100%)`
    }"
  >
    <template #header>
      <div class="card-header">
        <el-tooltip
          v-if="project.name.length > 9"
          :content="project.name"
          placement="top"
          :show-after="500"
          popper-class="custom-tooltip"
        >
          <template #content>
            <div class="tooltip-content">
              {{ project.name }}
            </div>
          </template>
          <span class="project-name text-ellipsis" :title="project.name">
            {{ project.name.slice(0, 9) + '...' }}
          </span>
        </el-tooltip>
        <span v-else class="project-name">{{ project.name }}</span>
        <div @click.stop>
          <el-dropdown>
            <el-button type="primary" text>
              <el-icon><More /></el-icon>
            </el-button>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item @click.stop="$emit('edit', project)">编辑</el-dropdown-item>
                <el-dropdown-item @click.stop="$emit('delete', project)" class="text-danger">
                  删除
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </div>
    </template>
    <div class="project-content">
      <el-tooltip
        v-if="(project.description || '暂无描述').length > 70"
        :content="project.description || '暂无描述'"
        placement="top"
        :show-after="500"
        popper-class="custom-tooltip"
      >
        <template #content>
          <div class="tooltip-content">
            {{ project.description || '暂无描述' }}
          </div>
        </template>
        <p class="project-description text-ellipsis-2">
          {{ (project.description || '暂无描述').slice(0, 70) + '...' }}
        </p>
      </el-tooltip>
      <p v-else class="project-description">
        {{ project.description || '暂无描述' }}
      </p>
      <div class="project-footer">
        <span class="create-time">创建于 {{ formatTime(project.createTime) }}</span>
      </div>
    </div>
  </el-card>
</template>

<script lang="ts" setup>
import { computed } from 'vue'
import { More } from '@element-plus/icons-vue'
import type { ProjectVO } from '@/types/project'

const props = defineProps<{
  project: ProjectVO
  colorIndex: number
  softColors: { light: string, dark: string }[]
}>()

defineEmits<{
  (e: 'click', project: ProjectVO): void
  (e: 'edit', project: ProjectVO): void
  (e: 'delete', project: ProjectVO): void
}>()

const colorStyle = computed(() => {
  return props.softColors[props.colorIndex % props.softColors.length]
})

// 格式化时间
const formatTime = (timestamp: number) => {
  return new Date(timestamp).toLocaleDateString()
}
</script>

<style scoped>
.project-card {
  height: 100%;
  border-radius: 12px;
  transition: all 0.3s ease;
  border: none;
  display: flex;
  flex-direction: column;
  min-height: 220px;
  position: relative;
  outline: none !important;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.08);
}

.project-card:deep(.el-card__body) {
  padding: 0;
  background: transparent !important;
  border-radius: 0 0 8px 8px;
  border: none !important;
  outline: none !important;
}

.project-card:deep(.el-card__header) {
  padding: 0;
  background: transparent !important;
  border: none !important;
  outline: none !important;
}

.project-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 12px 32px rgba(0, 0, 0, 0.12) !important;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 20px;
  background: transparent;
  border-radius: 8px 8px 0 0;
  border-bottom: 1px solid rgba(0, 0, 0, 0.05);
}

.project-name {
  font-size: 16px;
  font-weight: 500;
  color: #303133;
  display: inline-block;
  max-width: calc(100% - 40px);
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

.project-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  padding: 0;
  background: transparent;
  position: relative;
  min-height: 180px;
}

.project-description {
  flex: 1;
  margin: 0;
  padding: 20px 24px;
  font-size: 14px;
  color: #606266;
  line-height: 1.6;
  min-height: 100px;
  max-height: 140px;
  text-align: left;
}

.project-footer {
  padding: 8px 20px;
  border-top: 1px solid rgba(0, 0, 0, 0.05);
  margin: 0;
  background: transparent;
  border-radius: 0 0 12px 12px;
  height: 32px;
  display: flex;
  align-items: center;
}

.create-time {
  font-size: 12px;
  color: #909399;
  line-height: 1;
}

.text-danger {
  color: #f56c6c;
}

:deep(.el-button--primary) {
  border: none;
  padding: 10px 20px;
  height: auto;
  transition: all 0.3s;
}

:deep(.el-button--text) {
  padding: 4px;
  color: #909399;
  border: none;
  background: transparent !important;
  box-shadow: none !important;
}

:deep(.el-button--text:hover) {
  color: #606266;
  background: transparent !important;
}

:deep(.el-dropdown-menu__item) {
  padding: 8px 16px;
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
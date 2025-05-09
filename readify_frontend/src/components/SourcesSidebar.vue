<template>
  <div class="sidebar sources-sidebar" :class="{ 'collapsed': isCollapsed }">
    <div class="sidebar-header">
      <h3>书源</h3>
      <el-button 
        type="link" 
        class="collapse-btn"
        @click="$emit('toggle-collapse')"
      >
        <el-icon><Fold v-if="!isCollapsed" /><Expand v-else /></el-icon>
      </el-button>
    </div>
    <div class="sidebar-content">
      <div class="sources-actions">
        <el-button class="add-source-btn" plain @click="$emit('add-source')">
          <el-icon><Plus /></el-icon>
          <span>添加书源</span>
        </el-button>
        <div class="select-all-container">
          <span>全选</span>
          <el-checkbox v-model="selectAll" @change="handleSelectAllChange" />
        </div>
      </div>
      <div class="sources-list">
        <div v-for="source in sources" :key="source.id" class="source-item">
          <div class="source-name" :data-ext="getFileExtension(source.originalName)">
            <span>{{ source.originalName }}</span>
          </div>
          <div class="source-status">
            <el-checkbox 
              v-if="!source.loading" 
              v-model="source.selected" 
              @change="handleSourceSelect" 
            />
            <el-icon v-else class="el-loading is-loading">
              <Loading />
            </el-icon>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script lang="ts" setup>
import { ref, watch } from 'vue'
import { Fold, Expand, Plus, Loading } from '@element-plus/icons-vue'
import type { FileVO } from '@/types/file'

interface SourceFile extends FileVO {
  selected: boolean;
  vectorized: boolean;
  loading: boolean;
}

const props = defineProps<{
  sources: SourceFile[]
  isCollapsed: boolean
}>()

const emit = defineEmits<{
  (e: 'toggle-collapse'): void
  (e: 'add-source'): void
  (e: 'update:sources', sources: SourceFile[]): void
}>()

const selectAll = ref(false)

// 监听sources变化，更新全选状态
watch(() => props.sources, (newSources) => {
  selectAll.value = newSources.length > 0 && newSources.every(source => source.selected)
}, { deep: true, immediate: true })

// 全选/取消全选
const handleSelectAllChange = (val: boolean) => {
  const updatedSources = props.sources.map(source => ({
    ...source,
    selected: val
  }))
  emit('update:sources', updatedSources)
}

// 单个书源选择
const handleSourceSelect = () => {
  emit('update:sources', [...props.sources])
}

// 获取文件扩展名
const getFileExtension = (filename: string) => {
  const ext = filename.split('.').pop()
  return ext ? ext.toUpperCase() : ''
}
</script>

<style scoped>
/* 侧边栏通用样式 */
.sidebar {
  width: 300px;
  background: #ffffff;
  border-radius: 8px;
  display: flex;
  flex-direction: column;
  transition: all 0.3s ease;
  flex-shrink: 0;
}

.sidebar.collapsed {
  width: 64px;
}

.sidebar.collapsed .sidebar-header h3 {
  display: none;
}

.sidebar-header {
  height: 56px;
  padding: 0 16px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid #f0f0f0;
}

.sidebar-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 500;
  color: #303133;
}

.collapse-btn {
  padding: 0;
  border: none;
  transition: all 0.3s ease;
  background: transparent;
  outline: none !important;
  position: relative;
  width: 32px;
  height: 32px;
  min-height: 32px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0;
}

.collapse-btn:hover {
  box-shadow: 0 0 16px rgba(0, 0, 0, 0.15);
  transform: scale(1.05);
}

.collapse-btn:active {
  box-shadow: 0 0 12px rgba(0, 0, 0, 0.2);
  transform: scale(0.95);
}

.collapse-btn .el-icon {
  margin: 0;
  width: 16px;
  height: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1;
  color: #606266;
}

.collapse-btn:deep(.el-button) {
  margin: 0;
  padding: 0;
  background: transparent !important;
  outline: none !important;
  border: none;
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.collapse-btn:deep(.el-button:hover),
.collapse-btn:deep(.el-button:focus),
.collapse-btn:deep(.el-button:active) {
  background: transparent !important;
  border: none;
  outline: none;
  box-shadow: none;
  opacity: 1;
  margin: 0;
  padding: 0;
}

.collapse-btn:deep(.el-button .el-icon) {
  opacity: 1 !important;
}

.collapse-btn:deep(.el-button.is-text) {
  border: none;
  outline: none;
  opacity: 1;
}

.collapse-btn:deep(.el-button.is-text:hover),
.collapse-btn:deep(.el-button.is-text:focus),
.collapse-btn:deep(.el-button.is-text:focus-visible),
.collapse-btn:deep(.el-button.is-text:active) {
  border: none;
  outline: none;
  box-shadow: none;
  opacity: 1;
  background: transparent !important;
}

.sidebar-content {
  flex: 1;
  overflow-y: auto;
}

.sources-actions {
  padding: 16px;
}

.add-source-btn {
  width: 100%;
  margin-bottom: 16px;
  border-radius: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  transition: all 0.3s ease;
}

.add-source-btn .el-icon {
  margin: 0;
  display: flex;
  align-items: center;
  justify-content: center;
}

.add-source-btn span {
  transition: opacity 0.3s ease;
}

.add-source-btn:deep(.el-button.el-button--default.is-plain) {
  --el-button-bg-color: #ffffff;
  --el-button-border-color: #dcdfe6;
  --el-button-text-color: #606266;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0;
  border-radius: 40px;
}

.add-source-btn:deep(.el-button.el-button--default.is-plain:hover),
.add-source-btn:deep(.el-button.el-button--default.is-plain:focus) {
  background-color: #ffffff;
  border-color: #dcdfe6;
  color: #606266;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
  outline: none;
}

.add-source-btn:deep(.el-button.el-button--default.is-plain:active) {
  background-color: #ffffff;
  border-color: #dcdfe6;
  color: #606266;
  box-shadow: none;
  outline: none;
}

.add-source-btn:deep(.el-button.el-button--default.is-plain:focus-visible) {
  outline: none;
  border-color: #dcdfe6;
}

/* 折叠状态下的样式 */
.sidebar.collapsed .add-source-btn {
  width: 32px;
  height: 32px;
  min-height: 32px;
  margin: 12px auto;
  padding: 0;
  border: none;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s ease;
  background: transparent;
}

.sidebar.collapsed .add-source-btn:hover {
  box-shadow: 0 0 16px rgba(0, 0, 0, 0.15);
  transform: scale(1.05);
  border: none;
}

.sidebar.collapsed .add-source-btn:active {
  box-shadow: 0 0 12px rgba(0, 0, 0, 0.2);
  transform: scale(0.95);
  border: none;
}

.sidebar.collapsed .add-source-btn .el-icon {
  margin: 0;
  width: 16px;
  height: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.sidebar.collapsed .add-source-btn span:not(.el-icon) {
  width: 0;
  opacity: 0;
  overflow: hidden;
  display: none;
}

.sidebar.collapsed .add-source-btn:deep(.el-button) {
  padding: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  border: none;
  background: transparent;
}

.sidebar.collapsed .add-source-btn:deep(.el-button:hover),
.sidebar.collapsed .add-source-btn:deep(.el-button:focus),
.sidebar.collapsed .add-source-btn:deep(.el-button:active),
.sidebar.collapsed .add-source-btn:deep(.el-button:focus-visible) {
  border: none;
  outline: none;
  box-shadow: none;
  background: transparent;
}

.sidebar.collapsed .add-source-btn:deep(.el-button.el-button--default.is-plain) {
  border: none;
}

.sidebar.collapsed .add-source-btn:deep(.el-button.el-button--default.is-plain:hover),
.sidebar.collapsed .add-source-btn:deep(.el-button.el-button--default.is-plain:focus),
.sidebar.collapsed .add-source-btn:deep(.el-button.el-button--default.is-plain:active),
.sidebar.collapsed .add-source-btn:deep(.el-button.el-button--default.is-plain:focus-visible) {
  border: none;
  outline: none;
  background: transparent;
}

.sidebar.collapsed .select-all-container {
  display: none;
}

.sidebar.collapsed .sources-list {
  padding: 0 8px;
}

.sidebar.collapsed .source-item {
  justify-content: center;
  padding: 10px 0;
  margin: 0;
  width: 100%;
}

.sidebar.collapsed .source-item .source-name {
  width: 100%;
  margin: 0;
  text-align: center;
  display: flex;
  justify-content: center;
}

/* 只显示文件扩展名 */
.sidebar.collapsed .source-item .source-name::before {
  content: attr(data-ext);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border: 1px solid #f56c6c;
  border-radius: 4px;
  font-size: 12px;
  color: #f56c6c;
  font-weight: 500;
  padding: 0;
}

.sidebar.collapsed .source-item .source-name > span {
  display: none;
}

.sidebar.collapsed .source-item .el-checkbox {
  display: none;
}

/* 折叠状态下隐藏加载图标，但保持布局 */
.sidebar.collapsed .source-item .source-status {
  display: none;
}

.select-all-container {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 14px 16px;
  color: #606266;
  font-size: 14px;
  border-bottom: 1px solid #f0f0f0;
  margin: 0 -16px;
}

.select-all-container > span {
  flex: 1;
}

.select-all-container :deep(.el-checkbox) {
  width: 32px;
  display: flex;
  justify-content: center;
  margin-right: 0;
}

.select-all-container :deep(.el-checkbox .el-checkbox__input) {
  margin-left: 0;
}

.sources-list {
  padding: 0 16px;
}

.source-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 14px 0;
  cursor: pointer;
  transition: all 0.3s ease;
  border-radius: 4px;
  margin: 2px 0;
}

.source-item .source-name {
  color: #303133;
  font-size: 14px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  margin-right: 12px;
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1;
}

.source-item .source-name::before {
  content: attr(data-ext);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border: 1px solid #f56c6c;
  border-radius: 4px;
  font-size: 12px;
  color: #f56c6c;
  font-weight: 500;
  flex-shrink: 0;
}

.source-item .source-name > span {
  color: #303133;
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  font-family: 'Montserrat', sans-serif;
  font-size: 14px;
  font-weight: 500;
  letter-spacing: 0.2px;
}

.source-item .source-status {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
}

.source-item .el-loading {
  font-size: 16px;
  color: #909399;
}

.source-item .el-loading.is-loading {
  animation: rotating 2s linear infinite;
}

.source-item:hover {
  background-color: #f5f7fa;
  padding-left: 8px;
  padding-right: 8px;
  margin-left: -8px;
  margin-right: -8px;
}

.source-item :deep(.el-checkbox) {
  margin-right: 0;
  width: 32px;
  display: flex;
  justify-content: center;
}

.source-item :deep(.el-checkbox .el-checkbox__input) {
  transition: all 0.3s ease;
}

.source-item:hover :deep(.el-checkbox .el-checkbox__input:not(.is-checked) .el-checkbox__inner) {
  border-color: #303133;
}

@keyframes rotating {
  0% {
    transform: rotate(0deg);
  }
  100% {
    transform: rotate(360deg);
  }
}

/* 通用复选框样式 */
.sources-sidebar :deep(.el-checkbox) {
  --el-checkbox-font-size: 14px;
  --el-checkbox-input-height: 16px;
  --el-checkbox-input-width: 16px;
  --el-checkbox-border-radius: 3px;
  --el-checkbox-checked-text-color: #303133;
  --el-checkbox-checked-bg-color: #303133;
  --el-checkbox-checked-border-color: #303133;
  margin-right: 0;
}

.sources-sidebar :deep(.el-checkbox .el-checkbox__input) {
  transition: all 0.3s ease;
}

.sources-sidebar :deep(.el-checkbox .el-checkbox__input .el-checkbox__inner) {
  display: flex;
  align-items: center;
  justify-content: center;
}

.sources-sidebar :deep(.el-checkbox .el-checkbox__input .el-checkbox__inner::after) {
  position: static;
  margin: auto;
  transform: rotate(45deg) scaleY(1.2);
  top: auto;
  left: auto;
  border-width: 2px;
}

.sources-sidebar :deep(.el-checkbox .el-checkbox__input:not(.is-checked) .el-checkbox__inner:hover) {
  border-color: #303133;
}
</style> 
<template>
  <div class="sidebar notebook-sidebar" :class="{ 'collapsed': isCollapsed }">
    <div class="sidebar-header">
      <h3>笔记本</h3>
      <el-button 
        type="link" 
        class="collapse-btn"
        @click="$emit('toggle-collapse')"
      >
        <el-icon><Fold v-if="!isCollapsed" /><Expand v-else /></el-icon>
      </el-button>
    </div>
    <div class="sidebar-content">
      <div class="notebook-actions">
        <el-button class="add-note-btn" plain @click="handleCreateNote">
          <el-icon><Plus /></el-icon>
          <span>创建笔记</span>
        </el-button>
      </div>
      
      <!-- 笔记列表 -->
      <div class="notebook-list" v-loading="loading">
        <el-empty v-if="!loading && mindMaps.length === 0" description="暂无笔记" />
        <div v-else class="note-items">
          <div 
            v-for="map in mindMaps" 
            :key="map.id" 
            class="note-item"
            @click="handleNoteClick(map)"
          >
            <el-icon><Memo /></el-icon>
            <span class="note-title">{{ map.title }}</span>
            
            <!-- 操作下拉按钮 -->
            <el-dropdown 
              trigger="click" 
              @command="(command) => handleCommand(command, map)"
              @click.stop
            >
              <el-button 
                type="text" 
                class="action-btn"
                @click.stop
              >
                <el-icon><MoreFilled /></el-icon>
              </el-button>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item command="open">
                    <el-icon><View /></el-icon>
                    <span>打开</span>
                  </el-dropdown-item>
                  <el-dropdown-item command="delete" divided>
                    <el-icon><Delete /></el-icon>
                    <span>删除</span>
                  </el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </div>
        </div>
      </div>
    </div>
    
    <!-- 创建笔记弹窗 -->
    <CreateNoteDialog ref="createNoteDialogRef" @created="loadMindMaps" />
  </div>
</template>

<script lang="ts" setup>
import { ref, onMounted, inject, watch } from 'vue'
import { Fold, Expand, Plus, Memo, MoreFilled, View, Delete } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import CreateNoteDialog from '@/components/CreateNoteDialog.vue'
import { getProjectMindMaps, deleteMindMap } from '@/api/mindmap'
import type { MindMapVO } from '@/types/mindmap'

defineProps<{
  isCollapsed: boolean
}>()

const emit = defineEmits<{
  (e: 'toggle-collapse'): void
  (e: 'select-note', note: MindMapVO): void
  (e: 'refresh'): void
}>()

// 从父组件注入projectId
const injectedProjectId = inject<Ref<number>>('projectId', ref(1))

// 创建笔记弹窗的引用
const createNoteDialogRef = ref()

// 思维导图列表
const mindMaps = ref<MindMapVO[]>([])
const loading = ref(false)

// 监听projectId变化，重新加载思维导图
watch(() => injectedProjectId.value, () => {
  loadMindMaps()
})

// 组件挂载时加载数据
onMounted(() => {
  loadMindMaps()
})

// 加载项目下的所有思维导图
const loadMindMaps = async () => {
  if (!injectedProjectId.value) return
  
  try {
    loading.value = true
    const res = await getProjectMindMaps(injectedProjectId.value)
    mindMaps.value = res.data || []
  } catch (error) {
    console.error('Failed to load mind maps:', error)
    ElMessage.error('加载笔记列表失败')
  } finally {
    loading.value = false
  }
}

// 处理创建笔记按钮点击
const handleCreateNote = () => {
  createNoteDialogRef.value.open()
}

// 处理笔记点击
const handleNoteClick = (note: MindMapVO) => {
  emit('select-note', note)
}

// 处理下拉菜单命令
const handleCommand = async (command: string, note: MindMapVO) => {
  switch (command) {
    case 'open':
      emit('select-note', note)
      break
    case 'delete':
      await handleDeleteNote(note)
      break
  }
}

// 处理删除笔记
const handleDeleteNote = async (note: MindMapVO) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除笔记 "${note.title}" 吗？此操作不可恢复。`,
      '提示',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    const res = await deleteMindMap(note.id)
    if (res.code === '200') {
      ElMessage.success('删除成功')
      loadMindMaps()
    } else {
      ElMessage.error(res.message || '删除失败')
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('Failed to delete mind map:', error)
      ElMessage.error('删除失败，请重试')
    }
  }
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

.notebook-actions {
  padding: 16px 16px 8px;
}

.add-note-btn {
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

.add-note-btn .el-icon {
  margin: 0;
  display: flex;
  align-items: center;
  justify-content: center;
}

.add-note-btn span {
  transition: opacity 0.3s ease;
}

.add-note-btn:deep(.el-button.el-button--default.is-plain) {
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

.add-note-btn:deep(.el-button.el-button--default.is-plain:hover),
.add-note-btn:deep(.el-button.el-button--default.is-plain:focus) {
  background-color: #ffffff;
  border-color: #dcdfe6;
  color: #606266;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
  outline: none;
}

.add-note-btn:deep(.el-button.el-button--default.is-plain:active) {
  background-color: #ffffff;
  border-color: #dcdfe6;
  color: #606266;
  box-shadow: none;
  outline: none;
}

.add-note-btn:deep(.el-button.el-button--default.is-plain:focus-visible) {
  outline: none;
  border-color: #dcdfe6;
}

/* 笔记列表样式 */
.notebook-list {
  padding: 0 16px 16px;
}

.note-items {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.note-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  border-radius: 8px;
  transition: all 0.2s ease;
  cursor: pointer;
  position: relative;
}

.note-item:hover {
  background-color: #f5f7fa;
}

.note-item .el-icon {
  font-size: 18px;
  color: #409EFF;
}

.note-title {
  font-size: 14px;
  font-weight: 500;
  color: #303133;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  flex: 1;
}

.action-btn {
  padding: 6px;
  height: 28px;
  width: 28px;
  min-width: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 4px;
  transition: background-color 0.2s ease;
}

.action-btn:hover {
  background-color: rgba(64, 158, 255, 0.1);
}

.action-btn .el-icon {
  font-size: 16px;
  color: #909399;
}

.note-item:hover .action-btn .el-icon {
  color: #606266;
}

.note-item:deep(.el-dropdown-menu__item) {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
}

.note-item:deep(.el-dropdown-menu__item .el-icon) {
  font-size: 16px;
}

/* 折叠状态下的样式 */
.sidebar.collapsed .add-note-btn {
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

.sidebar.collapsed .add-note-btn:hover {
  box-shadow: 0 0 16px rgba(0, 0, 0, 0.15);
  transform: scale(1.05);
  border: none;
}

.sidebar.collapsed .add-note-btn:active {
  box-shadow: 0 0 12px rgba(0, 0, 0, 0.2);
  transform: scale(0.95);
  border: none;
}

.sidebar.collapsed .add-note-btn .el-icon {
  margin: 0;
  width: 16px;
  height: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.sidebar.collapsed .add-note-btn span:not(.el-icon) {
  width: 0;
  opacity: 0;
  overflow: hidden;
  display: none;
}

.sidebar.collapsed .add-note-btn:deep(.el-button) {
  padding: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  border: none;
  background: transparent;
}

.sidebar.collapsed .add-note-btn:deep(.el-button:hover),
.sidebar.collapsed .add-note-btn:deep(.el-button:focus),
.sidebar.collapsed .add-note-btn:deep(.el-button:active),
.sidebar.collapsed .add-note-btn:deep(.el-button:focus-visible) {
  border: none;
  outline: none;
  box-shadow: none;
  background: transparent;
}

.sidebar.collapsed .add-note-btn:deep(.el-button.el-button--default.is-plain) {
  border: none;
}

.sidebar.collapsed .add-note-btn:deep(.el-button.el-button--default.is-plain:hover),
.sidebar.collapsed .add-note-btn:deep(.el-button.el-button--default.is-plain:focus),
.sidebar.collapsed .add-note-btn:deep(.el-button.el-button--default.is-plain:active),
.sidebar.collapsed .add-note-btn:deep(.el-button.el-button--default.is-plain:focus-visible) {
  border: none;
  outline: none;
  background: transparent;
}

.sidebar.collapsed .note-title {
  display: none;
}

.sidebar.collapsed .note-item {
  justify-content: center;
  padding: 10px 0;
}

.sidebar.collapsed .note-item:hover {
  background-color: transparent;
}

.sidebar.collapsed .note-item .el-icon {
  margin: 0;
}

.sidebar.collapsed .action-btn {
  display: none;
}
</style> 
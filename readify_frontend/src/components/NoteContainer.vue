<template>
  <div class="note-container">
    <div class="note-header">
      <div class="title-area">
        <h3>{{ title }}</h3>
        <span class="subtitle">笔记</span>
      </div>
      <div class="actions">
        <el-button 
          type="text" 
          class="edit-btn" 
          @click="toggleEditMode"
        >
          <el-icon><Edit /></el-icon>
          {{ isEditing ? '完成' : '编辑' }}
        </el-button>
        <el-button 
          type="text" 
          class="close-btn" 
          @click="$emit('close')"
        >
          <el-icon><Close /></el-icon>
        </el-button>
      </div>
    </div>
    <div class="note-content">
      <!-- 编辑模式 -->
      <div v-if="isEditing" class="editor-container">
        <el-input
          v-model="editableContent"
          type="textarea"
          :rows="25"
          resize="none"
          placeholder="请输入Markdown内容..."
          class="markdown-editor"
        />
      </div>
      <!-- 思维导图模式 -->
      <div v-else class="note-display">
        <div class="markmap-container" v-loading="markmapLoading">
          <div class="svg-container" ref="svgContainer"></div>
        </div>
        <!-- 思维导图下方的输入框 -->
        <div class="note-input">
          <div class="input-wrapper">
            <el-input
              v-model="inputContent"
              type="textarea"
              :rows="3"
              placeholder="在此输入内容..."
              resize="none"
              @keydown.enter.prevent="handleSendInput"
            />
            <div class="select-container">
              <el-select 
                v-model="chatMode" 
                size="small" 
                class="mode-select"
                disabled
                style="--el-select-border-radius: 40px; --el-select-input-focus-border-color: #409EFF; --el-border-radius-base: 40px; border-radius: 40px; --el-fill-color-light: rgb(237, 239, 250); --el-fill-color-blank: rgb(237, 239, 250); --el-fill-color: rgb(237, 239, 250); background-color: rgb(237, 239, 250);"
              >
                <template #prefix>
                  <el-icon><EditPen /></el-icon>
                </template>
                <el-option label="笔记模式" value="note">
                  <template #default>
                    <div style="display: flex; align-items: center;">
                      <el-icon><EditPen /></el-icon>
                      <span style="margin-left: 5px; font-size: 12px;">笔记模式</span>
                    </div>
                  </template>
                </el-option>
              </el-select>
              <el-select v-model="vendor" size="small" class="model-select"
                 style="--el-border-radius-base: 40px; border-radius: 40px; background-color: #ffffff; width: 240px;"
              >
                <template #prefix>
                  <el-icon v-if="vendor === 'OpenAI'"><Lightning /></el-icon>
                  <el-icon v-else-if="vendor === 'OpenAI-China'"><Connection /></el-icon>
                  <el-icon v-else-if="vendor === 'DeepSeek'"><Connection /></el-icon>
                  <el-icon v-else-if="vendor === 'Qwen'"><Connection /></el-icon>
                </template>
                <el-option label="OpenAI" value="OpenAI">
                  <template #default>
                    <div style="display: flex; align-items: center; min-width: 90px;">
                      <el-icon><Lightning /></el-icon>
                      <span style="margin-left: 5px; font-size: 12px; white-space: nowrap;">OpenAI</span>
                    </div>
                  </template>
                </el-option>
                <el-option label="OpenAI-China" value="OpenAI-China">
                  <template #default>
                    <div style="display: flex; align-items: center; min-width: 90px;">
                      <el-icon><Connection /></el-icon>
                      <span style="margin-left: 5px; font-size: 12px; white-space: nowrap;">OpenAI-China</span>
                    </div>
                  </template>
                </el-option>
                <el-option label="DeepSeek" value="DeepSeek">
                  <template #default>
                    <div style="display: flex; align-items: center; min-width: 90px;">
                      <el-icon><Connection /></el-icon>
                      <span style="margin-left: 5px; font-size: 12px; white-space: nowrap;">DeepSeek</span>
                    </div>
                  </template>
                </el-option>
                <el-option label="Qwen" value="Qwen">
                  <template #default>
                    <div style="display: flex; align-items: center; min-width: 90px;">
                      <el-icon><Connection /></el-icon>
                      <span style="margin-left: 5px; font-size: 12px; white-space: nowrap;">Qwen</span>
                    </div>
                  </template>
                </el-option>
              </el-select>
            </div>
            <el-button 
              class="send-btn"
              :class="{ 'can-send': inputContent.trim() }"
              :disabled="!inputContent.trim()"
              @click="handleSendInput"
            >
              <span class="arrow">➜</span>
            </el-button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script lang="ts" setup>
import { ref, computed, onMounted, onBeforeUnmount, defineProps, defineEmits, watch, nextTick } from 'vue'
import { Close, Edit, EditPen, Lightning, Connection } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { marked } from 'marked'

// 配置marked选项
marked.setOptions({
  breaks: true,    // 支持GitHub风格的换行
  gfm: true,       // 启用GitHub风格的markdown
  sanitize: false, // 允许HTML标签
});

// 定义props
const props = defineProps<{
  title: string
  content: string
  visible: boolean
}>()

// 定义emit事件
const emit = defineEmits<{
  (e: 'close'): void
  (e: 'update:visible', value: boolean): void
  (e: 'save', content: string): void
  (e: 'send-input', input: string, mode: string, vendor: string): void
}>()

// 编辑状态
const isEditing = ref(false)

// 可编辑的内容
const editableContent = ref('')

// 思维导图下方输入框的内容
const inputContent = ref('')

// 选择框的响应式变量
const chatMode = ref('note') // 固定笔记模式
const vendor = ref('OpenAI') // 默认OpenAI模型

// 处理输入框发送
const handleSendInput = () => {
  if (!inputContent.value.trim()) return
  
  // 发送输入内容给父组件，同时传递模式和模型
  emit('send-input', inputContent.value, chatMode.value, vendor.value)
  
  // 清空输入框
  inputContent.value = ''
}

// 思维导图状态
const markmapLoading = ref(false)
const svgContainer = ref<HTMLElement | null>(null)

// 切换编辑模式
const toggleEditMode = () => {
  if (isEditing.value) {
    // 保存编辑内容
    emit('save', editableContent.value)
    ElMessage.success('笔记保存成功')
    
    // 退出编辑模式后，重新渲染思维导图
    nextTick(() => {
      renderMarkmap()
    })
  } else {
    // 进入编辑模式，设置当前内容
    editableContent.value = props.content
  }
  isEditing.value = !isEditing.value
}

// 渲染思维导图
const renderMarkmap = async () => {
  if (!svgContainer.value) return
  
  try {
    markmapLoading.value = true
    
    // 清空容器
    svgContainer.value.innerHTML = ''
    
    // 创建新的脚本元素以动态加载库
    const createScript = (src: string): Promise<void> => {
      return new Promise((resolve, reject) => {
        const script = document.createElement('script')
        script.src = src
        script.onload = () => resolve()
        script.onerror = (e) => reject(e)
        document.head.appendChild(script)
      })
    }
    
    // 检查是否已经加载了必要的库
    if (!window.d3 || !window.markmap) {
      console.log('Loading required libraries...')
      // 加载D3和markmap
      await createScript('https://cdn.jsdelivr.net/npm/d3@7')
      await createScript('https://cdn.jsdelivr.net/npm/markmap-view')
      await createScript('https://cdn.jsdelivr.net/npm/markmap-lib')
    }
    
    // 创建SVG元素
    const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg')
    // 获取容器高度 - 减去输入框高度
    const containerHeight = svgContainer.value.offsetHeight
    svg.setAttribute('style', `width: 100%; height: 100%; min-height: ${containerHeight}px;`)
    svgContainer.value.appendChild(svg)
    
    // 使用全局对象
    const { Transformer } = window.markmap
    const { Markmap } = window.markmap
    
    // 转换Markdown为mind map数据
    const transformer = new Transformer()
    const { root } = transformer.transform(props.content)
    
    // 创建markmap并渲染到SVG
    const mm = Markmap.create(svg, { 
      autoFit: true, 
      duration: 500,
      spacingVertical: 20,      // 增加垂直间距
      spacingHorizontal: 120,   // 增加水平间距
      maxWidth: 500,            // 限制节点最大宽度
      zoom: true,               // 允许缩放
      pan: true                 // 允许平移
    }, root)
    
    // 确保图自适应SVG大小
    setTimeout(() => mm.fit(), 300)
    
  } catch (error) {
    console.error('Failed to render markmap:', error)
    ElMessage.error('加载思维导图失败: ' + (error instanceof Error ? error.message : String(error)))
  } finally {
    markmapLoading.value = false
  }
}

// 监听content属性变化
watch(() => props.content, (newContent) => {
  if (!isEditing.value) {
    editableContent.value = newContent
    renderMarkmap()
  }
})

// 监听visible prop变化
watch(() => props.visible, (newValue) => {
  if (!newValue) {
    emit('close')
    isEditing.value = false
  } else {
    // 当显示组件时，渲染思维导图
    nextTick(() => {
      renderMarkmap()
    })
  }
})

// 监听窗口大小变化
const handleResize = () => {
  if (!isEditing.value && svgContainer.value) {
    renderMarkmap()
  }
}

// 组件挂载时初始化
onMounted(() => {
  editableContent.value = props.content
  window.addEventListener('resize', handleResize)
  // 初始化时渲染思维导图
  nextTick(() => {
    renderMarkmap()
  })
})

// 组件卸载前清理
onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
})

// 为typescript声明全局window属性
declare global {
  interface Window {
    d3: any
    markmap: any
  }
}
</script>

<style scoped>
.note-container {
  flex: 1;
  background: #ffffff;
  border-radius: 8px;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.note-header {
  height: 56px;
  padding: 0 16px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid #f0f0f0;
  background: linear-gradient(135deg, #f8f9fa 0%, #ffffff 100%);
}

.title-area {
  display: flex;
  align-items: baseline;
  gap: 10px;
}

.note-header h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: #303133;
}

.subtitle {
  color: #909399;
  font-size: 14px;
}

.actions {
  display: flex;
  gap: 8px;
}

.edit-btn,
.close-btn {
  padding: 6px;
  color: #909399;
}

.edit-btn:hover,
.close-btn:hover {
  color: #606266;
}

.note-content {
  flex: 1;
  padding: 16px;
  overflow-y: auto;
  position: relative;
  display: flex;
  flex-direction: column;
}

.editor-container {
  height: 100%;
}

.markdown-editor {
  height: 100%;
  font-family: monospace;
  line-height: 1.6;
}

.note-display {
  flex: 1;
  display: flex;
  flex-direction: column;
  height: 100%;
}

.markmap-container {
  flex: 1;
  width: 100%;
  min-height: 400px;
  position: relative;
}

.svg-container {
  width: 100%;
  height: 100%;
  min-height: 400px;
}

/* 思维导图下方输入区域样式 */
.note-input {
  margin-top: 16px;
  border-top: 1px solid #f0f0f0;
  padding-top: 16px;
}

.input-wrapper {
  position: relative;
  border-radius: 8px;
  background-color: #ffffff;
}

.note-input :deep(.el-textarea__inner) {
  resize: none;
  border-radius: 8px;
  padding: 12px 60px 12px 12px;
  padding-bottom: 40px; /* 增加底部内边距，为选择框腾出空间 */
  font-size: 14px;
  line-height: 1.6;
  min-height: 24px !important;
}

.select-container {
  position: absolute;
  left: 12px;
  bottom: 10px;
  display: flex;
  gap: 8px;
  z-index: 2;
}

/* 确保model-select在NoteContainer中的宽度固定 */
.model-select {
  width: 240px !important;
}

.model-select :deep(.el-input__wrapper) {
  width: 240px !important;
}

.send-btn {
  position: absolute;
  right: 12px;
  top: 12px;
  width: 40px;
  height: 40px;
  min-height: 40px;
  padding: 0;
  border: none;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: rgb(160, 172, 255);
  transition: all 0.3s ease;
  pointer-events: none;
}

.send-btn.can-send {
  background-color: rgb(57, 77, 209);
  pointer-events: auto;
}

.send-btn.can-send:hover {
  transform: scale(1.05);
}

.send-btn.can-send:active {
  transform: scale(0.95);
}

.send-btn .arrow {
  font-size: 28px;
  color: #ffffff;
  font-family: system-ui;
  line-height: 0;
  transform: rotate(-90deg);
  display: flex;
  align-items: center;
  justify-content: center;
  height: 28px;
}

/* 自定义滚动条样式 */
.note-content::-webkit-scrollbar {
  width: 4px;
}

.note-content::-webkit-scrollbar-thumb {
  background-color: #dcdfe6;
  border-radius: 2px;
}

.note-content::-webkit-scrollbar-track {
  background-color: transparent;
}

/* 为模式选择器添加样式 */
.mode-select :deep(.el-input__wrapper),
.mode-select :deep(.el-input__inner),
.mode-select :deep(.el-select__wrapper),
.mode-select :deep(.el-select__input),
.mode-select :deep(.el-select-dropdown__item),
.mode-select :deep(.el-tag),
.mode-select :deep(.el-tag__content) {
  background-color: rgb(237, 239, 250) !important;
}

.mode-select :deep(.el-input__inner) {
  font-size: 12px;
  height: 24px;
}

/* 为模型选择器保持原样式 */
.model-select :deep(.el-input__wrapper) {
  box-shadow: none;
  padding: 0 8px;
  border-radius: 40px;
}

/* 调整前缀图标样式 */
.mode-select :deep(.el-input__prefix-inner),
.model-select :deep(.el-input__prefix-inner) {
  margin-right: 5px;
}

.mode-select :deep(.el-input__prefix),
.model-select :deep(.el-input__prefix) {
  display: flex;
  align-items: center;
}

.mode-select :deep(.el-input__prefix .el-icon),
.model-select :deep(.el-input__prefix .el-icon) {
  font-size: 16px;
  color: #409EFF;
}
</style>

<style>
/* 调整下拉菜单的宽度与select输入框一致 */
.mode-select :deep(.el-select-dropdown),
.model-select :deep(.el-select-dropdown) {
  min-width: 100px !important;
  width: auto !important;
}

/* 直接添加到组件中的强制样式 */
.mode-select .el-input__wrapper, 
.mode-select .el-input__inner {
  background-color: rgb(237, 239, 250) !important;
}
</style> 
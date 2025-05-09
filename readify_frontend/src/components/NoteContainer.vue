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

    <!-- 思考过程抽屉 -->
    <el-drawer
      v-model="drawerVisible"
      direction="rtl"
      :size="'30%'"
      :with-header="false"
      :close-on-click-modal="false"
      :close-on-press-escape="false"
      :show-close="false"
      :modal="true"
      :append-to-body="true"
      custom-class="thinking-drawer"
      v-if="drawerVisible && !isMinimized"
      destroy-on-close
    >
      <div class="thinking-content">
        <!-- 自定义标题栏 -->
        <div class="custom-drawer-header">
          <div class="drawer-title">{{ isThinkingComplete ? '思考已完成' : '思考过程' }}</div>
          <div class="drawer-header-actions">
            <el-button
              type="text"
              class="minimize-header-btn"
              @click="handleMinimize"
              title="最小化"
            >
              <el-icon><Minus /></el-icon>
            </el-button>
            <el-button
              v-if="isThinkingComplete"
              type="text"
              class="close-header-btn"
              @click="closeThinkingDrawer"
              title="关闭"
            >
              <el-icon><Close /></el-icon>
            </el-button>
          </div>
        </div>
        
        <div class="thinking-header">
          <h3>{{ isThinkingComplete ? 'AI思考已完成' : 'AI正在思考' }}</h3>
          <div class="thinking-status" :class="{ 'complete': isThinkingComplete }">
            <el-icon v-if="!isThinkingComplete" class="is-loading"><Loading /></el-icon>
            <el-icon v-else><Check /></el-icon>
            <span>{{ isThinkingComplete ? '生成完成' : '生成中...' }}</span>
          </div>
        </div>
        <div class="thinking-body" ref="thinkingContentRef">
          <div v-html="compiledThinkingContent"></div>
        </div>
      </div>
    </el-drawer>

    <!-- 最小化状态的浮动按钮，确保在drawerVisible为true且isMinimized为true时显示 -->
    <div class="float-thinking-button" v-if="drawerVisible && isMinimized">
      <el-tooltip content="查看AI思考过程" placement="left" effect="light">
        <el-button type="primary" circle @click="handleExpand">
          <el-icon><BrainProcess /></el-icon>
        </el-button>
      </el-tooltip>
    </div>
  </div>
</template>

<script lang="ts" setup>
import { ref, computed, onMounted, onBeforeUnmount, defineProps, defineEmits, watch, nextTick } from 'vue'
import { Close, Edit, EditPen, Lightning, Connection, Loading, Check, ArrowRightBold, ArrowLeftBold, ChatDotRound, Minus } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { marked } from 'marked'
import { h } from 'vue'

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
  (e: 'refresh-mindmap'): void
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

// 思考过程抽屉相关状态
const drawerVisible = ref(false)
const thinkingContent = ref('')
const thinkingContentRef = ref<HTMLElement | null>(null)
const isThinkingComplete = ref(false)
const isMinimized = ref(false)

// 处理最小化按钮点击
const handleMinimize = () => {
  console.log('最小化按钮被点击');
  // 切换到最小化状态
  isMinimized.value = true;
}

// 处理浮动按钮点击，展开抽屉
const handleExpand = () => {
  console.log('展开按钮被点击');
  // 切换到展开状态
  isMinimized.value = false;
  
  // 确保滚动到正确位置
  nextTick(() => {
    if (thinkingContentRef.value) {
      thinkingContentRef.value.scrollTop = thinkingContentRef.value.scrollHeight;
    }
  });
}

// 处理输入框发送
const handleSendInput = () => {
  if (!inputContent.value.trim()) return
  
  // 清空之前的思考内容并打开抽屉
  thinkingContent.value = ''
  isThinkingComplete.value = false
  isMinimized.value = false
  drawerVisible.value = true
  
  // 发送输入内容给父组件，同时传递模式和模型
  emit('send-input', inputContent.value, chatMode.value, vendor.value)
  
  // 清空输入框
  inputContent.value = ''
}

// 处理收到Agent消息
const handleAgentMessage = (message: string) => {
  try {
    // 尝试解析消息为JSON
    const parsedMessage = JSON.parse(message);
    
    // 处理[DONE]类型的消息
    if (parsedMessage.type === '[DONE]') {
      // 思维导图生成完成，更改抽屉状态为已完成
      isThinkingComplete.value = true;
      
      // 延迟最小化抽屉
      setTimeout(() => {
        isMinimized.value = true;
        
        // 发送刷新思维导图的事件给父组件
        emit('refresh-mindmap');
      }, 1500);
      
      return;
    }
    
    // 检查各种可能的消息格式
    if (parsedMessage.data) {
      // 情况1: data是对象并包含content字段
      if (typeof parsedMessage.data === 'object' && parsedMessage.data.content) {
        // 如果content为空字符串，则忽略这条消息
        if (parsedMessage.data.content.trim() === '') {
          return;
        }
        
        const content = parsedMessage.data.content;
        const messageType = parsedMessage.type || parsedMessage.data.type;
        
        // 根据类型处理渲染样式
        if (messageType === 'error') {
          // 错误类型消息，添加红色样式
          thinkingContent.value += `<div class="error-message">${content}</div>`;
        } else {
          // 普通消息，直接添加内容
          thinkingContent.value += content;
        }
      } 
      // 情况2: data本身就是字符串
      else if (typeof parsedMessage.data === 'string') {
        // 如果data为空字符串，则忽略这条消息
        if (parsedMessage.data.trim() === '') {
          return;
        }
        
        const messageType = parsedMessage.type;
        
        if (messageType === 'error') {
          thinkingContent.value += `<div class="error-message">${parsedMessage.data}</div>`;
        } else {
          thinkingContent.value += parsedMessage.data;
        }
      }
      // 情况3: data是对象但没有content字段
      else {
        // 尝试将整个data对象转为字符串
        try {
          const dataStr = typeof parsedMessage.data === 'object' 
            ? JSON.stringify(parsedMessage.data, null, 2)
            : String(parsedMessage.data);
            
          // 如果转换后的字符串为空，则忽略这条消息
          if (dataStr.trim() === '') {
            return;
          }
            
          if (parsedMessage.type === 'error') {
            thinkingContent.value += `<div class="error-message">${dataStr}</div>`;
          } else {
            thinkingContent.value += dataStr;
          }
        } catch (e) {
          // 只有在转换出错时才直接输出原始消息
          thinkingContent.value += message;
        }
      }
    } 
    // 处理思考类型消息，但content为空的情况
    else if (parsedMessage.type === 'thought' && (!parsedMessage.content || parsedMessage.content.trim() === '')) {
      // 忽略空content的thought类型消息
      return;
    }
    // 情况4: 消息本身是一个对象但没有data字段
    else if (parsedMessage.content) {
      // 如果content为空字符串，则忽略这条消息
      if (parsedMessage.content.trim() === '') {
        return;
      }
      
      if (parsedMessage.type === 'error') {
        thinkingContent.value += `<div class="error-message">${parsedMessage.content}</div>`;
      } else {
        thinkingContent.value += parsedMessage.content;
      }
    }
    // 情况5: 其他格式，直接输出原始消息（除非为空）
    else if (message.trim() !== '') {
      thinkingContent.value += message;
    }
  } catch (e) {
    // 如果解析JSON失败，按原方式添加消息（除非为空）
    if (message.trim() !== '') {
      thinkingContent.value += message;
    }
  }
  
  // 自动滚动到底部
  nextTick(() => {
    if (thinkingContentRef.value) {
      thinkingContentRef.value.scrollTop = thinkingContentRef.value.scrollHeight;
    }
  });
}

// 处理关闭抽屉
const closeThinkingDrawer = () => {
  // 完全关闭抽屉
  drawerVisible.value = false;
  isMinimized.value = false;
}

// 处理重新打开抽屉
const reopenThinkingDrawer = () => {
  drawerVisible.value = true;
  isMinimized.value = false;
}

// 使用marked将思考内容转换为HTML
const compiledThinkingContent = computed(() => {
  return marked(thinkingContent.value || '正在等待AI响应...')
})

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

// 暴露方法给父组件
defineExpose({
  handleAgentMessage,
  closeThinkingDrawer,
  reopenThinkingDrawer
})

// 自定义思考图标组件
const BrainProcess = {
  name: 'BrainProcess',
  render() {
    return h('svg', {
      xmlns: 'http://www.w3.org/2000/svg',
      viewBox: '0 0 24 24',
      width: '1em',
      height: '1em',
      fill: 'currentColor'
    }, [
      h('path', {
        d: 'M12 2a8 8 0 0 0-8 8c0 2.21.9 4.21 2.36 5.65l-1.51 1.5a3 3 0 0 0 0 4.24 3 3 0 0 0 4.24 0l1.5-1.5A7.954 7.954 0 0 0 12 22c4.42 0 8-3.58 8-8 0-2.21-.9-4.21-2.36-5.65l1.51-1.5a3 3 0 0 0 0-4.24 3 3 0 0 0-4.24 0l-1.5 1.5A7.954 7.954 0 0 0 12 2zM9.17 19.17a1 1 0 0 1-1.41 0 1 1 0 0 1 0-1.42l1.24-1.24a7.984 7.984 0 0 0 1.42 1.42l-1.25 1.24zM12 20a6 6 0 0 1-4.24-1.76 5.994 5.994 0 0 1 0-8.48l1.06 1.06a4 4 0 1 0 6.36 0l1.06-1.06a5.994 5.994 0 0 1 0 8.48A6 6 0 0 1 12 20zm4.24-14.83a1 1 0 0 1 1.41 0 1 1 0 0 1 0 1.42l-1.24 1.24a7.984 7.984 0 0 0-1.42-1.42l1.25-1.24zM12 4c1.47 0 2.82.5 3.89 1.33l-1.06 1.06a4 4 0 1 0-5.66 5.66l-1.06 1.06A5.994 5.994 0 0 1 12 4zm0 5.5a1.5 1.5 0 1 1 0 3 1.5 1.5 0 0 1 0-3z'
      })
    ]);
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

/* 思考过程抽屉样式 */
.thinking-content {
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow: hidden;
}

.thinking-header {
  display: flex;
  flex-direction: column;
  padding: 16px 20px;
  border-bottom: 1px solid #f0f0f0;
}

.thinking-header h3 {
  margin: 0 0 8px 0;
  font-size: 18px;
  font-weight: 600;
  color: #303133;
}

.drawer-actions {
  display: flex;
  justify-content: flex-end;
  margin-bottom: 8px;
}

.minimize-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 5px;
  color: #606266;
}

.thinking-status {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #409EFF;
  font-size: 14px;
}

.thinking-status.complete {
  color: #67C23A;
}

.thinking-status .el-icon {
  font-size: 16px;
}

.thinking-body {
  flex: 1;
  overflow-y: auto;
  font-size: 14px;
  line-height: 1.6;
  padding: 0 20px 20px 20px;
}

.thinking-body::-webkit-scrollbar {
  width: 6px;
}

.thinking-body::-webkit-scrollbar-thumb {
  background-color: #dcdfe6;
  border-radius: 3px;
}

.thinking-body::-webkit-scrollbar-track {
  background-color: transparent;
}

/* 代码块样式 */
.thinking-body :deep(pre) {
  background-color: #f8f9fa;
  padding: 12px;
  border-radius: 4px;
  overflow-x: auto;
}

.thinking-body :deep(code) {
  font-family: monospace;
  font-size: 13px;
}

.thinking-body :deep(.error-message) {
  color: #f56c6c;
  font-weight: 500;
  padding: 8px;
  padding-left: 12px;
  background-color: rgba(245, 108, 108, 0.1);
  border-radius: 4px;
  margin: 8px 0;
  border-left: 4px solid #f56c6c;
  position: relative;
}

.thinking-body :deep(.error-message)::before {
  content: "⚠️";
  margin-right: 8px;
  font-size: 14px;
}

/* 最小化抽屉样式 */
:deep(.minimized-drawer) {
  background: transparent !important;
  box-shadow: none !important;
  border: none !important;
  width: auto !important;
  min-width: 60px !important;
}

:deep(.minimized-drawer .el-drawer__header) {
  display: none !important;
}

:deep(.minimized-drawer .el-drawer__body) {
  padding: 0 !important;
  background: transparent !important;
}

.minimized-content {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
}

.minimized-button-wrapper {
  position: fixed;
  top: 50%;
  right: 20px;
  transform: translateY(-50%);
  z-index: 2000;
}

.minimized-button-wrapper .el-button {
  width: 46px;
  height: 46px;
  font-size: 20px;
  background: linear-gradient(145deg, #4a8bff, #3169e7);
  box-shadow: 0 4px 12px rgba(62, 125, 233, 0.4);
  transition: all 0.3s;
  border: none;
  display: flex;
  align-items: center;
  justify-content: center;
}

.minimized-button-wrapper .el-button:hover {
  transform: scale(1.1);
  box-shadow: 0 6px 16px rgba(62, 125, 233, 0.5);
  background: linear-gradient(145deg, #5a97ff, #4179f7);
}

.minimized-button-wrapper .el-button:active {
  transform: scale(0.95);
  box-shadow: 0 2px 8px rgba(62, 125, 233, 0.4);
}

/* 添加脉冲动画效果 */
@keyframes pulse {
  0% {
    box-shadow: 0 0 0 0 rgba(62, 125, 233, 0.4);
  }
  70% {
    box-shadow: 0 0 0 10px rgba(62, 125, 233, 0);
  }
  100% {
    box-shadow: 0 0 0 0 rgba(62, 125, 233, 0);
  }
}

.minimized-button-wrapper .el-button {
  animation: pulse 2s infinite;
}

/* 确保激活状态下抽屉层级足够高 */
:deep(.el-drawer) {
  z-index: 2010 !important;
}

:deep(.minimized-drawer) {
  z-index: 2005 !important;
}

/* 当抽屉处于最小化状态时，禁用蒙层 */
:deep(.minimized-drawer + .v-modal) {
  background-color: transparent !important;
  opacity: 0 !important;
  pointer-events: none !important;
}

/* 添加透明模态层样式 */
:deep(.transparent-modal) {
  background-color: transparent !important;
  pointer-events: none !important;
}

/* 隐藏抽屉样式 */
:deep(.hidden-drawer) {
  opacity: 0 !important;
  pointer-events: none !important;
}

/* 浮动思考按钮样式 */
.float-thinking-button {
  position: fixed;
  top: 50%;
  right: 20px;
  transform: translateY(-50%);
  z-index: 9999;
}

.float-thinking-button .el-button {
  width: 50px;
  height: 50px;
  font-size: 24px;
  background: linear-gradient(145deg, #4f87ff, #2259d9);
  box-shadow: 0 4px 12px rgba(62, 125, 233, 0.4);
  transition: all 0.3s ease;
  border: none;
}

.float-thinking-button .el-button:hover {
  transform: scale(1.1);
  box-shadow: 0 6px 16px rgba(62, 125, 233, 0.5);
  background: linear-gradient(145deg, #5a97ff, #4179f7);
}

.float-thinking-button .el-button:active {
  transform: scale(0.95);
  box-shadow: 0 2px 8px rgba(62, 125, 233, 0.4);
}

/* 添加脉冲动画 */
@keyframes button-pulse {
  0% {
    box-shadow: 0 0 0 0 rgba(79, 135, 255, 0.6);
  }
  70% {
    box-shadow: 0 0 0 10px rgba(79, 135, 255, 0);
  }
  100% {
    box-shadow: 0 0 0 0 rgba(79, 135, 255, 0);
  }
}

.float-thinking-button .el-button {
  animation: button-pulse 2s infinite;
}

/* 自定义抽屉标题栏样式 */
.custom-drawer-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 20px;
  height: 50px;
  border-bottom: 1px solid #ebeef5;
  background: linear-gradient(135deg, #f8f9fa 0%, #ffffff 100%);
}

.drawer-title {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.drawer-header-actions {
  display: flex;
  gap: 8px;
}

.minimize-header-btn,
.close-header-btn {
  padding: 6px;
  color: #909399;
  font-size: 16px;
}

.minimize-header-btn:hover,
.close-header-btn:hover {
  color: #606266;
  background-color: #f2f6fc;
}

.minimize-header-btn .el-icon,
.close-header-btn .el-icon {
  font-size: 18px;
  display: flex;
  align-items: center;
  justify-content: center;
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
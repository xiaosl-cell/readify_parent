<template>
  <div class="home-container">
    <!-- 顶部导航栏 -->
    <Navbar :project-name="projectName" />

    <!-- 主要内容区域 -->
    <div class="main-content">
      <div class="content-layout">
        <!-- 左侧书源栏 -->
        <SourcesSidebar
          :sources="sources"
          :is-collapsed="isSourcesSidebarCollapsed"
          @toggle-collapse="isSourcesSidebarCollapsed = !isSourcesSidebarCollapsed"
          @add-source="handleAddSource"
          @update:sources="handleSourcesUpdate"
        />

        <!-- 中间聊天对话栏 -->
        <ChatContainer v-show="!isNoteVisible">
          <Chat 
            @send-message="(message, projectId) => { console.log('[事件监听调试] - send-message事件已经被直接捕获:', message, projectId); handleSendChatMessage(message, projectId); }"
            ref="chatRef"
          />
          <div v-if="!actualProjectId" class="project-loading">
            <el-alert
              title="项目正在加载中"
              type="info"
              :closable="false"
              description="请稍候，项目信息正在加载..."
              show-icon
            />
          </div>
        </ChatContainer>

        <!-- 笔记内容容器 -->
        <NoteContainer
          v-show="isNoteVisible"
          :title="currentNote.title"
          :content="currentNote.content"
          :visible="isNoteVisible"
          @close="handleNoteClose"
          @save="handleNoteSave"
          @send-input="handleNoteInput"
        />

        <!-- 右侧笔记本栏 -->
        <NotebookSidebar
          :is-collapsed="isNotebookSidebarCollapsed"
          @toggle-collapse="isNotebookSidebarCollapsed = !isNotebookSidebarCollapsed"
          @select-note="handleSelectNote"
        >
          <!-- 这里后续添加笔记本内容 -->
        </NotebookSidebar>
      </div>
    </div>

    <!-- WebSocket管理器 -->
    <WebSocketManager
      :project-id="actualProjectId"
      @message="handleWebSocketMessage"
      @error="handleWebSocketError"
      @connected="handleWebSocketConnected"
      @disconnected="handleWebSocketDisconnected"
      ref="wsManager"
    />

    <!-- 文件上传框 -->
    <UploadDialog
      v-model:visible="uploadDialogVisible"
      :project-id="actualProjectId"
      :project-name="projectName"
      :upload-headers="uploadHeaders"
      @success="handleUploadSuccess"
    />

    <!-- 思维导图查看器 -->
    <MindMapDialog 
      ref="mindMapDialogRef" 
      @open="handleMindMapOpen" 
      @close="handleMindMapClose" 
    />
  </div>
</template>

<script lang="ts" setup>
import { ref, computed, onMounted, onBeforeUnmount, watch, provide, nextTick } from 'vue'
import { useStore } from 'vuex'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage, ElLoading } from 'element-plus'
import { getAuthHeader, getToken } from '@/utils/auth'
import { getProjectById } from '@/api/project'
import { getProjectFiles } from '@/api/file'
import { sendChatMessage, getProjectConversations } from '@/api/chat'
import { getMindMapById, updateMindMap } from '@/api/mindmap'
import { getFullMindMap } from '@/api/mindmap'
import type { FileVO } from '@/types/file'
import type { MindMapVO } from '@/types/mindmap'
import type { MindMapNodeTreeVO } from '@/types/mindmap'

// 导入组件
import Navbar from '@/components/Navbar.vue'
import SourcesSidebar from '@/components/SourcesSidebar.vue'
import ChatContainer from '@/components/ChatContainer.vue'
import NotebookSidebar from '@/components/NotebookSidebar.vue'
import UploadDialog from '@/components/UploadDialog.vue'
import WebSocketManager from '@/components/WebSocketManager.vue'
import Chat from '@/components/Chat.vue'
import MindMapDialog from '@/components/MindMapDialog.vue'
import NoteContainer from '@/components/NoteContainer.vue'

const store = useStore()
const router = useRouter()
const route = useRoute()
const wsManager = ref<InstanceType<typeof WebSocketManager> | null>(null)

// 控制思维导图和聊天窗口显示状态
const isMindMapVisible = ref(false)
// 控制笔记显示状态
const isNoteVisible = ref(false)

// 当前笔记内容
const currentNote = ref({
  id: 0,
  title: '',
  content: ''
})

// WebSocket相关状态
const isWebSocketConnected = ref(false)

// 项目信息
const projectId = computed(() => {
  // 打印原始路由参数，帮助调试
  
  // 尝试从URL路径中直接提取ID，这是最可靠的方法
  const pathMatch = route.path.match(/\/project\/(\d+)/)
  if (pathMatch && pathMatch[1]) {
    const idFromPath = Number(pathMatch[1])
    return idFromPath
  }
  
  // 如果URL路径无法提取，尝试从路由参数获取
  if (route.params.id) {
    const id = Number(route.params.id)
    if (!isNaN(id) && id > 0) {
      return id
    }
  }
  
  // 如果以上都失败，使用默认值
  console.warn('无法从URL或路由参数获取有效ID，使用默认值23')
  return 23
})

// 创建一个明确的数字类型的项目ID变量
const actualProjectId = ref(23); // 默认值23

// 当计算属性projectId变化时，更新actualProjectId
watch(projectId, (newId) => {
  actualProjectId.value = Number(newId) || 23;
}, { immediate: true });

// 使用provide提供projectId给子组件
provide('projectId', actualProjectId);
// 同时提供WebSocket管理器引用给子组件
provide('wsManager', wsManager);

const projectName = ref('加载中...')

// 添加API状态相关变量
const apiLoadingFailed = ref(false);

// 加载项目信息
const loadProject = async () => {
  if (!actualProjectId.value) {
    console.error('无效的项目ID, 无法加载项目')
    return
  }
  
  try {
    // 设置超时选项
    const res = await getProjectById(actualProjectId.value)
    if (res.data) {
      projectName.value = res.data.name
      apiLoadingFailed.value = false; // 重置错误状态
    }
  } catch (error) {
    console.error('Failed to load project:', error)
    apiLoadingFailed.value = true; // 设置错误状态
    
    // 设置一个默认的项目名
    projectName.value = `项目 #${actualProjectId.value}`;
    
    // 仅在非ECONNABORTED错误时显示消息给用户
    if (error.code !== 'ECONNABORTED') {
      ElMessage.error('获取项目信息失败，使用默认值继续操作')
    }
  }
}

// 侧边栏收缩状态
const isSourcesSidebarCollapsed = ref(false)
const isNotebookSidebarCollapsed = ref(false)

// 书源相关状态
interface SourceFile extends FileVO {
  selected: boolean;
  vectorized: boolean;
  loading: boolean;
}

const sources = ref<SourceFile[]>([])

// 聊天相关引用
const chatRef = ref<InstanceType<typeof Chat> | null>(null)

// 添加本地变量存储已加载的对话历史
const loadedConversations = ref(null)

// 加载项目文件
const loadProjectFiles = async () => {
  try {
    const res = await getProjectFiles(actualProjectId.value)
    if (res.data) {
      sources.value = res.data.map(file => ({
        ...file,
        selected: file.vectorized,
        vectorized: file.vectorized,
        loading: file.vectorized ? false : true
      }))
      apiLoadingFailed.value = false; // 重置错误状态
    }
  } catch (error) {
    console.error('Failed to load project files:', error)
    apiLoadingFailed.value = true; // 设置错误状态
    
    // 仅在非ECONNABORTED错误时显示消息给用户
    if (error.code !== 'ECONNABORTED') {
      ElMessage.error('获取项目文件失败，可以继续使用聊天功能')
    }
  }
}

// 加载项目对话历史
const loadProjectConversations = async () => {
  if (!actualProjectId.value) {
    console.error('无效的项目ID, 无法加载项目对话历史')
    return
  }
  
  try {
    const res = await getProjectConversations(actualProjectId.value)
    
    // 打印完整响应，帮助调试
    
    // 预处理数据
    let conversationData = [];
    
    if (res) {
      if (typeof res.code !== 'undefined') {
        // 标准格式响应
        
        if (res.code === '200' && res.data) {
          conversationData = Array.isArray(res.data) ? res.data : 
                              (res.data && typeof res.data === 'object') ? [res.data] : [];
        }
      } else if (Array.isArray(res)) {
        // 直接返回数组的情况
        conversationData = res;
      }
    }
    
    // 存储到本地变量
    loadedConversations.value = conversationData
    
    // 尝试更新Chat组件
    if (chatRef.value && typeof chatRef.value.setConversationHistory === 'function') {
      chatRef.value.setConversationHistory(conversationData)
    } else {
    }
  } catch (error) {
  }
}

// 监听Chat组件引用，设置已加载的对话历史
watch(chatRef, (newChatRef) => {
  if (newChatRef && loadedConversations.value) {
    if (typeof newChatRef.setConversationHistory === 'function') {
      newChatRef.setConversationHistory(loadedConversations.value)
    } else {
      console.error('[chatRef监听] - setConversationHistory方法不存在')
    }
  } else if (newChatRef && actualProjectId.value) {
    loadProjectConversations()
  }
}, { immediate: true })

// 同时也监听项目ID变化，加载新项目的对话历史
watch(actualProjectId, (newId) => {
  if (newId && newId > 0) {
    loadProjectConversations()
  }
})

// 监听projectId变化
watch(actualProjectId, (newId) => {
  if (newId) {
    loadProject()
    // WebSocket已连接时，不需要HTTP请求
    if (!isWebSocketConnected.value) {
      loadProjectFiles()
    }
  }
}, { immediate: true })

// 处理书源更新
const handleSourcesUpdate = (updatedSources: SourceFile[]) => {
  sources.value = updatedSources
}

// 文件上传相关状态
const uploadDialogVisible = ref(false)
const uploadHeaders = computed(() => ({
  Authorization: getAuthHeader()
}))

// 处理添加书源按钮点击
const handleAddSource = () => {
  uploadDialogVisible.value = true
}

// 处理WebSocket事件
const handleWebSocketMessage = (message: any) => {
  // 按消息类型处理
  if (message.type === 'projectFiles') {
    sources.value = message.data.map((file: FileVO) => ({
      ...file,
      selected: file.vectorized,
      vectorized: file.vectorized,
      loading: file.vectorized ? false : true
    }))
  } else if (['agentMessage', 'agentComplete'].includes(message.type)) {
    // 转发AI代理消息到Chat组件
    chatRef.value?.handleWebSocketMessage(message)
  } else if (['messageSent', 'sendMessageResponse'].includes(message.type)) {
    // 处理发送消息的确认回执
    if (chatRef.value) {
      // 转换为一个系统消息通知Chat组件
      chatRef.value.handleWebSocketMessage({
        type: 'agentMessage',
        data: JSON.stringify({
          type: 'system',
          content: `消息已通过WebSocket发送，服务器回应: ${message.type}`
        })
      })
    }
  } else {
    // 其他未知类型消息，直接转发给Chat组件
    chatRef.value?.handleWebSocketMessage(message)
  }
}

const handleWebSocketError = (error: any) => {
  console.error('[WebSocket事件] - WebSocket错误:', error)
  isWebSocketConnected.value = false
  
  // 如果WebSocket出错，回退到HTTP请求
  loadProjectFiles()
  
  // 显示错误提示
  ElMessage.error('聊天服务连接异常，请尝试刷新页面')
}

const handleWebSocketConnected = () => {
  isWebSocketConnected.value = true
  
  // 获取WebSocket实例，并传递给Chat组件
  if (wsManager.value && wsManager.value.ws && chatRef.value) {
    // 确保Chat组件挂载完成后再设置WebSocket实例
    if (typeof chatRef.value.setWebSocketInstance === 'function') {
      chatRef.value.setWebSocketInstance(wsManager.value.ws)
    }
  }
}

const handleWebSocketDisconnected = () => {
  isWebSocketConnected.value = false
  
  // 断开连接时，尝试使用HTTP请求加载数据
  loadProjectFiles()
  
  // 通知Chat组件WebSocket已断开
  if (chatRef.value && typeof chatRef.value.setWebSocketInstance === 'function') {
    chatRef.value.setWebSocketInstance(null)
  }
}

// 上传成功的回调
const handleUploadSuccess = () => {
  wsManager.value?.queryProjectFiles()
}

// 发送聊天消息
const handleSendChatMessage = (message: string, messageProjectId: number) => {
  // 优先使用传入的项目ID（如果有效）
  if (messageProjectId && messageProjectId !== 0) {
    // 如果传入的项目ID与当前不同，更新actualProjectId
    if (messageProjectId !== actualProjectId.value) {
      actualProjectId.value = messageProjectId
    }
  }
  
  if (!message || message.trim() === '') {
    console.error('消息内容为空，不发送')
    return
  }
  
  // 检查actualProjectId是否有效
  if (!actualProjectId.value || actualProjectId.value === 0) {
    ElMessage.error('无法确定项目，请刷新页面后重试')
    chatRef.value?.handleSendFailed()
    return
  }
  
  // 尝试通过HTTP API发送消息
  sendChatMessage({
    query: message,
    projectId: actualProjectId.value
  }).then(response => {
    // 发送成功，不需要额外处理
  }).catch(error => {
    console.error('[API尝试] - 发送失败:', error)
    
    // 如果API请求失败，尝试WebSocket方式
    if (!wsManager.value) {
      ElMessage.error('聊天服务未连接，请稍后再试')
      chatRef.value?.handleSendFailed()
      return
    }
    
    // 尝试自动重连WebSocket
    if (!isWebSocketConnected.value && wsManager.value) {
      wsManager.value.initWebSocket();
      
      // 添加延迟重试发送
      setTimeout(() => {
        if (wsManager.value?.ws?.readyState === WebSocket.OPEN) {
          sendMessageToWebSocket(message);
        } else {
          ElMessage.error('聊天服务重连失败，请稍后再试')
          chatRef.value?.handleSendFailed()
        }
      }, 1000);
      return;
    }
    
    // 发送WebSocket消息
    sendMessageToWebSocket(message);
  })
}

// WebSocket消息发送逻辑
const sendMessageToWebSocket = (message: string) => {
  // 检查WebSocket状态
  if (!wsManager.value || !wsManager.value.ws || wsManager.value.ws.readyState !== WebSocket.OPEN) {
    ElMessage.error('聊天服务未连接，无法发送消息')
    chatRef.value?.handleSendFailed()
    return
  }
  
  try {
    const messageData = {
      type: 'sendMessage',
      data: {
        query: message,
        projectId: actualProjectId.value.toString()
      },
      timestamp: Date.now()
    }
    
    // 发送消息
    const result = wsManager.value.sendMessage(messageData)
    
    if (!result) {
      throw new Error('WebSocket发送消息失败')
    }
  } catch (error) {
    console.error('[WebSocket发送] - 发送失败:', error)
    ElMessage.error('发送消息失败，请稍后再试')
    chatRef.value?.handleSendFailed()
  }
}

// 获取文件扩展名
const getFileExtension = (filename: string) => {
  const ext = filename.split('.').pop()
  return ext ? ext.toUpperCase() : ''
}

// 思维导图对话框引用
const mindMapDialogRef = ref<InstanceType<typeof MindMapDialog> | null>(null)

// 处理选择笔记
const handleSelectNote = (note: MindMapVO) => {
  // 不再打开思维导图，而是显示笔记内容
  openNote(note)
}

// 打开笔记
const openNote = async (note: MindMapVO) => {
  try {
    // 显示加载状态
    const loadingInstance = ElLoading.service({
      text: '正在加载笔记内容...',
      background: 'rgba(255, 255, 255, 0.8)'
    })
    
    // 获取完整思维导图结构
    const res = await getFullMindMap(note.id)
    
    // 关闭加载提示
    loadingInstance.close()
    
    if (res.data) {
      // 将思维导图节点树转换为Markdown格式
      const markdown = convertNodeTreeToMarkdown(res.data)
      
      // 设置当前笔记内容
      currentNote.value = {
        id: note.id,
        title: note.title,
        // 使用转换后的Markdown作为笔记内容
        content: markdown
      }
      // 显示笔记容器
      isNoteVisible.value = true
    } else {
      ElMessage.error('获取笔记内容失败')
    }
  } catch (error) {
    console.error('Failed to load note content:', error)
    ElMessage.error('获取笔记内容失败，使用示例内容')
    
    // 加载失败时使用示例内容
    currentNote.value = {
      id: note.id,
      title: note.title,
      content: EXAMPLE_MARKDOWN
    }
    isNoteVisible.value = true
  }
}

// 将思维导图节点树转换为Markdown格式
const convertNodeTreeToMarkdown = (nodeTree: MindMapNodeTreeVO): string => {
  // 构建Markdown头部
  let markdown = `---
title: ${currentNote.value.title || '思维导图笔记'}
markmap:
  colorFreezeLevel: 2
---\n\n`
  
  // 如果有根节点，递归构建Markdown内容
  if (nodeTree) {
    markdown += buildMarkdownFromNode(nodeTree, 1) // 从一级标题开始
  }
  
  return markdown
}

// 递归构建Markdown内容
const buildMarkdownFromNode = (node: MindMapNodeTreeVO, level: number): string => {
  // 标题层级，最多支持6级
  const headerLevel = Math.min(level, 6)
  const prefix = '#'.repeat(headerLevel)
  
  // 当前节点的Markdown文本
  let markdown = `${prefix} ${node.content || '未命名节点'}\n\n`
  
  // 递归处理子节点
  if (node.children && node.children.length > 0) {
    for (const child of node.children) {
      markdown += buildMarkdownFromNode(child, level + 1)
    }
  }
  
  return markdown
}

// 处理笔记关闭
const handleNoteClose = () => {
  isNoteVisible.value = false
}

// 处理保存笔记
const handleNoteSave = async (content: string) => {
  if (!currentNote.value.id) return
  
  try {
    // 显示加载状态
    const loadingInstance = ElLoading.service({
      text: '正在保存笔记...',
      background: 'rgba(255, 255, 255, 0.8)'
    })
    
    // 更新笔记内容
    const res = await updateMindMap(currentNote.value.id, {
      description: content
    })
    
    // 关闭加载提示
    loadingInstance.close()
    
    if (res.data) {
      ElMessage.success('笔记保存成功')
      // 更新当前笔记内容
      currentNote.value.content = content
    } else {
      ElMessage.error('保存笔记失败: ' + (res.message || '未知错误'))
    }
  } catch (error) {
    console.error('Failed to save note:', error)
    ElMessage.error('保存笔记失败，请重试')
  }
}

// 处理思维导图打开
const handleMindMapOpen = () => {
  isMindMapVisible.value = true
}

// 处理思维导图关闭
const handleMindMapClose = () => {
  isMindMapVisible.value = false
}

// 示例Markdown数据
const EXAMPLE_MARKDOWN = `---
title: 示例笔记
---

## 笔记内容

这是一个示例笔记，展示了Markdown的基本格式。

### 列表示例

- 第一项
- 第二项
- 第三项

### 代码示例

\`\`\`javascript
console.log('Hello, World!');
\`\`\`

### 表格示例

| 项目 | 价格 |
|------|------|
| 苹果 | ¥5   |
| 香蕉 | ¥3   |

### 引用示例

![](https://markmap.js.org/favicon.png)

`

// 处理笔记输入框发送的内容
const handleNoteInput = (input: string, mode: string, vendor: string) => {
  if (!input.trim()) return
  
  // 在这里处理笔记输入
  console.log('收到笔记输入:', input, '模式:', mode, '模型:', vendor)
  
  // 可以调用WebSocket发送消息，与聊天共用逻辑
  if (actualProjectId.value) {
    // 如果需要，可以在这里传递模式和模型信息
    handleSendChatMessage(input, actualProjectId.value)
  }
}

// 组件挂载时初始化
onMounted(async () => {
  
  try {
    // 加载项目基本信息
    await loadProject()
    
    // 先加载一次数据，确保有初始数据显示
    await loadProjectFiles()
    
    
    // 如果chatRef此时已可用，尝试主动调用自加载方法
    if (chatRef.value) {
      if (typeof chatRef.value.loadConversationHistory === 'function') {
        try {
          await chatRef.value.loadConversationHistory()
          
          // 添加延迟检查，确保消息显示正常
          setTimeout(() => {
            if (chatRef.value && typeof chatRef.value.forceRefreshHistory === 'function') {
              const refreshResult = chatRef.value.forceRefreshHistory()
            }
          }, 3000)
        } catch (err) {
        }
      } else {
      }
    } else {
    }
  } catch (error) {
    ElMessage.error('加载项目数据时出错，请尝试刷新页面')
  }
})
</script>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700&family=Montserrat:wght@600&display=swap');

.home-container {
  width: 100vw;
  height: 100vh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  /* 覆盖 Element Plus 的全局主题变量 */
  --el-color-primary: #606266;
  --el-color-primary-light-3: #f5f7fa;
  --el-color-primary-light-5: #f5f7fa;
  --el-color-primary-light-7: #f5f7fa;
  --el-color-primary-light-8: #f5f7fa;
  --el-color-primary-light-9: #f5f7fa;
  --el-color-primary-dark-2: #606266;
  
  /* 自定义按钮变量 */
  --el-button-hover-link-text-color: #606266;
  --el-button-hover-border-color: #dcdfe6;
  --el-button-hover-bg-color: #ffffff;
  --el-button-active-border-color: #dcdfe6;
  --el-button-active-color: #606266;
  --el-button-hover-text-color: #606266;
}

.main-content {
  flex: 1;
  width: 100%;
  overflow: hidden;
  background-color: rgb(237, 239, 250);
  padding: 0 24px 16px 24px;
}

.content-layout {
  height: 100%;
  display: flex;
  gap: 24px;
}
</style>
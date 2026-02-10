<template>
  <div class="chat">
    <!-- 聊天历史记录区域 -->
    <div class="chat-history" ref="chatHistory">
      <div v-for="(message, index) in messages" :key="index" class="message-wrapper">
        <div class="message" :class="{ 'user-message': message.isUser }">
          <div v-if="message.thought && !message.isUser" class="thought-section">
            <div class="thought-header" @click="toggleThought(index)">
              <el-icon><ArrowDown v-if="!message.thoughtExpanded" /><ArrowUp v-else /></el-icon>
              <span>思考过程</span>
            </div>
            <div v-show="message.thoughtExpanded" class="thought-content" v-html="formatMessage(message.thought)"></div>
          </div>
          <div class="message-content" :class="{ 'error-message': message.isError }" v-html="formatMessage(message.content)">
          </div>
        </div>
      </div>
    </div>

    <!-- 消息发送栏 -->
    <div class="chat-input">
      <div class="input-wrapper">
        <el-input
          v-model="inputMessage"
          type="textarea"
          :rows="3"
          placeholder="请输入您的问题..."
          resize="none"
          @keydown.enter.prevent="handleSend"
          :disabled="isSending"
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
              <el-icon><ChatRound /></el-icon>
            </template>
            <el-option label="问答模式" value="ask">
              <template #default>
                <div style="display: flex; align-items: center;">
                  <el-icon><ChatRound /></el-icon>
                  <span style="margin-left: 5px; font-size: 12px;">问答模式</span>
                </div>
              </template>
            </el-option>
          </el-select>
        </div>
        <el-button 
          class="send-btn"
          :class="{ 'can-send': inputMessage.trim() && !isSending }"
          :disabled="!inputMessage.trim() || isSending"
          @click="handleSend"
        >
          <span v-if="!isSending" class="arrow">➜</span>
          <el-icon v-else class="is-loading"><Loading /></el-icon>
        </el-button>
      </div>
    </div>
  </div>
</template>

<script lang="ts" setup>
import { ref, nextTick, defineProps, defineEmits, computed, watch, onMounted, inject, onBeforeUnmount } from 'vue'
import { ArrowDown, ArrowUp, Loading, ChatRound } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { getToken } from '@/utils/auth'  // 导入getToken函数
import { getProjectConversations } from '@/api/chat'
import { marked } from 'marked' // 导入marked库

// 配置marked选项
marked.setOptions({
  breaks: true, // 支持GitHub风格的换行
  gfm: true,    // 启用GitHub风格的markdown
  sanitize: false, // 允许HTML标签
  highlight: function(code, lang) {
    return code; // 这里可以添加代码高亮的逻辑
  }
});

interface ChatMessage {
  content: string
  isUser: boolean
  timestamp: number
  thought?: string
  thoughtExpanded?: boolean
  finalAnswer?: string
  isError?: boolean
}

interface AgentMessage {
  type: string
  content: string
}

interface ChatProps {
  // 不再需要通过props接收projectId
}

// 已经不需要这个props定义，但为了与模板兼容，仍保留
const props = defineProps<ChatProps>()

const emit = defineEmits<{
  (e: 'send-message', message: string, projectId: number): void
}>()

// 从父组件注入projectId
const injectedProjectId = inject<Ref<number>>('projectId', ref(23))

// 添加从父组件注入WebSocket管理器
const injectedWsManager = inject('wsManager', null)
// 添加wsManager变量到全局变量方便函数访问
window['__chat_injectedWsManager'] = injectedWsManager

// 添加本地ref变量，用于跟踪实际使用的projectId
const localProjectId = computed(() => {
  const id = injectedProjectId.value || 23;
  console.log('计算本地projectId:', id);
  return id;
})

// 监听注入的projectId变化
watch(injectedProjectId, (newProjectId) => {
  console.log('Chat组件检测到注入的projectId变化:', newProjectId)
}, { immediate: true })

const messages = ref<ChatMessage[]>([
  
])
const inputMessage = ref('')
const chatHistory = ref<HTMLElement | null>(null)
const isSending = ref(false)
const currentResponseIndex = ref(-1)
const currentThought = ref('')
const currentAnswer = ref('')
// 添加变量存储加载的对话历史
const loadedConversations = ref<any[]>([])

// 添加选择框的响应式变量
const chatMode = ref('ask') // 默认问答模式

// 存储WebSocket实例
const wsInstance = ref<WebSocket | null>(null)

// 设置WebSocket实例的方法
const setWebSocketInstance = (ws: WebSocket) => {
  // 检查参数是否有效
  if (!ws) {
    console.error('[WebSocket] - 接收到无效的WebSocket实例')
    return
  }
  
  // 检查WebSocket实例的readyState
  const readyStates = ['CONNECTING', 'OPEN', 'CLOSING', 'CLOSED']
  console.log('[WebSocket] - 接收到WebSocket实例，状态:', ws.readyState, 
    '状态说明:', readyStates[ws.readyState])
  
  // 只接受未关闭的WebSocket实例
  if (ws.readyState === WebSocket.CLOSING || ws.readyState === WebSocket.CLOSED) {
    console.warn('[WebSocket] - 接收到已关闭或正在关闭的WebSocket实例，拒绝存储')
    return
  }
  
  // 设置实例并记录详细日志
  wsInstance.value = ws
  console.log('[WebSocket] - WebSocket实例已成功存储')
  
  // 监听WebSocket的状态变化
  const originalOnclose = ws.onclose
  ws.onclose = (event) => {
    console.log('[WebSocket] - 存储的WebSocket连接已关闭, 状态码:', event.code)
    wsInstance.value = null
    
    // 调用原始的onclose处理程序
    if (typeof originalOnclose === 'function') {
      originalOnclose.call(ws, event)
    }
  }
  
  // 确认可用性，可能的话发送测试ping
  if (ws.readyState === WebSocket.OPEN) {
    try {
      // 可以考虑发送一个测试消息来验证连接
      console.log('[WebSocket] - 连接处于OPEN状态，可以使用')
    } catch (error) {
      console.error('[WebSocket] - 测试连接时出错:', error)
    }
  }
}

// 获取已存在的WebSocket连接
const getExistingWebSocket = () => {
  console.log('[WebSocket] - 开始查找可用的WebSocket连接')
  
  // 定义一个函数来验证WebSocket实例是否可用
  const validateWs = (ws, source) => {
    if (!ws) return null
    
    if (ws.readyState === WebSocket.OPEN) {
      console.log(`[WebSocket] - 使用${source}的WebSocket实例`)
      return ws
    } else {
      const states = ['CONNECTING', 'OPEN', 'CLOSING', 'CLOSED']
      console.log(`[WebSocket] - ${source}的WebSocket实例状态不是OPEN (${states[ws.readyState]})，无法使用`)
      return null
    }
  }
  
  // 1. 首先尝试使用组件内部存储的实例
  const localWs = validateWs(wsInstance.value, '本地组件')
  if (localWs) return localWs
  
  // 2. 尝试从全局变量获取
  try {
    const globalWs = validateWs(window['__readifyWebSocket'], '全局变量')
    if (globalWs) return globalWs
  } catch (e) {
    console.error('[WebSocket] - 尝试获取全局WebSocket实例时出错:', e)
  }
  
  // 3. 尝试从WebSocket管理器获取
  try {
    if (window['readifyWebSocketManager'] && window['readifyWebSocketManager'].ws) {
      const managerWs = validateWs(window['readifyWebSocketManager'].ws, 'WebSocket管理器')
      if (managerWs) return managerWs
    }
  } catch (e) {
    console.error('[WebSocket] - 尝试从WebSocket管理器获取实例时出错:', e)
  }
  
  // 4. 尝试从父组件注入的引用获取 - 使用全局变量
  const globalInjectedWsManager = window['__chat_injectedWsManager']
  if (globalInjectedWsManager && globalInjectedWsManager.value && globalInjectedWsManager.value.ws) {
    const injectedWs = validateWs(globalInjectedWsManager.value.ws, '注入的WebSocket管理器')
    if (injectedWs) return injectedWs
  }
  
  console.warn('[WebSocket] - 无法找到可用的WebSocket连接')
  return null
}

// 折叠/展开思考过程
const toggleThought = (index: number) => {
  if (messages.value[index] && messages.value[index].thought) {
    messages.value[index].thoughtExpanded = !messages.value[index].thoughtExpanded
  }
}

// 格式化消息内容，处理换行和特殊格式
const formatMessage = (content: string) => {
  if (!content) return ''
  
  try {
    // 预处理内容，解决重复渲染问题
    // 去除重复的"Thought:"模式
    content = content.replace(/(Thought:+\s*)+/g, 'Thought: ');
    // 去除连续重复的相同字符
    content = content.replace(/([一-龥])(\1{3,})/g, '$1');
    // 去除连续重复的单词
    content = content.replace(/\b(\w+)(\s+\1){2,}\b/g, '$1');
    
    // 首先使用marked渲染markdown
    let formatted = marked(content)
    
    // 处理错误信息的特殊格式
    formatted = formatted.replace(
      /(步骤 \d+:[\s\S]*?结果:.*?)(?=步骤 \d+:|$)/g, 
      '<div class="error-block">$1</div>'
    )
    
    return formatted
  } catch (error) {
    console.error('Markdown渲染错误:', error)
    return content
  }
}

// 添加消息显示轮询检查变量
let messageRenderingCheckInterval: number | null = null;
let renderingChecksCount = 0;
const MAX_RENDERING_CHECKS = 5;

// 添加消息解析函数，尝试从各种可能的格式中提取有用内容
const extractMessageContent = (data: any): { type?: string, content?: string } => {
  console.log('[消息提取] - 尝试从数据中提取有用内容, 数据类型:', typeof data);
  
  // 结果对象
  const result = { type: undefined, content: undefined };
  
  // 如果是字符串，尝试解析JSON，如果失败则直接作为内容
  if (typeof data === 'string') {
    try {
      const parsed = JSON.parse(data);
      // 递归处理解析后的对象
      const extracted = extractMessageContent(parsed);
      if (extracted.type) result.type = extracted.type;
      if (extracted.content) result.content = extracted.content;
    } catch (e) {
      // 如果不是有效的JSON，直接使用字符串作为内容
      result.content = data;
      
      // 尝试从字符串中推断类型
      if (data.includes('[DONE]')) {
        result.type = '[DONE]';
      } else if (data.includes('error') || data.includes('错误')) {
        result.type = 'error';
      }
    }
    return result;
  }
  
  // 如果是对象，尝试从各种可能的字段中提取信息
  if (data && typeof data === 'object') {
    // 尝试获取类型信息
    if (data.type) {
      result.type = data.type;
    } else if (data.message_type) {
      result.type = data.message_type;
    } else if (data.messageType) {
      result.type = data.messageType;
    }
    
    // 尝试获取内容
    if (data.content) {
      result.content = data.content;
    } else if (data.message) {
      result.content = data.message;
    } else if (data.text) {
      result.content = data.text;
    } else if (data.answer) {
      result.content = data.answer;
    } else if (data.data) {
      // 如果有data字段，递归处理
      const extracted = extractMessageContent(data.data);
      if (extracted.type) result.type = extracted.type;
      if (extracted.content) result.content = extracted.content;
    }
    
    // 如果对象本身有多个键，且没有找到有用内容，尝试将整个对象转为字符串
    if (!result.content && Object.keys(data).length > 0) {
      try {
        result.content = JSON.stringify(data);
      } catch (e) {
        console.warn('[消息提取] - 无法将对象转为字符串');
      }
    }
  }
  
  console.log('[消息提取] - 提取结果:', result);
  return result;
}

// 添加辅助函数检查WebSocket消息
const inspectWebSocketMessage = (data: any): string => {
  try {
    console.log('[消息检查] - 开始检查WebSocket消息');
    
    // 记录原始消息类型
    const originalType = typeof data;
    const result = {
      messageType: 'unknown',
      dataType: originalType,
      hasValidContent: false,
      contentPreview: '',
      nestedTypes: []
    };
    
    // 检查对象类型消息
    if (originalType === 'object' && data !== null) {
      // 检查是否有type字段
      if (data.type) {
        result.messageType = data.type;
      }
      
      // 检查data字段
      if (data.data) {
        const dataType = typeof data.data;
        result.nestedTypes.push(`data:${dataType}`);
        
        // 检查嵌套的字符串JSON
        if (dataType === 'string') {
          try {
            const parsedData = JSON.parse(data.data);
            const parsedType = typeof parsedData;
            result.nestedTypes.push(`parsed:${parsedType}`);
            
            // 检查嵌套对象的类型字段
            if (parsedType === 'object' && parsedData.type) {
              result.nestedTypes.push(`nestedType:${parsedData.type}`);
              
              // 特别检查final_answer类型
              if (parsedData.type === 'final_answer' && parsedData.content) {
                result.hasValidContent = true;
                result.contentPreview = parsedData.content.substring(0, 50) + 
                                       (parsedData.content.length > 50 ? '...' : '');
              }
            }
          } catch (e) {
            result.nestedTypes.push('parseFailed');
          }
        } else if (dataType === 'object' && data.data !== null) {
          // 直接检查嵌套对象
          if (data.data.type) {
            result.nestedTypes.push(`nestedType:${data.data.type}`);
          }
          
          if (data.data.content) {
            result.hasValidContent = true;
            const contentType = typeof data.data.content;
            result.nestedTypes.push(`content:${contentType}`);
            
            if (contentType === 'string') {
              result.contentPreview = data.data.content.substring(0, 50) + 
                                     (data.data.content.length > 50 ? '...' : '');
            }
          }
        }
      }
      
      // 检查直接的content字段
      if (data.content && typeof data.content === 'string') {
        result.hasValidContent = true;
        result.contentPreview = data.content.substring(0, 50) + 
                               (data.content.length > 50 ? '...' : '');
      }
    } else if (originalType === 'string') {
      // 检查字符串是否是JSON
      try {
        const parsed = JSON.parse(data);
        result.nestedTypes.push(`parsed:${typeof parsed}`);
        
        if (typeof parsed === 'object' && parsed !== null) {
          if (parsed.type) {
            result.messageType = parsed.type;
          }
          
          if (parsed.content) {
            result.hasValidContent = true;
            result.contentPreview = parsed.content.substring(0, 50) + 
                                   (parsed.content.length > 50 ? '...' : '');
          }
        }
      } catch (e) {
        // 不是有效的JSON
        result.nestedTypes.push('notJSON');
      }
    }
    
    // 记录结果
    const summary = `消息类型: ${result.messageType}, 数据类型: ${result.dataType}, ` +
      `嵌套类型: [${result.nestedTypes.join(', ')}], ` +
      `有效内容: ${result.hasValidContent}, ` +
      `内容预览: ${result.contentPreview}`;
    
    console.log('[消息检查] - 检查结果:', summary);
    return summary;
  } catch (error) {
    console.error('[消息检查] - 检查过程出错:', error);
    return `检查出错: ${error.message}`;
  }
};

// 处理WebSocket消息
const handleWebSocketMessage = (wsMessage: any) => {
  console.log('[消息处理] - Chat组件收到WebSocket消息:', 
    typeof wsMessage === 'object' && wsMessage.type ? wsMessage.type : typeof wsMessage);
  
  // 添加更详细的日志，显示确切的消息内容
  console.log('[消息处理] - Chat组件收到的原始消息数据:', 
    typeof wsMessage === 'string' ? wsMessage.substring(0, 150) : 
    JSON.stringify(wsMessage).substring(0, 150));
  
  // 添加消息检查工具
  inspectWebSocketMessage(wsMessage);
  
  // 添加调试日志，显示完整消息内容
  console.log('[消息处理] - 原始消息数据:', JSON.stringify(wsMessage).substring(0, 300));
  
  // 预处理输入的消息对象，确保它有一个标准的结构
  let processedMessage = wsMessage;
  
  // 如果收到的是字符串，尝试解析为JSON
  if (typeof wsMessage === 'string') {
    try {
      processedMessage = JSON.parse(wsMessage);
    } catch (e) {
      // 不是有效的JSON，创建标准结构
      processedMessage = {
        type: 'raw',
        data: wsMessage
      };
    }
  }
  
  // 检查状态并重置如果需要
  const stateFixed = checkAndFixSendingState()
  if (stateFixed) {
    // 状态已重置
  }
  
  // 增加标记变量，用于跟踪是否有消息处理成功
  let messageProcessed = false;
  
  try {
    // 主要处理agentMessage类型的消息
    if (processedMessage.type === 'agentMessage') {
      // 尝试解析data字段，如果已经是对象就直接使用
      let dataContent = processedMessage.data;
      let agentMessage: AgentMessage;
      
      // 如果data是字符串，尝试解析为JSON对象
      if (typeof dataContent === 'string') {
        try {
          // 尝试解析为JSON对象
          agentMessage = JSON.parse(dataContent) as AgentMessage;
          console.log('[消息处理] - 成功解析JSON消息:', agentMessage.type);
          
          // 处理[DONE]类型的消息 - 表示对话结束
          if (agentMessage.type === '[DONE]') {
            console.log('[消息处理] - 检测到[DONE]消息，标记对话完成');
            isSending.value = false;
            
            // 最终检查确保内容正确显示
            if (currentResponseIndex.value !== -1 && currentResponseIndex.value < messages.value.length) {
              console.log('[消息处理] - 完成对话，当前索引:', currentResponseIndex.value);
              
              // 如果没有最终答案但有思考过程，确保有内容显示
              if (!messages.value[currentResponseIndex.value].content || 
                  messages.value[currentResponseIndex.value].content === '思考中...' || 
                  messages.value[currentResponseIndex.value].content === '正在处理...') {
                if (currentThought.value) {
                  messages.value[currentResponseIndex.value].content = '处理完成，但没有返回最终答案。';
                  // 强制更新时间戳触发视图刷新
                  messages.value[currentResponseIndex.value].timestamp = Date.now();
                }
              }
              
              // 收起思考过程
              if (messages.value[currentResponseIndex.value].thought) {
                messages.value[currentResponseIndex.value].thoughtExpanded = false;
              }
            }
            
            // 重置状态
            currentResponseIndex.value = -1;
            currentThought.value = '';
            currentAnswer.value = '';

            messageProcessed = true;

            // [DONE]消息强制检查消息渲染状态 
            setTimeout(checkMessageRendering, 300);
            
            return; // 提前返回，避免进一步处理
          }
          
          // 处理thought类型消息 - 思考过程
          if (agentMessage.type === 'thought') {
            console.log('[消息处理] - 收到思考过程，内容:', agentMessage.content?.substring(0, 50));

            // 累加思考内容
            if (agentMessage.content) {
              currentThought.value += agentMessage.content;
            }
            
            // 如果尚未创建AI回复，则创建一个
            if (currentResponseIndex.value === -1) {
              console.log('[消息处理] - 创建新的AI响应消息');
              messages.value.push({
                content: '思考中...',
                isUser: false,
                timestamp: Date.now(),
                thought: currentThought.value,
                thoughtExpanded: true // 默认展开思考过程
              });
              currentResponseIndex.value = messages.value.length - 1;
            } else if (currentResponseIndex.value < messages.value.length) {
              // 更新已有消息的思考过程
              console.log('[消息处理] - 更新已有消息的思考过程');
              // 保存当前的展开状态
              const currentExpanded = messages.value[currentResponseIndex.value].thoughtExpanded !== false;
              messages.value[currentResponseIndex.value].thought = currentThought.value;
              // 保留之前的展开状态，如果未设置则默认为展开
              messages.value[currentResponseIndex.value].thoughtExpanded = currentExpanded;
              // 强制更新时间戳
              messages.value[currentResponseIndex.value].timestamp = Date.now();
            }
            
            messageProcessed = true;
          }
          
          // 处理final_answer类型消息 - 最终答案
          else if (agentMessage.type === 'final_answer') {
            console.log('[消息处理] - 收到最终答案，内容:', agentMessage.content?.substring(0, 50));
            currentAnswer.value = agentMessage.content || '';
            
            // 更新消息的内容为最终答案
            if (currentResponseIndex.value !== -1 && currentResponseIndex.value < messages.value.length) {
              console.log('[消息处理] - 更新已有消息为最终答案, index:', currentResponseIndex.value);
              messages.value[currentResponseIndex.value].content = currentAnswer.value;
              // 强制更新时间戳
              messages.value[currentResponseIndex.value].timestamp = Date.now();
              
              // 最终答案到达后，折叠思考过程
              if (messages.value[currentResponseIndex.value].thought) {
                messages.value[currentResponseIndex.value].thoughtExpanded = false;
              }
            } else {
              console.log('[消息处理] - 没有找到之前的AI消息，创建新的最终答案消息');
              // 如果没有找到之前的消息，创建一个新的
              messages.value.push({
                content: currentAnswer.value,
                isUser: false,
                timestamp: Date.now()
              });
              currentResponseIndex.value = messages.value.length - 1;
            }
            
            messageProcessed = true;
          }
          // 处理tool_error类型消息 - 工具执行错误，红色显示
          else if (agentMessage.type === 'tool_error') {
            console.log('[消息处理] - 收到工具错误消息(对象)，内容:', agentMessage.content?.substring(0, 50));
            const errorContent = agentMessage.content || '工具执行出错';
            
            // 更新或创建一条包含错误信息的消息
            if (currentResponseIndex.value !== -1 && currentResponseIndex.value < messages.value.length) {
              console.log('[消息处理] - 更新已有消息为工具错误, index:', currentResponseIndex.value);
              messages.value[currentResponseIndex.value].content = errorContent;
              messages.value[currentResponseIndex.value].isError = true; // 添加错误标记
              // 强制更新时间戳
              messages.value[currentResponseIndex.value].timestamp = Date.now();
            } else {
              console.log('[消息处理] - 创建新的工具错误消息');
              // 创建一条新的错误消息
              messages.value.push({
                content: errorContent,
                isUser: false,
                isError: true, // 添加错误标记
                timestamp: Date.now()
              });
              currentResponseIndex.value = messages.value.length - 1;
            }
            
            messageProcessed = true;
          }
          // 忽略system类型的消息
          else if (agentMessage.type === 'system') {
            console.log('[消息处理] - 收到system消息，忽略渲染:', agentMessage.content?.substring(0, 50));
            // 不渲染系统消息，但标记为已处理
            messageProcessed = true;
          }
        } catch (parseError) {
          console.error('[消息处理] - JSON解析失败:', parseError, '原始消息:', dataContent);
          // 如果解析失败但字符串包含[DONE]，仍然当作完成消息处理
          if (typeof dataContent === 'string' && dataContent.includes('[DONE]')) {
            console.log('[消息处理] - 字符串包含[DONE]，以完成消息处理');
            isSending.value = false;
            currentResponseIndex.value = -1;
            currentThought.value = '';
            currentAnswer.value = '';
            messageProcessed = true;
            setTimeout(checkMessageRendering, 300);
            return;
          }

          // 其他情况尝试作为普通消息处理
          agentMessage = {
            type: 'final_answer',
            content: dataContent
          };
          
          // 处理普通文本消息
          if (currentResponseIndex.value === -1) {
            messages.value.push({
              content: dataContent,
              isUser: false,
              timestamp: Date.now()
            });
            currentResponseIndex.value = messages.value.length - 1;
          } else {
            messages.value[currentResponseIndex.value].content = dataContent;
            messages.value[currentResponseIndex.value].timestamp = Date.now();
          }
          
          messageProcessed = true;
        }
      } else if (typeof dataContent === 'object' && dataContent !== null) {
        // 如果data已经是对象，直接处理
        agentMessage = dataContent as AgentMessage;
        console.log('[消息处理] - 接收到对象类型data:', agentMessage.type);
        
        // 处理不同类型的消息
        if (agentMessage.type === 'thought') {
          // 思考过程消息
            if (agentMessage.content) {
              currentThought.value += agentMessage.content;
            }

            // 更新或创建消息
            if (currentResponseIndex.value === -1) {
              messages.value.push({
                content: '思考中...',
                isUser: false,
                timestamp: Date.now(),
                thought: currentThought.value,
                thoughtExpanded: true
              });
              currentResponseIndex.value = messages.value.length - 1;
            } else {
              const currentExpanded = messages.value[currentResponseIndex.value].thoughtExpanded !== false;
              messages.value[currentResponseIndex.value].thought = currentThought.value;
              messages.value[currentResponseIndex.value].thoughtExpanded = currentExpanded;
              messages.value[currentResponseIndex.value].timestamp = Date.now();
            }

            messageProcessed = true;
        } else if (agentMessage.type === 'final_answer') {
          // 最终答案
          currentAnswer.value = agentMessage.content || '';
          
          if (currentResponseIndex.value !== -1) {
            messages.value[currentResponseIndex.value].content = currentAnswer.value;
            messages.value[currentResponseIndex.value].timestamp = Date.now();
            
            if (messages.value[currentResponseIndex.value].thought) {
              messages.value[currentResponseIndex.value].thoughtExpanded = false;
            }
          } else {
            messages.value.push({
              content: currentAnswer.value,
              isUser: false,
              timestamp: Date.now()
            });
            currentResponseIndex.value = messages.value.length - 1;
          }
          
          messageProcessed = true;
        } else if (agentMessage.type === '[DONE]') {
          // 完成消息
          isSending.value = false;
          currentResponseIndex.value = -1;
          currentThought.value = '';
          currentAnswer.value = '';
          messageProcessed = true;
          setTimeout(checkMessageRendering, 300);
        }
        // 忽略system类型的消息
        else if (agentMessage.type === 'system') {
          console.log('[消息处理] - 收到system消息，忽略渲染:', agentMessage.content?.substring(0, 50));
          // 不渲染系统消息，但标记为已处理
          messageProcessed = true;
        }
      } else {
        console.warn('[消息处理] - 无效的消息数据格式:', typeof dataContent);
      }
    } else if (processedMessage.type === 'agentComplete') {
      console.log('[消息处理] - 代理消息流完成, 当前消息数:', messages.value.length);
      // 调用专门的处理函数
      handleAgentComplete();
      messageProcessed = true;
    }
  } catch (error) {
    console.error('[消息处理] - 消息处理过程中发生错误:', error);
    // 添加错误处理逻辑
    messages.value.push({
      content: `消息处理错误: ${error.message}`,
      isUser: false,
      timestamp: Date.now()
    });
    messageProcessed = true;
    isSending.value = false;
  }
  
  // 强制进行视图更新并滚动到底部
  nextTick(() => {
    console.log('[消息处理] - 视图更新后的消息数量:', messages.value.length);
    // 确保消息容器存在
    if (chatHistory.value) {
      chatHistory.value.scrollTop = chatHistory.value.scrollHeight;
      console.log('[消息处理] - 已滚动到底部');
    } else {
      console.warn('[消息处理] - 无法找到聊天历史容器, chatHistory ref为空');
    }
    
    // 增加一个小延迟，确保DOM已更新
    setTimeout(() => {
      // 检查消息是否成功渲染
      checkMessageRendering();
      
      // 启动轮询检查机制，确保消息被渲染
      startRenderingPolling();
      
      // 额外检查
      if (messageProcessed && messages.value.length > 0) {
        const lastMessage = messages.value[messages.value.length - 1];
        // 再次强制更新时间戳，触发额外的渲染
        lastMessage.timestamp = Date.now();
        console.log('[消息处理] - 执行额外的渲染检查');
      }
    }, 100);
  });
}

// 添加检查消息渲染状态的函数
const checkMessageRendering = () => {
  console.log('[渲染检查] - 检查消息是否成功渲染, 当前消息数:', messages.value.length);
  if (messages.value.length > 0) {
    // 获取最后一条消息
    const lastMessage = messages.value[messages.value.length - 1];
    
    // 更新时间戳以触发视图更新
    lastMessage.timestamp = Date.now();
    console.log('[渲染检查] - 已更新最后一条消息时间戳');
    
    // 延迟检查消息是否正确渲染
    setTimeout(() => {
      console.log('[渲染检查] - 进行延迟渲染检查');
      
      // 检查DOM中是否有这条消息
      const messageElements = document.querySelectorAll('.message-content');
      console.log('[渲染检查] - 当前DOM中的消息元素数:', messageElements.length);
      
      // 如果DOM中的消息数量少于messages数组中的数量，尝试强制刷新
      if (messageElements.length < messages.value.length) {
        console.warn('[渲染检查] - 检测到DOM中的消息数量少于预期，尝试强制刷新');
        forceRenderMessages();
      } else {
        console.log('[渲染检查] - 消息渲染正常');
        
        // 确保再次滚动到底部
        if (chatHistory.value) {
          chatHistory.value.scrollTop = chatHistory.value.scrollHeight;
        }
      }
    }, 500);
  }
}

// 添加滚动到底部的函数
const scrollToBottom = () => {
  if (chatHistory.value) {
    chatHistory.value.scrollTop = chatHistory.value.scrollHeight;
    console.log('[滚动] - 已滚动到聊天底部');
  }
}

// 修改forceRenderMessages函数，增加更多逻辑
const forceRenderMessages = () => {
  console.log('[强制刷新] - 开始强制刷新消息渲染, 当前消息数:', messages.value.length);
  
  // 检查是否有需要渲染的消息
  if (messages.value.length === 0) {
    console.log('[强制刷新] - 没有消息需要渲染');
    return;
  }
  
  // 使用一个临时变量存储当前消息
  const tempMessages = JSON.parse(JSON.stringify(messages.value));
  
  // 清空消息数组后再恢复，强制触发视图更新
  messages.value = [];
  
  // 使用nextTick确保DOM已更新
  nextTick(() => {
    console.log('[强制刷新] - 消息清空后开始恢复');
    
    // 在恢复消息前添加一个小延迟
    setTimeout(() => {
      // 恢复消息，并确保每条消息都有最新的时间戳
      messages.value = tempMessages.map(msg => ({
        ...msg,
        timestamp: Date.now() + Math.random() // 添加随机数确保每条消息时间戳不同
      }));
      
      console.log('[强制刷新] - 消息恢复完成, 当前消息数:', messages.value.length);
      
      // 使用Vue的nextTick确保视图已更新
      nextTick(() => {
        // 滚动到底部
        if (chatHistory.value) {
          chatHistory.value.scrollTop = chatHistory.value.scrollHeight;
          console.log('[强制刷新] - 已滚动到底部');
        }
        
        // 添加CSS动画以触发浏览器重绘
        const chatHistoryElement = chatHistory.value;
        if (chatHistoryElement) {
          chatHistoryElement.style.opacity = '0.99';
          setTimeout(() => {
            chatHistoryElement.style.opacity = '1';
            chatHistoryElement.scrollTop = chatHistoryElement.scrollHeight;
          }, 50);
        }
        
        // 检查消息是否真正渲染在DOM中
        setTimeout(() => {
          const messageElements = document.querySelectorAll('.message-content');
          console.log('[强制刷新] - DOM中消息元素数:', messageElements.length, 'messages数组长度:', messages.value.length);
          
          if (messageElements.length < messages.value.length) {
            console.warn('[强制刷新] - DOM中消息数量仍少于预期，尝试最终修复方案');
            
            // 使用更激进的处理方式
            try {
              // 遍历所有消息，强制更新每条消息的内容
              for (let i = 0; i < messages.value.length; i++) {
                const originalContent = messages.value[i].content;
                // 临时修改内容，触发Vue的更新机制
                messages.value[i].content = originalContent + ' ';
                // 立即改回原内容
                setTimeout(() => {
                  messages.value[i].content = originalContent;
                }, 10);
              }
              
              // 最终再次滚动到底部
              setTimeout(() => {
                if (chatHistory.value) {
                  chatHistory.value.scrollTop = chatHistory.value.scrollHeight;
                }
                console.log('[强制刷新] - 完成最终修复尝试');
              }, 100);
            } catch (e) {
              console.error('[强制刷新] - 最终修复尝试失败:', e);
            }
          }
        }, 300);
      });
    }, 100);
  });
}

// 发送消息
const handleSend = async () => {
  try {
    // 记录更详细的projectId信息
    console.log('[Chat.handleSend] - 被调用', {
      inputMessage: inputMessage.value,
      isSending: isSending.value,
      hasContent: !!inputMessage.value.trim(),
      injectedProjectId: injectedProjectId.value,
      localProjectId: localProjectId.value,
      chatMode: chatMode.value
    })
    
    if (!inputMessage.value.trim()) {
      console.log('[Chat.handleSend] - 输入消息为空，不发送')
      return
    }
    
    if (isSending.value) {
      console.log('[Chat.handleSend] - 正在发送中，不重复发送')
      return
    }

    // 重置之前的响应状态，确保新一轮对话正确开始
    currentResponseIndex.value = -1
    currentThought.value = ''
    currentAnswer.value = ''
    console.log('[Chat.handleSend] - 已重置响应状态')

    // 使用计算的localProjectId，确保类型正确
    console.log('[Chat.handleSend] - 开始发送消息:', inputMessage.value, '项目ID:', localProjectId.value)
    
    // 设置发送状态
    isSending.value = true
    
    // 添加用户消息
    messages.value.push({
      content: inputMessage.value,
      isUser: true,
      timestamp: Date.now()
    })

    // 保存问题并清空输入框
    const question = inputMessage.value
    inputMessage.value = ''

    // 滚动到底部
    await nextTick()
    if (chatHistory.value) {
      chatHistory.value.scrollTop = chatHistory.value.scrollHeight
    }

    // 优先使用已建立的WebSocket连接
    const existingWs = getExistingWebSocket()
    if (existingWs) {
      console.log('[Chat.handleSend] - 找到可用WebSocket，准备发送消息')
      
      const messageData = {
        type: 'sendMessage',
        data: {
          query: question,
          projectId: localProjectId.value.toString(),
          taskType: chatMode.value
        },
        timestamp: Date.now()
      }
      
      console.log('[Chat.handleSend] - 即将发送的消息数据:', JSON.stringify(messageData))
      
      try {
        existingWs.send(JSON.stringify(messageData))
        console.log('[Chat.handleSend] - WebSocket消息发送成功!')
        // 消息响应统一由 handleWebSocketMessage (Path A) 处理，
        // 不再注册额外的 responseHandler，避免 thought 内容重复累加。

        return // 发送成功后直接返回
      } catch (wsError) {
        console.error('[Chat.handleSend] - 使用WebSocket发送失败:', wsError)
        // 发送失败后继续尝试其他方式
      }
    } else {
      console.warn('[Chat.handleSend] - 未找到可用的WebSocket连接')
    }
    
    // 如果没有可用的WebSocket连接，使用emit触发父组件方法
    console.log('[Chat.handleSend] - 尝试通过emit发送消息事件, 注入的projectId:', injectedProjectId.value)
    
    // 在此处添加调试点，查看调用堆栈
    console.log('[Chat.handleSend] - 发送前状态检查:',{
      hasEmitFunction: typeof emit === 'function',
      question,
      localProjectId: localProjectId.value,
      injectedProjectId: injectedProjectId.value
    });
    
    // 如果没有定义emit函数，添加警告
    if (typeof emit !== 'function') {
      console.error('[Chat.handleSend] - 严重错误: emit不是一个函数!');
      throw new Error('emit is not a function');
    }
    
    // 通过emit通知父组件发送消息（父组件会通过HTTP API或WebSocket发送）
    emit('send-message', question, localProjectId.value)
    
  } catch (error) {
    console.error('[Chat.handleSend] - 发送消息过程中出错:', error)
    handleSendFailed()
  }
}

// 直接发送WebSocket消息的备用方法
const directSendWebSocketMessage = (message: string) => {
  try {
    
    // 获取token (仍然保留，可能在其他地方需要)
    const token = getToken()
    if (!token) {
      return false
    }
    
    // 查找已存在的WebSocket连接，进行详细检查
    let websocketInstance = null
    
    // 记录具体的尝试顺序，便于调试
    
    // 1. 首先尝试通过标准方法获取
    websocketInstance = getExistingWebSocket()
    
    // 2. 如果没有找到，尝试备用方法检查全局变量
    if (!websocketInstance) {
      if (window['__readifyWebSocket']) {
        if (window['__readifyWebSocket'].readyState === WebSocket.OPEN) {
          websocketInstance = window['__readifyWebSocket']
        }
      }
    }
    
    // 3. 如果仍然没有找到，检查父组件中的WebSocket管理器
    if (!websocketInstance) {
      if (window['readifyWebSocketManager'] && 
          window['readifyWebSocketManager'].ws &&
          window['readifyWebSocketManager'].ws.readyState === WebSocket.OPEN) {
        websocketInstance = window['readifyWebSocketManager'].ws
      }
    }
    
    // 最终检查
    if (websocketInstance && websocketInstance.readyState === WebSocket.OPEN) {
      
      // 构建消息数据
      const messageData = {
        type: 'sendMessage',
        data: {
          query: message,
          projectId: localProjectId.value.toString(),
          taskType: chatMode.value,
          timestamp: Date.now()
        },
        id: `msg_${Date.now()}_${Math.random().toString(36).substring(2, 10)}`,
        timestamp: Date.now()
      }
      
      
      // 消息响应统一由 handleWebSocketMessage (Path A) 处理，
      // 不再注册额外的 responseHandler，避免 thought 内容重复累加。

      try {
        // 发送消息
        const jsonString = JSON.stringify(messageData)
        websocketInstance.send(jsonString)
        return true
      } catch (error) {
        return false
      }
    } else {
      // WebSocket实例不存在
      console.warn('[WebSocket] - WebSocket实例不存在，无法发送消息')
      return false
    }
  } catch (error) {
    console.error('[WebSocket] - 发送消息时出错:', error)
    return false
  }
}

// 处理发送失败
const handleSendFailed = () => {
  // 重置发送状态
  isSending.value = false
  
  // 添加发送失败提示到最后一条用户消息
  const lastMessageIndex = messages.value.length - 1
  if (lastMessageIndex >= 0 && messages.value[lastMessageIndex].isUser) {
    messages.value.push({
      content: '消息发送失败，请检查网络连接后重试',
      isUser: false,
      timestamp: Date.now()
    })
    
    // 滚动到底部
    nextTick(() => {
      if (chatHistory.value) {
        chatHistory.value.scrollTop = chatHistory.value.scrollHeight
      }
    })
  }
}

// 接口定义，用于对话历史记录
interface ConversationItem {
  id: number;
  userId: number;
  projectId: number;
  query: string;
  answer: string;
  thought?: string;
  createTime: string;
  updateTime: string;
}

// 添加设置对话历史的方法
const setConversationHistory = (conversations: ConversationItem[] | any) => {
  
  // 首先尝试把数据标准化为数组
  let conversationArray: any[] = [];
  
  if (Array.isArray(conversations)) {
    conversationArray = conversations;
  } else if (conversations && typeof conversations === 'object') {
    // 处理单个对话项的情况
    conversationArray = [conversations];
  } else {
    console.error('[历史记录] - 无效的数据格式:', conversations)
    return;
  }
  
  if (conversationArray.length === 0) {
    return;
  }
  
  
  try {
    // 是否保留欢迎消息
    const keepWelcomeMessage = messages.value.length === 1 && 
      !messages.value[0].isUser && 
      messages.value[0].content.includes('您好');
    
    // 清空现有消息，但可能保留欢迎消息
    const welcomeMessage = keepWelcomeMessage ? messages.value[0] : null;
    messages.value = keepWelcomeMessage ? [welcomeMessage] : [];
    
    // 对话创建时间字段可能不同，适配多种格式
    const getTime = (item: any): number => {
      if (item.createdAt) return new Date(item.createdAt).getTime();
      if (item.createTime) return new Date(item.createTime).getTime();
      if (item.time) return new Date(item.time).getTime();
      if (item.timestamp) return typeof item.timestamp === 'number' ? item.timestamp : new Date(item.timestamp).getTime();
      return Date.now();
    };
    
    // 尝试按时间排序(如果有时间字段)
    try {
      conversationArray.sort((a, b) => getTime(a) - getTime(b));
    } catch (sortError) {
      console.warn('[历史记录] - 排序失败，使用原始顺序:', sortError);
    }
    
    
    // 将对话历史转换为消息格式并添加到messages中
    conversationArray.forEach((conv, index) => {
      // 处理新API格式 (有messageType字段的情况)
      if (conv.messageType) {
        if (conv.messageType === 'user') {
          // 用户消息
          messages.value.push({
            content: conv.content || '',
            isUser: true,
            timestamp: getTime(conv)
          });
          
        } else if (conv.messageType === 'assistant') {
          // AI回复
          const thoughtContent = conv.thinking ? 
                               (typeof conv.thinking === 'object' ? conv.thinking.content : conv.thinking) : 
                               null;
          
          messages.value.push({
            content: conv.content || '',
            isUser: false,
            timestamp: getTime(conv),
            thought: thoughtContent,
            thoughtExpanded: false // 默认折叠思考过程
          });
          
        }
        return; // 处理完新格式后返回
      }
      
      // 处理传统格式
      // 处理用户消息
      const userQuery = conv.query || conv.question || (conv.role === 'user' ? conv.content : null);
      
      if (userQuery && typeof userQuery === 'string') {
        messages.value.push({
          content: userQuery,
          isUser: true,
          timestamp: getTime(conv)
        });
        
      }
      
      // 处理AI回复
      const aiResponse = conv.answer || conv.response || (conv.role === 'assistant' ? conv.content : null);
      
      if (aiResponse && typeof aiResponse === 'string') {
        const thoughtContent = conv.thought || conv.thinking || conv.reasoning;
        
        messages.value.push({
          content: aiResponse,
          isUser: false,
          timestamp: conv.updateTime ? new Date(conv.updateTime).getTime() : (getTime(conv) + 1000),
          thought: thoughtContent,
          thoughtExpanded: false // 默认折叠思考过程
        });
        
      }
    });
    
    // 滚动到底部
    nextTick(() => {
      if (chatHistory.value) {
        chatHistory.value.scrollTop = chatHistory.value.scrollHeight;
      }
    });
    
  } catch (error) {
    console.error('[历史记录] - 处理对话历史时出错:', error);
  }
}

// 确保暴露必要的方法给父组件
const exposedMethods = {
  handleWebSocketMessage,
  handleSendFailed,
  setConversationHistory,
  setWebSocketInstance
};

// 自主加载对话历史的方法
const loadConversationHistory = async () => {
  try {
    // 获取项目ID
    const projectId = localProjectId.value
    if (!projectId) {
      return false
    }

    
    // 添加超时控制和错误重试
    let retryCount = 0;
    const maxRetries = 2;
    let success = false;
    let conversationData = [];
    
    while (!success && retryCount <= maxRetries) {
      try {
        // 设置请求超时
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 5000); // 5秒超时
        
        const res = await getProjectConversations(projectId);
        clearTimeout(timeoutId);
        
        
        // 处理响应
        if (res) {
          if (typeof res.code !== 'undefined') {
            if (res.code === '200' && res.data) {
              conversationData = Array.isArray(res.data) ? res.data : 
                                (res.data && typeof res.data === 'object') ? [res.data] : []
            } else {
              console.warn('[Chat自加载] - API返回非成功状态码:', res.code, res.message)
            }
          } else if (Array.isArray(res)) {
            conversationData = res
          } else {
            console.warn('[Chat自加载] - 响应格式不符合预期:', typeof res)
          }
        } else {
          console.warn('[Chat自加载] - 响应为空')
        }
        
        success = true;
      } catch (error) {
        retryCount++;
        console.error(`[Chat自加载] - 请求失败 (${retryCount}/${maxRetries})`, error)
        
        if (retryCount <= maxRetries) {
          await new Promise(resolve => setTimeout(resolve, retryCount * 1000));
        }
      }
    }

    // 检查并设置对话历史
    if (conversationData && conversationData.length > 0) {
      try {
        // 保存历史记录到本地变量
        loadedConversations.value = conversationData
        // 设置对话历史
        setConversationHistory(conversationData)
        return true
      } catch (setError) {
        console.error('[Chat自加载] - 设置对话历史时出错:', setError)
        return false
      }
    } else {
      return false
    }
  } catch (error) {
    return false
  }
}

// 强制重新初始化和渲染对话历史
const forceRefreshHistory = () => {
  // 检查是否已有加载的历史记录
  if (loadedConversations && loadedConversations.length > 0) {
    
    // 保存当前的消息数
    const currentCount = messages.value.length
    
    // 尝试重设历史记录
    setConversationHistory(loadedConversations)
    
    // 检查是否有改变
    const newCount = messages.value.length
    console.log(`[强制刷新] - 刷新前消息数: ${currentCount}, 刷新后: ${newCount}`)
    
    return newCount > currentCount
  }
  return false
}

// 修改defineExpose部分，添加forceRenderMessages方法
defineExpose({
  ...exposedMethods,
  loadConversationHistory,
  forceRefreshHistory,
  forceRenderMessages
})

// 存储清理函数的变量
let cleanupKeydownListener: (() => void) | null = null;

// 创建按键监听器
const createKeydownListener = () => {
  const handleKeydown = (event) => {
    // 按下Ctrl+R或Command+R (Mac)
    if ((event.ctrlKey || event.metaKey) && event.key === 'r') {
      event.preventDefault() // 阻止浏览器刷新
      forceRenderMessages()
    }
  }
  
  // 添加监听器
  window.addEventListener('keydown', handleKeydown)
  
  // 返回清理函数
  return () => {
    window.removeEventListener('keydown', handleKeydown)
  }
}

// 组件卸载前清理资源
onBeforeUnmount(() => {
  
  // 清理按键监听器
  if (typeof cleanupKeydownListener === 'function') {
    cleanupKeydownListener();
  }
  
  // 清理消息渲染检查轮询
  stopRenderingPolling();
  
  // 重置状态
  resetSendingState();
})

// 组件挂载时检查projectId和初始化，并尝试自加载历史
onMounted(() => {
  
  // 添加按键监听器
  cleanupKeydownListener = createKeydownListener()
  
  // 尝试初始化WebSocket连接
  setTimeout(() => {
    const ws = getExistingWebSocket()
    if (ws) {
    } else {
      // 如果还没有可用的WebSocket连接，尝试通过全局变量获取
      setTimeout(() => {
        const retryWs = getExistingWebSocket()
        if (retryWs) {
        } else {
        }
      }, 5000)
    }
  }, 500)

  // 添加强制应用样式的方法
  applySelectOverrides()
  
  // 尝试自主加载对话历史
  setTimeout(() => {
    loadConversationHistory()
      .then(success => {
        
        // 如果加载成功但渲染没有改变，尝试强制刷新
        if (success && messages.value.length <= 1) {
          const refreshResult = forceRefreshHistory()
        }
      })
      .catch(err => {
        console.error('[Chat自加载] - 自加载过程出错:', err)
      })
  }, 1000) // 延迟1000ms，确保组件完全挂载
  
  // 添加额外的延迟强制刷新
  setTimeout(() => {
    if (messages.value.length <= 1) {
      const refreshResult = forceRefreshHistory()
    }
  }, 3000) // 3秒后检查
})

// 添加强制应用样式的方法
const applySelectOverrides = () => {
  // 直接使用全局样式文件，不需要额外创建style元素
  console.log('[样式] - 使用全局样式文件覆盖下拉菜单样式');
  
  // 如果在某些场景下全局样式不生效，可能需要手动添加类名
  // 以下代码仅作为备用逻辑保留
  setTimeout(() => {
    // 确保下拉菜单出现后，样式能够正确应用
    const dropdowns = document.querySelectorAll('.el-select-dropdown');
    if (dropdowns.length > 0) {
      dropdowns.forEach(dropdown => {
        // 添加特定类名以便CSS选择器匹配
        dropdown.classList.add('readify-styled-dropdown');
      });
    }
  }, 1000);
}

// 重置发送状态的方法
const resetSendingState = () => {
  
  if (isSending.value) {
                    isSending.value = false
  }
  
  if (currentResponseIndex.value !== -1) {
                    currentResponseIndex.value = -1
  }
  
  if (currentThought.value || currentAnswer.value) {
                    currentThought.value = ''
                    currentAnswer.value = ''
  }
  
}

// 检查并修复卡住的发送状态
const checkAndFixSendingState = () => {
  if (isSending.value) {
    
    // 如果超过30秒还在发送状态，我们认为可能卡住了
    const lastMessageIndex = messages.value.length - 1
    
    if (lastMessageIndex >= 0) {
      const lastMessage = messages.value[lastMessageIndex]
      const now = Date.now()
      const messageAge = now - lastMessage.timestamp
      
      if (messageAge > 30000) { // 30秒
        console.warn('[状态检查] - 发送状态已持续超过30秒，可能卡住，进行重置')
        resetSendingState()
        return true
      }
                  } else {
      // 没有消息但状态是发送中，直接重置
      console.warn('[状态检查] - 发送状态为true但没有消息，进行重置')
      resetSendingState()
      return true
    }
  }
  
  return false
}

// 添加启动轮询检查的函数
const startRenderingPolling = () => {
  // 清除可能存在的之前的检查
  stopRenderingPolling();
  
  // 重置检查计数
  renderingChecksCount = 0;
  
  // 启动新的轮询检查
  messageRenderingCheckInterval = window.setInterval(() => {
    renderingChecksCount++;
    
    // 检查DOM中的消息数量
    const messageElements = document.querySelectorAll('.message-content');
    
    if (messageElements.length < messages.value.length) {
      console.warn('[轮询检查] - 检测到消息未完全渲染，尝试强制刷新');
      
      // 尝试不同的刷新策略，根据检查次数递增
      if (renderingChecksCount <= 2) {
        // 前两次尝试简单的时间戳更新
        if (messages.value.length > 0) {
          messages.value.forEach(msg => {
            msg.timestamp = Date.now() + Math.random();
          });
        }
      } else if (renderingChecksCount <= 4) {
        // 第3-4次使用基本的强制刷新
        forceRenderMessages();
                } else {
        // 最后一次使用更激进的DOM操作方法
        console.warn('[轮询检查] - 尝试最终解决方案');
        
        // 尝试直接操作DOM
        try {
          const chatHistoryElement = chatHistory.value;
          if (chatHistoryElement) {
            // 添加并移除一个临时元素以触发浏览器重绘
            const tempElement = document.createElement('div');
            tempElement.style.cssText = 'position:absolute;width:100%;height:1px;';
            chatHistoryElement.appendChild(tempElement);
            
            // 强制布局重新计算
            void chatHistoryElement.offsetHeight; 
            
            // 移除临时元素
            setTimeout(() => {
              chatHistoryElement.removeChild(tempElement);
              // 最后的尝试：完全重建消息数组
              const tempArray = JSON.parse(JSON.stringify(messages.value));
              messages.value = [];
              setTimeout(() => messages.value = tempArray, 100);
            }, 50);
          }
        } catch (error) {
          console.error('[轮询检查] - DOM操作失败:', error);
        }
      }
    } else {
      stopRenderingPolling();
    }
    
    // 达到最大检查次数后停止
    if (renderingChecksCount >= MAX_RENDERING_CHECKS) {
      stopRenderingPolling();
      
      // 如果经过多次尝试仍未渲染成功，显示提示
      if (messageElements.length < messages.value.length) {
        console.warn('[轮询检查] - 多次尝试后消息仍未完全渲染');
        ElMessage({
          message: '消息显示可能不完整，请尝试按Ctrl+R刷新视图',
          type: 'warning',
          duration: 3000
        });
      }
    }
  }, 800); // 每800ms检查一次
}

// 添加停止轮询检查的函数
const stopRenderingPolling = () => {
  if (messageRenderingCheckInterval !== null) {
    clearInterval(messageRenderingCheckInterval);
    messageRenderingCheckInterval = null;
    console.log('[轮询检查] - 已停止轮询检查');
  }
}

// 添加专门处理agentComplete消息的函数
const handleAgentComplete = () => {
  console.log('[消息完成] - 开始处理代理消息完成');
  
  try {
    // 1. 重置发送状态
    isSending.value = false;
    
    // 2. 检查最后一条消息是否正确显示
    if (currentResponseIndex.value !== -1 && currentResponseIndex.value < messages.value.length) {
      const finalMessage = messages.value[currentResponseIndex.value];
      console.log('[消息完成] - 检查最终消息内容:', finalMessage.content?.substring(0, 50));
      
      // 如果消息内容是占位内容，但有思考内容，则更新显示
      if ((finalMessage.content === '思考中...' || finalMessage.content === '正在处理...') 
         && finalMessage.thought && finalMessage.thought.length > 0) {
        finalMessage.content = '处理完成';
        // 强制更新时间戳
        finalMessage.timestamp = Date.now();
        console.log('[消息完成] - 已更新最终消息显示');
      }
      
      // 收起思考过程
      if (finalMessage.thought) {
        finalMessage.thoughtExpanded = false;
      }
    }
    
    // 3. 如果没有设置最后一条消息但有未显示的回答，创建一个
    if (currentAnswer.value && (currentResponseIndex.value === -1 || 
       (currentResponseIndex.value >= 0 && 
        messages.value[currentResponseIndex.value].content !== currentAnswer.value))) {
      console.log('[消息完成] - 添加未显示的最终答案');
      messages.value.push({
        content: currentAnswer.value,
        isUser: false,
        timestamp: Date.now()
      });
    }
    
    // 4. 重置所有状态变量
    currentResponseIndex.value = -1;
    currentThought.value = '';
    currentAnswer.value = '';

    console.log('[消息完成] - 状态重置完成');
    
    // 5. 强制重新渲染确保显示正确
                nextTick(() => {
      console.log('[消息完成] - 强制检查渲染');
      // 检查所有消息是否已渲染
      const messageElements = document.querySelectorAll('.message-content');
      if (messageElements.length < messages.value.length) {
        console.warn('[消息完成] - 消息未完全渲染，强制刷新');
        forceRenderMessages();
      } else {
        console.log('[消息完成] - 消息已正确渲染');
        // 仍然确保滚动到底部
        if (chatHistory.value) {
          chatHistory.value.scrollTop = chatHistory.value.scrollHeight;
        }
      }
    });
    
    return true;
  } catch (error) {
    console.error('[消息完成] - 处理代理消息完成时出错:', error);
    // 确保状态重置
    isSending.value = false;
    currentResponseIndex.value = -1;
    currentThought.value = '';
    currentAnswer.value = '';
    return false;
  }
};
</script>

<style scoped>
.chat {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: #ffffff;
  border-radius: 8px;
}

.chat-history {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
  scroll-behavior: smooth;
}

.message-wrapper {
  margin-bottom: 24px;
  display: flex;
  flex-direction: column;
}

.message {
  max-width: 80%;
  margin-bottom: 8px;
  display: flex;
  flex-direction: column;
}

.message.user-message {
  margin-left: auto;
}

.message-content {
  padding: 12px 16px;
  border-radius: 8px;
  font-size: 14px;
  line-height: 1.6;
  word-break: break-word;
}

/* 非用户消息（AI回复）的特殊样式 */
.message:not(.user-message) .message-content {
  padding-top: 0px;  /* 完全移除上边距 */
  margin-top: -4px;  /* 使用负margin进一步拉近距离 */
}

.thought-section {
  border: none;
  border-radius: 8px;
  overflow: visible; /* 改为visible允许内容超出section */
  width: 100%;
  box-shadow: none;
  background-color: transparent;
}

.thought-header {
  padding: 0px 12px;
  display: inline-flex; /* 使宽度自适应内容 */
  align-items: center;
  cursor: pointer;
  user-select: none;
  font-size: 13px;
  color: #606266;
  width: 12.5%; /* 设置为1/8宽度（再缩减一半） */
  min-width: 100px; /* 设置最小宽度防止内容过小 */
}

.thought-header:hover {
  opacity: 0.8;
}

.thought-header .el-icon {
  margin-right: 8px;
  font-size: 12px;
  color: #909399;
}

.thought-content {
  padding: 12px;
  font-size: 13px;
  color: #8c8c8c;
  line-height: 1.5;
  width: 100%; /* 设置为全宽 */
  margin-top: 8px;
  margin-left: 17px;
  border-left: 2px solid #e0e0e0;
  padding-left: 16px;
  padding-top: 0; /* 移除上内边距 */
  background-color: transparent;
  border-top: none;
  border-right: none;
  border-bottom: none;
  box-shadow: none;
}

/* 专门为思考过程内的p标签设置样式 */
.thought-content :deep(p) {
  margin-top: 0;  /* 移除上边距 */
  margin-bottom: 8px;
}

.message-content :deep(.error-block) {
  background-color: rgba(245, 108, 108, 0.1);
  border-left: 3px solid #f56c6c;
  padding: 8px 12px;
  border-radius: 4px;
  font-family: monospace;
}

.message-content :deep(.code-block) {
  background-color: #f5f7fa;
  padding: 12px;
  border-radius: 4px;
  font-family: monospace;
  overflow-x: auto;
}

.message-content :deep(pre) {
  white-space: pre-wrap;
  margin: 0;
}

.user-message .message-content {
  margin-left: auto;
  background-color: rgb(237, 239, 250);  /* 保留用户消息的背景色 */
}

/* 工具错误消息样式 */
.message-content.error-message {
  background-color: rgba(245, 108, 108, 0.1);
  color: #f56c6c;
  border: 1px solid rgba(245, 108, 108, 0.3);
  font-weight: 500;
}

/* Markdown样式 */
.message-content :deep(h1),
.message-content :deep(h2),
.message-content :deep(h3),
.message-content :deep(h4),
.message-content :deep(h5),
.message-content :deep(h6) {
  margin-top: 16px;
  margin-bottom: 8px;
  font-weight: 600;
  line-height: 1.25;
}

.message-content :deep(h1) { font-size: 1.5em; }
.message-content :deep(h2) { font-size: 1.3em; }
.message-content :deep(h3) { font-size: 1.2em; }
.message-content :deep(h4) { font-size: 1.1em; }
.message-content :deep(h5) { font-size: 1em; }
.message-content :deep(h6) { font-size: 1em; color: #666; }

.message-content :deep(p) {
  margin: 8px 0;
  line-height: 1.6;
}

.message-content :deep(ul),
.message-content :deep(ol) {
  padding-left: 20px;
  margin: 8px 0;
}

.message-content :deep(li) {
  margin: 4px 0;
}

.message-content :deep(code) {
  background-color: rgba(175, 184, 193, 0.2);
  padding: 0.2em 0.4em;
  border-radius: 3px;
  font-family: ui-monospace, SFMono-Regular, SF Mono, Menlo, Consolas, Liberation Mono, monospace;
  font-size: 0.9em;
}

.message-content :deep(pre) {
  background-color: #f6f8fa;
  border-radius: 6px;
  padding: 16px;
  overflow-x: auto;
  margin: 8px 0;
}

.message-content :deep(pre code) {
  background-color: transparent;
  padding: 0;
  font-size: 0.9em;
  line-height: 1.45;
  display: block;
}

.message-content :deep(blockquote) {
  margin: 8px 0;
  padding: 0 16px;
  color: #666;
  border-left: 4px solid #ddd;
}

.message-content :deep(table) {
  border-collapse: collapse;
  width: 100%;
  margin: 8px 0;
}

.message-content :deep(th),
.message-content :deep(td) {
  padding: 6px 12px;
  border: 1px solid #ddd;
}

.message-content :deep(th) {
  background-color: #f6f8fa;
  font-weight: 600;
}

.message-content :deep(a) {
  color: #0366d6;
  text-decoration: none;
}

.message-content :deep(a:hover) {
  text-decoration: underline;
}

.message-content :deep(img) {
  max-width: 100%;
  height: auto;
  margin: 8px 0;
  border-radius: 4px;
}

.message-content :deep(hr) {
  height: 1px;
  background-color: #ddd;
  border: none;
  margin: 16px 0;
}

.chat-input {
  padding: 16px;
  border-top: 1px solid #f0f0f0;
}

.input-wrapper {
  position: relative;
  width: 100%;
}

/* 添加选择框容器样式 */
.select-container {
  display: flex;
  gap: 8px;
  position: absolute;
  bottom: 8px;
  left: 12px;
  z-index: 10;
  background-color: rgba(255, 255, 255, 0.8); /* 半透明背景 */
  padding: 2px 4px;
  border-radius: 4px;
}

.mode-select, .model-select {
  width: 100px;
}

/* 为问答模式选择器添加圆角边框 */
.mode-select :deep(.el-input__wrapper) {
  box-shadow: none !important;
  padding: 0 12px !important;
  border-radius: 40px !important;
  border: 0px solid #409EFF !important;
  transition: all 0.3s ease;
  overflow: hidden !important;
}

/* 重载Element Plus默认样式以确保圆角效果 */
.mode-select :deep(.el-input) {
  --el-select-border-radius: 40px !important;
  --el-input-border-radius: 40px !important;
}

.mode-select :deep(.el-input .el-input__wrapper) {
  border-radius: 40px !important;
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

.model-select :deep(.el-input__inner) {
  font-size: 12px;
  height: 24px;
}

.chat-input :deep(.el-textarea__inner) {
  resize: none;
  border-radius: 8px;
  padding: 12px 60px 12px 12px;
  padding-bottom: 40px; /* 增加底部内边距，为选择框腾出空间 */
  font-size: 14px;
  line-height: 1.6;
  min-height: 24px !important;
}

.chat-input :deep(.el-textarea__inner:disabled) {
  background-color: #fbfbfb;
  color: #909399;
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

.send-btn :deep(.is-loading) {
  color: #ffffff;
  font-size: 18px;
  animation: rotating 2s linear infinite;
}

.send-btn:deep(.el-button) {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: transparent;
}

.send-btn:deep(.el-button:focus),
.send-btn:deep(.el-button:hover),
.send-btn:deep(.el-button:active) {
  background-color: inherit;
  border-color: transparent;
  outline: none;
  box-shadow: none;
}

.send-btn.can-send:deep(.el-button:hover) {
  background-color: rgb(57, 77, 209);
}

@keyframes rotating {
  0% {
    transform: rotate(0deg);
  }
  100% {
    transform: rotate(360deg);
  }
}

/* 自定义滚动条样式 */
.chat-history::-webkit-scrollbar,
.thought-content::-webkit-scrollbar {
  width: 4px;
}

.chat-history::-webkit-scrollbar-thumb,
.thought-content::-webkit-scrollbar-thumb {
  background-color: #dcdfe6;
  border-radius: 2px;
}

.chat-history::-webkit-scrollbar-track,
.thought-content::-webkit-scrollbar-track {
  background-color: transparent;
}

/* 为问答模式选择器添加圆角边框 - 使用极高优先级选择器 */
html body .chat .chat-input .input-wrapper .select-container .mode-select :deep(.el-input),
html body .chat .chat-input .input-wrapper .select-container .mode-select :deep(.el-input__wrapper),
.mode-select :deep(.el-input__wrapper) {
  border-radius: 40px !important;
  overflow: hidden !important;
  border: 2px solid #409EFF !important;
  background-color: rgb(237, 239, 250) !important;
  box-shadow: none !important;
}

/* 调整前缀图标样式 */
.mode-select :deep(.el-input__prefix-inner) {
  margin-right: 5px;
}

.mode-select :deep(.el-input__prefix) {
  display: flex;
  align-items: center;
}

.mode-select :deep(.el-input__prefix .el-icon) {
  font-size: 16px;
  color: #409EFF;
}

/* 使用属性选择器进一步提高特异性 */
.chat .chat-input .input-wrapper .select-container [class*="mode-select"] :deep(.el-input__wrapper) {
  border-radius: 40px !important;
  border-color: #409EFF !important;
  background-color: rgb(237, 239, 250) !important;
}

/* 添加针对内部实际元素的样式 */
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

/* 调整模型选择器图标样式 */
.model-select :deep(.el-input__prefix-inner) {
  margin-right: 5px;
}

.model-select :deep(.el-input__prefix) {
  display: flex;
  align-items: center;
}

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
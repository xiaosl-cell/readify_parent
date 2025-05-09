<template>
  <div style="display: none">
    <!-- 这是一个无渲染组件，只处理WebSocket逻辑 -->
  </div>
</template>

<script lang="ts" setup>
import { ref, onMounted, onBeforeUnmount, defineEmits } from 'vue'
import { ElMessage } from 'element-plus'
import { getToken } from '@/utils/auth'

const props = defineProps<{
  projectId: number
}>()

const emit = defineEmits<{
  (e: 'message', data: any): void
  (e: 'error', error: any): void
  (e: 'connected'): void
  (e: 'disconnected'): void
}>()

// WebSocket 相关状态
const ws = ref<WebSocket | null>(null)
const wsReconnectAttempts = ref(0)
const MAX_RECONNECT_ATTEMPTS = 5
const PING_INTERVAL = 30000
let pingTimer: number | null = null
let reconnectTimer: number | null = null
let missedPongCount = ref(0)
const MAX_MISSED_PONG = 3

// 通过WebSocket查询项目文件
const queryProjectFiles = () => {
  if (ws.value?.readyState === WebSocket.OPEN) {
    try {
      const queryMessage = {
        type: 'queryProjectFiles',
        data: {
          projectId: props.projectId
        },
        timestamp: Date.now()
      }
      ws.value.send(JSON.stringify(queryMessage))
    } catch (error) {
      emit('error', error)
    }
  } else {
    emit('error', new Error('WebSocket未连接'))
  }
}

// 通过WebSocket发送消息
const sendMessage = (message: any) => {
  if (!ws.value) {
    emit('error', new Error('WebSocket实例不存在'))
    return false
  }
  
  if (ws.value.readyState === WebSocket.OPEN) {
    try {
      ws.value.send(JSON.stringify(message))
      return true
    } catch (error) {
      emit('error', error)
      return false
    }
  } else if (ws.value.readyState === WebSocket.CONNECTING) {
    // 如果正在连接中，等待连接完成后再发送
    setTimeout(() => {
      if (ws.value?.readyState === WebSocket.OPEN) {
        try {
          ws.value.send(JSON.stringify(message))
        } catch (error) {
          emit('error', error)
        }
      }
    }, 1000)
    return false
  } else {
    emit('error', new Error('WebSocket未连接'))
    return false
  }
}

// 启动心跳检测
const startPingInterval = () => {
  clearPingInterval() // 先清除现有的定时器
  
  pingTimer = window.setInterval(() => {
    if (ws.value?.readyState === WebSocket.OPEN) {
      try {
        ws.value.send(JSON.stringify({ type: 'ping', timestamp: Date.now() }))
        missedPongCount.value++
        
        if (missedPongCount.value >= MAX_MISSED_PONG) {
          ws.value?.close()
          handleReconnect()
        }
      } catch (error) {
        // 错误处理
      }
    }
  }, PING_INTERVAL)
}

// 清除心跳检测
const clearPingInterval = () => {
  if (pingTimer) {
    clearInterval(pingTimer)
    pingTimer = null
  }
}

// 处理重连
const handleReconnect = () => {
  if (wsReconnectAttempts.value >= MAX_RECONNECT_ATTEMPTS) {
    ElMessage.error('WebSocket连接失败，请刷新页面重试')
    return
  }

  if (reconnectTimer) {
    clearTimeout(reconnectTimer)
  }

  wsReconnectAttempts.value++
  const delay = Math.min(1000 * Math.pow(2, wsReconnectAttempts.value), 10000)
  
  reconnectTimer = window.setTimeout(() => {
    initWebSocket()
  }, delay)
}

// 初始化 WebSocket 连接
const initWebSocket = () => {
  // 检查是否有现有连接，如果有则先关闭
  if (ws.value) {
    try {
      ws.value.onclose = null // 移除现有的onclose处理器，防止触发重连
      ws.value.close()
    } catch (closeError) {
      // 错误处理
    }
    ws.value = null
  }
  
  const token = getToken()
  if (!token) {
    ElMessage.error('未找到认证信息')
    return
  }

  try {
    // 使用token参数创建WebSocket连接
    const wsUrl = `ws://localhost:8080/api/v1/ws/readify?token=${encodeURIComponent(token)}`
    ws.value = new WebSocket(wsUrl)

    ws.value.onopen = () => {
      wsReconnectAttempts.value = 0
      missedPongCount.value = 0
      emit('connected')
      startPingInterval()
      queryProjectFiles()
    }

    ws.value.onmessage = (event) => {
      try {
        const data = event.data
        const message = JSON.parse(data)
        handleWebSocketMessage(message)
      } catch (error) {
        // 错误处理
      }
    }

    ws.value.onclose = () => {
      clearPingInterval()
      emit('disconnected')
      handleReconnect()
    }

    ws.value.onerror = (error) => {
      emit('error', error)
    }
  } catch (error) {
    emit('error', error)
  }
}

// 处理 WebSocket 消息
const handleWebSocketMessage = (message: any) => {
  if (!message || !message.type) {
    return
  }

  // 使用消息处理器映射替代switch-case
  const messageHandlers: Record<string, (data: any) => void> = {
    pong: () => {
      missedPongCount.value = 0
    },
    connected: (data) => {
      emit('message', { type: 'connected', data })
    },
    projectFiles: (data) => {
      emit('message', { type: 'projectFiles', data })
    },
    agentMessage: (data) => {
      emit('message', { type: 'agentMessage', data })
    },
    agentComplete: (data) => {
      emit('message', { type: 'agentComplete', data })
    },
    messageSent: (data) => {
      emit('message', { type: 'messageSent', data })
    },
    sendMessageResponse: (data) => {
      emit('message', { type: 'sendMessageResponse', data })
    },
    error: (data) => {
      emit('message', { type: 'error', data })
      emit('error', new Error(data.message || '服务器返回错误'))
    }
  }

  const handler = messageHandlers[message.type]
  if (handler) {
    handler(message.data)
  } else {
    emit('message', message)
  }
}

// 组件挂载时初始化WebSocket
onMounted(() => {
  initWebSocket()
})

// 组件卸载前清理资源
onBeforeUnmount(() => {
  if (ws.value) {
    ws.value.close()
  }
  clearPingInterval()
  if (reconnectTimer) {
    clearTimeout(reconnectTimer)
  }
})

// 暴露方法给父组件
defineExpose({
  ws,
  queryProjectFiles,
  sendMessage,
  initWebSocket
})
</script> 
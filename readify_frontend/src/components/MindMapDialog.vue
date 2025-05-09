<template>
  <el-dialog
    v-model="dialogVisible"
    :title="mindMapTitle"
    width="90%"
    class="mind-map-dialog"
    fullscreen
    :destroy-on-close="true"
    @closed="handleDialogClosed"
    @opened="handleDialogOpened"
  >
    <template #header>
      <div class="dialog-header">
        <div class="dialog-title">
          <span class="main-title">{{ mindMapTitle }}</span>
          <span class="sub-title">思维导图</span>
        </div>
      </div>
    </template>
    
    <div v-loading="loading" class="mind-map-container">
      <div class="svg-container" ref="svgContainer"></div>
    </div>
    
    <template #footer>
      <span class="dialog-footer">
        <el-button @click="dialogVisible = false">关闭</el-button>
      </span>
    </template>
  </el-dialog>
</template>

<script lang="ts" setup>
import { ref, onMounted, onBeforeUnmount, nextTick } from 'vue'
import { ElMessage } from 'element-plus'

const dialogVisible = ref(false)
const svgContainer = ref<HTMLElement | null>(null)
const loading = ref(false)
const mindMapTitle = ref('')
const currentMarkdown = ref('')

// 定义emit事件
const emit = defineEmits<{
  (e: 'open'): void
  (e: 'close'): void
}>()

// 示例Markdown数据
const EXAMPLE_MARKDOWN = `---
title: markmap
markmap:
  colorFreezeLevel: 2
---

## Links

- [Website](https://markmap.js.org/)
- [GitHub](https://github.com/gera2ld/markmap)

## Related Projects

- [coc-markmap](https://github.com/gera2ld/coc-markmap) for Neovim
- [markmap-vscode](https://marketplace.visualstudio.com/items?itemName=gera2ld.markmap-vscode) for VSCode
- [eaf-markmap](https://github.com/emacs-eaf/eaf-markmap) for Emacs

## Features

Note that if blocks and lists appear at the same level, the lists will be ignored.

### Lists

- **strong** ~~del~~ *italic* ==highlight==
- \`inline code\`
- [x] checkbox
- Now we can wrap very very very very long text based on \`maxWidth\` option
- Ordered list
  1. item 1
  2. item 2

### Blocks

\`\`\`js
console.log('hello, JavaScript')
\`\`\`

| Products | Price |
|-|-|
| Apple | 4 |
| Banana | 2 |

![](https://markmap.js.org/favicon.png)
`

// 当对话框打开时进行处理
const handleDialogOpened = () => {
  if (currentMarkdown.value) {
    renderMarkmap()
  }
  // 触发open事件
  emit('open')
}

// 当对话框关闭时进行处理
const handleDialogClosed = () => {
  resetView()
  // 触发close事件
  emit('close')
}

// 渲染思维导图
const renderMarkmap = async () => {
  if (!svgContainer.value) return
  
  try {
    loading.value = true
    console.log('Rendering markmap, container exists:', !!svgContainer.value)
    
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
    // 获取浏览器px高度
    const browserHeight = window.innerHeight
    svg.setAttribute('style', `width: 100%; height: 100%; min-height: ${browserHeight-100}px;`)
    svgContainer.value.appendChild(svg)
    
    // 使用全局对象
    const { Transformer } = window.markmap
    const { Markmap } = window.markmap
    
    // 转换Markdown为mind map数据
    const transformer = new Transformer()
    const markdown = currentMarkdown.value || EXAMPLE_MARKDOWN
    const { root } = transformer.transform(markdown)
    
    console.log('Creating markmap with root:', root)
    
    // 创建markmap并渲染到SVG
    const mm = Markmap.create(svg, { 
      autoFit: true, 
      duration: 500,
      spacingVertical: 20,   // 增加垂直间距
      spacingHorizontal: 120, // 增加水平间距
      maxWidth: 500,         // 限制节点最大宽度
      zoom: true,            // 允许缩放
      pan: true              // 允许平移
    }, root)
    
    // 确保图自适应SVG大小
    setTimeout(() => mm.fit(), 300)
    
    console.log('Markmap rendered successfully')
  } catch (error) {
    console.error('Failed to render markmap:', error)
    ElMessage.error('加载思维导图失败: ' + (error instanceof Error ? error.message : String(error)))
  } finally {
    loading.value = false
  }
}

// 加载思维导图数据
const loadMindMap = async (id: number, title: string) => {
  mindMapTitle.value = title
  currentMarkdown.value = EXAMPLE_MARKDOWN
  
  if (dialogVisible.value && svgContainer.value) {
    renderMarkmap()
  }
}

// 打开对话框
const open = (id: number, title: string) => {
  dialogVisible.value = true
  loadMindMap(id, title)
}

// 使用自定义Markdown数据打开思维导图
const openWithMarkdown = (markdown: string, title: string) => {
  dialogVisible.value = true
  mindMapTitle.value = title
  currentMarkdown.value = markdown
  
  if (dialogVisible.value && svgContainer.value) {
    renderMarkmap()
  }
}

// 重置视图
const resetView = () => {
  mindMapTitle.value = ''
  currentMarkdown.value = ''
  if (svgContainer.value) {
    svgContainer.value.innerHTML = ''
  }
}

// 监听窗口大小变化
const handleResize = () => {
  if (dialogVisible.value && svgContainer.value && svgContainer.value.querySelector('svg')) {
    // 触发重新渲染以适应新尺寸
    renderMarkmap()
  }
}

// 添加窗口大小变化事件监听
onMounted(() => {
  window.addEventListener('resize', handleResize)
})

// 移除事件监听
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
  open,
  openWithMarkdown
})
</script>

<style scoped>
.mind-map-dialog {
  --el-dialog-padding-primary: 0;
}

.mind-map-dialog :deep(.el-dialog__header) {
  margin: 0;
  padding: 28px 32px 24px;
  border-bottom: 1px solid #f0f0f0;
  background: linear-gradient(135deg, #f8f9fa 0%, #ffffff 100%);
}

.dialog-header {
  width: 100%;
}

.dialog-title {
  display: flex;
  align-items: baseline;
  gap: 16px;
}

.main-title {
  color: #303133;
  font-weight: 600;
  font-size: 24px;
  font-family: 'Montserrat', sans-serif;
  background: linear-gradient(135deg, #409EFF 0%, #2c3e50 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  padding: 2px 0;
}

.sub-title {
  color: #909399;
  font-weight: normal;
  font-size: 15px;
  position: relative;
  top: 1px;
}

.mind-map-dialog :deep(.el-dialog__headerbtn) {
  top: 32px;
  right: 32px;
}

.mind-map-dialog :deep(.el-dialog__body) {
  padding: 0;
  height: calc(100vh - 150px); /* 留出头部和底部的空间 */
  min-height: 700px; /* 确保最小高度 */
}

.mind-map-container {
  width: 100%;
  height: 100%;
  overflow: hidden;
  background-color: #fafafa;
}

.svg-container {
  width: 100%;
  height: 100%;
}

/* 确保SVG元素占满整个容器并有足够高度 */
.svg-container svg {
  width: 100% !important;
  height: 100% !important;
}

.mind-map-dialog :deep(.el-dialog__footer) {
  padding: 16px 32px;
  border-top: 1px solid #f0f0f0;
  background: #ffffff;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
}

.dialog-footer .el-button {
  padding: 9px 20px;
  font-size: 14px;
  border-radius: 6px;
}
</style> 
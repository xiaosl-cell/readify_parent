<template>
  <div class="about">
    <el-row>
      <el-col :span="24">
        <h1>关于页面</h1>
        <el-button type="success" @click="showExampleMarkmap">加载示例数据</el-button>
      </el-col>
    </el-row>
    
    <!-- 思维导图对话框 -->
    <MindMapDialog ref="mindMapDialogRef" />
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import MindMapDialog from '@/components/MindMapDialog.vue';

const mindMapDialogRef = ref<InstanceType<typeof MindMapDialog> | null>(null);

// 示例markmap数据
const exampleMarkdownData = `---
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

![](https://markmap.js.org/favicon.png)`;

// 显示示例数据的思维导图
const showExampleMarkmap = () => {
  if (mindMapDialogRef.value) {
    mindMapDialogRef.value.openWithMarkdown(exampleMarkdownData, '示例Markmap数据');
  }
};
</script>

<style scoped>
.about {
  padding: 20px;
}

h1 {
  margin-bottom: 20px;
}

.el-button {
  margin-right: 10px;
}
</style> 
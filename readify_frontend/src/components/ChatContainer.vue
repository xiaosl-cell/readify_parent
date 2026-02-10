<template>
  <div class="chat-container">
    <div class="chat-header">
      <h3>对话</h3>
    </div>
    <div class="chat-content">
      <slot />
    </div>
  </div>
</template>

<script lang="ts" setup>
</script>

<style scoped>
.chat-container {
  flex: 1;
  background: #ffffff;
  border-radius: 8px;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.chat-header {
  height: 56px;
  padding: 0 16px;
  display: flex;
  align-items: center;
  border-bottom: 1px solid #f0f0f0;
}

.chat-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 500;
  color: #303133;
}

.chat-content {
  flex: 1;
  overflow: hidden;
}
</style> 
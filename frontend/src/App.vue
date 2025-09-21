<template>
  <div id="app" class="app-container">
    <router-view />
  </div>
</template>

<script setup lang="ts">
import { useAuthStore } from '@/stores/auth'
import { onMounted } from 'vue'

const authStore = useAuthStore()

onMounted(() => {
  // Initialize auth state from stored token
  authStore.initializeAuth()
})
</script>

<style lang="scss">
* {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}

html, body {
  height: 100%;
  font-family: 'Helvetica Neue', Helvetica, 'PingFang TC', 'Hiragino Sans GB', 'Microsoft JhengHei', '微軟正黑體', Arial, sans-serif;
}

#app {
  height: 100vh;
}

.app-container {
  height: 100%;
  display: flex;
  flex-direction: column;
}

// Element Plus customizations
:root {
  --el-color-primary: #409eff;
  --el-color-primary-light-3: #79bbff;
  --el-color-primary-light-5: #a0cfff;
  --el-color-primary-light-7: #c6e2ff;
  --el-color-primary-light-8: #d9ecff;
  --el-color-primary-light-9: #ecf5ff;
  --el-color-primary-dark-2: #337ecc;
}

.el-table {
  .el-table__cell {
    padding: 8px 0;
  }
}

.el-card {
  border-radius: 8px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}

.el-button {
  border-radius: 4px;
}

.page-container {
  padding: 20px;
  background: #f5f5f5;
  min-height: calc(100vh - 60px);
}

.content-card {
  background: white;
  border-radius: 8px;
  padding: 20px;
  margin-bottom: 20px;
}

.toolbar {
  margin-bottom: 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  
  .toolbar-left {
    display: flex;
    gap: 12px;
    align-items: center;
  }
  
  .toolbar-right {
    display: flex;
    gap: 12px;
    align-items: center;
  }
}

.status-tag {
  &.draft { --el-tag-bg-color: #f4f4f5; --el-tag-text-color: #909399; }
  &.submitted { --el-tag-bg-color: #e1f3d8; --el-tag-text-color: #67c23a; }
  &.approved { --el-tag-bg-color: #f0f9ff; --el-tag-text-color: #409eff; }
  &.rejected { --el-tag-bg-color: #fef0f0; --el-tag-text-color: #f56c6c; }
  &.purchased { --el-tag-bg-color: #f4e2ff; --el-tag-text-color: #722ed1; }
}

.form-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 20px;
  margin-bottom: 20px;
}

.form-actions {
  text-align: right;
  padding-top: 20px;
  border-top: 1px solid #ebeef5;
  
  .el-button + .el-button {
    margin-left: 12px;
  }
}

.table-actions {
  .el-button {
    margin-right: 8px;
  }
}

.pagination-container {
  text-align: right;
  padding: 20px 0;
}

// Responsive design
@media (max-width: 768px) {
  .page-container {
    padding: 10px;
  }
  
  .content-card {
    padding: 15px;
  }
  
  .toolbar {
    flex-direction: column;
    gap: 12px;
    align-items: stretch;
  }
  
  .form-grid {
    grid-template-columns: 1fr;
    gap: 16px;
  }
}
</style>
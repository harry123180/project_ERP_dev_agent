<template>
  <div class="page-404">
    <div class="not-found-container">
      <div class="error-code">404</div>
      <div class="error-message">頁面未找到</div>
      <div class="error-description">
        抱歉，您訪問的頁面不存在或已被移除。
      </div>
      <div class="actions">
        <el-button type="primary" @click="goHome">
          返回首頁
        </el-button>
        <el-button @click="goBack">
          返回上一頁
        </el-button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'

const router = useRouter()

const goHome = () => {
  router.push('/')
}

const goBack = () => {
  router.back()
}
</script>

<style scoped>
.page-404 {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  background: #f5f7fa;
}

.not-found-container {
  text-align: center;
  max-width: 500px;
  padding: 40px;
}

.error-code {
  font-size: 120px;
  font-weight: bold;
  color: #409eff;
  line-height: 1;
  margin-bottom: 20px;
}

.error-message {
  font-size: 24px;
  color: #303133;
  margin-bottom: 15px;
}

.error-description {
  font-size: 16px;
  color: #606266;
  margin-bottom: 30px;
  line-height: 1.5;
}

.actions {
  display: flex;
  gap: 15px;
  justify-content: center;
}
</style>
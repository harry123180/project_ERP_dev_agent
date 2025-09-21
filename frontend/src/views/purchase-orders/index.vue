<template>
  <div class="page-container">
    <div class="content-card">
      <!-- 只在非集運單詳情頁面顯示標題和工具欄 -->
      <template v-if="!isConsolidationDetail">
        <h1>採購管理</h1>
        <div class="toolbar">
          <div class="toolbar-left">
            <el-button type="primary" @click="$router.push('/purchase-orders')">
              採購單列表
            </el-button>
            <el-button @click="$router.push('/purchase-orders/create')">
              手動新增採購單
            </el-button>
          </div>
        </div>
      </template>
      <router-view />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()

// 判斷是否為集運單詳情頁面
const isConsolidationDetail = computed(() => {
  return route.name === 'ConsolidationDetail'
})
</script>
<template>
  <div class="page-container">
    <div class="content-card">
      <h1>會計管理</h1>
      <div class="toolbar">
        <div class="toolbar-left">
          <el-button type="primary" @click="$router.push('/accounting')">
            請款管理
          </el-button>
          <el-button @click="$router.push('/accounting/billing')">
            請款單管理
          </el-button>
          <el-button @click="$router.push('/accounting/payments')">
            付款管理
          </el-button>
        </div>
      </div>
      <router-view />
    </div>
  </div>
</template>

<script setup lang="ts">
// Accounting module entry point with navigation
</script>
<template>
  <div class="page-container">
    <div class="content-card">
      <h1>請購管理</h1>
      <div class="toolbar">
        <div class="toolbar-left">
          <el-button type="primary" @click="$router.push('/requisitions')">
            請購單列表
          </el-button>
          <el-button @click="$router.push('/requisitions/create')">
            新增請購單
          </el-button>
        </div>
      </div>
      <router-view />
    </div>
  </div>
</template>

<script setup lang="ts">
// Requisition module entry point with navigation
</script>
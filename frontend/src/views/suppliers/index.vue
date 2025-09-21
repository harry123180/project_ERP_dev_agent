<template>
  <div class="page-container">
    <div class="content-card">
      <h1>供應商管理</h1>
      <div class="toolbar">
        <div class="toolbar-left">
          <el-button type="primary" @click="$router.push('/suppliers')">
            供應商列表
          </el-button>
          <el-button @click="$router.push('/suppliers/create')">
            新增供應商
          </el-button>
        </div>
      </div>
      <router-view />
    </div>
  </div>
</template>

<script setup lang="ts">
// Suppliers module entry point with navigation
</script>
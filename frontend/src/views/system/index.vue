<template>
  <div class="page-container">
    <div class="content-card">
      <h1>系統管理</h1>
      <div class="toolbar">
        <div class="toolbar-left">
          <el-button type="primary" @click="$router.push('/system/users')">
            用戶管理
          </el-button>
          <el-button @click="$router.push('/system/settings')">
            系統設定
          </el-button>
        </div>
      </div>
      <router-view />
    </div>
  </div>
</template>

<script setup lang="ts">
// System module entry point with navigation
</script>
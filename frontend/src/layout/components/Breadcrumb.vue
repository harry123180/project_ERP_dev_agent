<template>
  <el-breadcrumb class="breadcrumb" separator="/">
    <el-breadcrumb-item
      v-for="(item, index) in breadcrumbs"
      :key="index"
      :to="item.to || undefined"
    >
      {{ item.text }}
    </el-breadcrumb-item>
  </el-breadcrumb>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import type { BreadcrumbItem } from '@/types/common'

const route = useRoute()

const breadcrumbs = computed(() => {
  const items: BreadcrumbItem[] = []
  
  // Add home
  items.push({ text: '首頁', to: '/dashboard' })
  
  // Generate breadcrumbs from route matched records
  const matched = route.matched.filter(record => record.meta && record.meta.title)
  
  matched.forEach((record, index) => {
    // Skip the layout route
    if (record.path === '/') return
    
    const isLast = index === matched.length - 1
    const title = record.meta?.title as string
    
    if (title) {
      items.push({
        text: title,
        to: isLast ? undefined : record.path
      })
    }
  })
  
  // Handle specific route patterns
  if (route.params.id) {
    const routeName = route.name as string
    if (routeName?.includes('Edit')) {
      items[items.length - 1].text = '編輯'
    } else if (routeName?.includes('Detail')) {
      items[items.length - 1].text = '詳情'
    }
  }
  
  return items
})
</script>

<style lang="scss" scoped>
.breadcrumb {
  font-size: 14px;
  
  :deep(.el-breadcrumb__item:last-child .el-breadcrumb__inner) {
    color: #606266;
    font-weight: normal;
  }
  
  :deep(.el-breadcrumb__item .el-breadcrumb__inner) {
    color: #909399;
    font-weight: normal;
  }
  
  :deep(.el-breadcrumb__item .el-breadcrumb__inner:hover) {
    color: #409eff;
    cursor: pointer;
  }
}
</style>
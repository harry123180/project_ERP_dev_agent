/**
 * Project Management Store
 * Handles project creation, tracking, and expenditure management
 * Architecture Lead: Winston
 */

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { Project, ProjectFilters, ProjectExpenditure } from '@/types/project'
import { apiClient } from '@/utils/api'
import { ElMessage } from 'element-plus'

export const useProjectsStore = defineStore('projects', () => {
  // State
  const projects = ref<Project[]>([])
  const currentProject = ref<Project | null>(null)
  const loading = ref(false)
  const filters = ref<ProjectFilters>({
    status: undefined,
    manager_id: undefined,
    search: '',
    start_date: undefined,
    end_date: undefined
  })
  const expenditures = ref<ProjectExpenditure[]>([])
  const expenditureLoading = ref(false)
  
  // Pagination
  const pagination = ref({
    page: 1,
    page_size: 20,
    total: 0,
    has_more: false
  })

  // Getters
  const activeProjects = computed(() => 
    projects.value.filter(project => project.is_active)
  )
  
  const completedProjects = computed(() => 
    projects.value.filter(project => 
      project.end_date && new Date(project.end_date) <= new Date()
    )
  )
  
  const projectsOverBudget = computed(() => 
    projects.value.filter(project => 
      project.budget && project.total_expenditure > project.budget
    )
  )
  
  const filteredProjects = computed(() => {
    let filtered = projects.value
    
    if (filters.value.status) {
      switch (filters.value.status) {
        case 'active':
          filtered = filtered.filter(p => p.is_active)
          break
        case 'inactive':
          filtered = filtered.filter(p => !p.is_active)
          break
        case 'completed':
          filtered = filtered.filter(p => 
            p.end_date && new Date(p.end_date) <= new Date()
          )
          break
      }
    }
    
    if (filters.value.manager_id) {
      filtered = filtered.filter(p => p.manager?.id === filters.value.manager_id)
    }
    
    if (filters.value.search) {
      const searchTerm = filters.value.search.toLowerCase()
      filtered = filtered.filter(p => 
        p.project_name.toLowerCase().includes(searchTerm) ||
        p.project_code.toLowerCase().includes(searchTerm) ||
        (p.project_description && p.project_description.toLowerCase().includes(searchTerm))
      )
    }
    
    return filtered
  })
  
  const projectById = computed(() => (id: number) => 
    projects.value.find(project => project.id === id)
  )
  
  const getProjectStats = computed(() => ({
    total: projects.value.length,
    active: activeProjects.value.length,
    completed: completedProjects.value.length,
    over_budget: projectsOverBudget.value.length,
    total_budget: projects.value.reduce((sum, p) => sum + (p.budget || 0), 0),
    total_expenditure: projects.value.reduce((sum, p) => sum + p.total_expenditure, 0)
  }))

  // Actions
  const fetchProjects = async (options: {
    page?: number
    page_size?: number
    refresh?: boolean
  } = {}) => {
    if (!options.refresh && projects.value.length > 0 && !loading.value) {
      return
    }
    
    loading.value = true
    
    try {
      const params = new URLSearchParams({
        page: (options.page || pagination.value.page).toString(),
        page_size: (options.page_size || pagination.value.page_size).toString(),
        ...(filters.value.status && { status: filters.value.status }),
        ...(filters.value.manager_id && { manager_id: filters.value.manager_id.toString() }),
        ...(filters.value.search && { search: filters.value.search }),
        ...(filters.value.start_date && { start_date: filters.value.start_date }),
        ...(filters.value.end_date && { end_date: filters.value.end_date })
      })
      
      const response = await apiClient.get(`/api/v1/projects?${params}`)
      
      if (response.data.success) {
        projects.value = response.data.data
        pagination.value = response.data.pagination
      } else {
        throw new Error(response.data.error?.message || 'Failed to fetch projects')
      }
    } catch (error) {
      console.error('Error fetching projects:', error)
      ElMessage.error('Failed to load projects')
      throw error
    } finally {
      loading.value = false
    }
  }

  const fetchProjectDetails = async (projectId: number) => {
    loading.value = true
    
    try {
      const response = await apiClient.get(`/api/v1/projects/${projectId}`)
      
      if (response.data.success) {
        currentProject.value = response.data.data
        
        // Update project in the list if it exists
        const index = projects.value.findIndex(p => p.id === projectId)
        if (index !== -1) {
          projects.value[index] = response.data.data
        }
        
        return response.data.data
      } else {
        throw new Error(response.data.error?.message || 'Failed to fetch project details')
      }
    } catch (error) {
      console.error('Error fetching project details:', error)
      ElMessage.error('Failed to load project details')
      throw error
    } finally {
      loading.value = false
    }
  }

  const createProject = async (projectData: {
    project_name: string
    project_code: string
    project_description?: string
    manager_id?: number
    budget?: number
    start_date?: string
    end_date?: string
    is_active?: boolean
  }) => {
    loading.value = true
    
    try {
      const response = await apiClient.post('/api/v1/projects', projectData)
      
      if (response.data.success) {
        const newProject = response.data.data
        projects.value.unshift(newProject)
        currentProject.value = newProject
        
        ElMessage.success('Project created successfully')
        return newProject
      } else {
        throw new Error(response.data.error?.message || 'Failed to create project')
      }
    } catch (error) {
      console.error('Error creating project:', error)
      const message = error.response?.data?.error?.message || 'Failed to create project'
      ElMessage.error(message)
      throw error
    } finally {
      loading.value = false
    }
  }

  const updateProject = async (projectId: number, updates: {
    project_name?: string
    project_description?: string
    manager_id?: number
    budget?: number
    start_date?: string
    end_date?: string
    is_active?: boolean
  }) => {
    loading.value = true
    
    try {
      const response = await apiClient.put(`/api/v1/projects/${projectId}`, updates)
      
      if (response.data.success) {
        const updatedProject = response.data.data
        
        // Update in projects list
        const index = projects.value.findIndex(p => p.id === projectId)
        if (index !== -1) {
          projects.value[index] = { ...projects.value[index], ...updatedProject }
        }
        
        // Update current project if it's the same
        if (currentProject.value?.id === projectId) {
          currentProject.value = { ...currentProject.value, ...updatedProject }
        }
        
        ElMessage.success('Project updated successfully')
        return updatedProject
      } else {
        throw new Error(response.data.error?.message || 'Failed to update project')
      }
    } catch (error) {
      console.error('Error updating project:', error)
      const message = error.response?.data?.error?.message || 'Failed to update project'
      ElMessage.error(message)
      throw error
    } finally {
      loading.value = false
    }
  }

  const fetchProjectExpenditure = async (
    projectId: number, 
    options: {
      start_date?: string
      end_date?: string
      supplier_id?: number
      page?: number
      page_size?: number
    } = {}
  ) => {
    expenditureLoading.value = true
    
    try {
      const params = new URLSearchParams({
        page: (options.page || 1).toString(),
        page_size: (options.page_size || 50).toString(),
        ...(options.start_date && { start_date: options.start_date }),
        ...(options.end_date && { end_date: options.end_date }),
        ...(options.supplier_id && { supplier_id: options.supplier_id.toString() })
      })
      
      const response = await apiClient.get(`/api/v1/projects/${projectId}/expenditure?${params}`)
      
      if (response.data.success) {
        expenditures.value = response.data.data.expenditures
        return response.data.data
      } else {
        throw new Error(response.data.error?.message || 'Failed to fetch expenditure')
      }
    } catch (error) {
      console.error('Error fetching project expenditure:', error)
      ElMessage.error('Failed to load project expenditure')
      throw error
    } finally {
      expenditureLoading.value = false
    }
  }

  const setFilters = (newFilters: Partial<ProjectFilters>) => {
    filters.value = { ...filters.value, ...newFilters }
    // Reset pagination when filters change
    pagination.value.page = 1
  }

  const clearFilters = () => {
    filters.value = {
      status: undefined,
      manager_id: undefined,
      search: '',
      start_date: undefined,
      end_date: undefined
    }
    pagination.value.page = 1
  }

  const setCurrentProject = (project: Project | null) => {
    currentProject.value = project
  }

  const loadMore = async () => {
    if (pagination.value.has_more && !loading.value) {
      await fetchProjects({
        page: pagination.value.page + 1,
        refresh: false
      })
    }
  }

  const refreshProjects = async () => {
    pagination.value.page = 1
    await fetchProjects({ refresh: true })
  }

  // Computed helpers for project management
  const getProjectProgress = computed(() => (project: Project) => {
    if (!project.budget || project.budget === 0) return 0
    return Math.round((project.total_expenditure / project.budget) * 100)
  })

  const getProjectStatus = computed(() => (project: Project) => {
    if (!project.is_active) return 'inactive'
    if (project.end_date && new Date(project.end_date) <= new Date()) return 'completed'
    if (project.start_date && new Date(project.start_date) > new Date()) return 'upcoming'
    return 'active'
  })

  const getProjectBudgetStatus = computed(() => (project: Project) => {
    if (!project.budget) return 'no_budget'
    
    const utilization = project.total_expenditure / project.budget
    if (utilization > 1) return 'over_budget'
    if (utilization > 0.9) return 'near_budget'
    if (utilization > 0.5) return 'on_track'
    return 'under_budget'
  })

  return {
    // State
    projects,
    currentProject,
    loading,
    filters,
    expenditures,
    expenditureLoading,
    pagination,
    
    // Getters
    activeProjects,
    completedProjects,
    projectsOverBudget,
    filteredProjects,
    projectById,
    getProjectStats,
    getProjectProgress,
    getProjectStatus,
    getProjectBudgetStatus,
    
    // Actions
    fetchProjects,
    fetchProjectDetails,
    createProject,
    updateProject,
    fetchProjectExpenditure,
    setFilters,
    clearFilters,
    setCurrentProject,
    loadMore,
    refreshProjects
  }
})
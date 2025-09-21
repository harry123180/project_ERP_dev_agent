import api, { type PaginatedResponse } from './index'
import type { Project } from '@/types/common'

export interface ProjectFilters {
  status?: 'ongoing' | 'completed'
  page?: number
  page_size?: number
  search?: string
}

export interface CreateProjectRequest {
  project_id: string
  project_code?: string
  project_name: string
  description?: string
  project_status: 'ongoing' | 'completed'
  start_date?: string
  end_date?: string
  budget?: number
  customer_name?: string
  customer_contact?: string
  customer_address?: string
  customer_phone?: string
  customer_department?: string
  manager_id?: number
}

export interface UpdateProjectRequest extends Partial<CreateProjectRequest> {}

export const projectsApi = {
  // List projects
  getProjects: async (filters: ProjectFilters = {}): Promise<PaginatedResponse<Project>> => {
    const response = await api.get('/projects', { params: filters })
    return response.data
  },

  // Get project detail with expenditure tracking
  getProject: async (id: string): Promise<Project> => {
    const response = await api.get(`/projects/${id}`)
    return response.data
  },

  // Create project
  createProject: async (data: CreateProjectRequest): Promise<Project> => {
    const response = await api.post('/projects', data)
    return response.data
  },

  // Update project
  updateProject: async (id: string, data: UpdateProjectRequest): Promise<Project> => {
    const response = await api.put(`/projects/${id}`, data)
    return response.data
  },

  // Get all active projects for dropdown
  getActiveProjects: async (): Promise<Project[]> => {
    const response = await api.get('/projects', { 
      params: { status: 'ongoing', page_size: 1000 } 
    })
    return response.data.items || []
  },

  // Get project statistics (weekly, monthly, total expenditures)
  getProjectStatistics: async (id: string): Promise<any> => {
    const response = await api.get(`/projects/${id}/statistics`)
    return response.data
  },

  // Generate project ID
  generateProjectId: async (): Promise<string> => {
    const timestamp = new Date().getTime()
    return `PROJ${timestamp.toString().slice(-8)}`
  },

  // Get project requisitions
  getProjectRequisitions: async (id: string): Promise<any[]> => {
    const response = await api.get(`/projects/${id}/requisitions`)
    return response.data
  }
}
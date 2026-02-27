import apiClient from './client'

export interface UploadResponse {
  filename: string
  path: string
  url: string
  size: number
}

export const uploadsApi = {
  async uploadImage(file: File): Promise<UploadResponse> {
    const formData = new FormData()
    formData.append('file', file)
    const response = await apiClient.post<UploadResponse>('/uploads/images/', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    return response.data
  },

  async deleteImage(url: string): Promise<void> {
    const filename = url.split('/').pop()
    if (filename) {
      await apiClient.delete(`/uploads/images/${filename}`)
    }
  }
}

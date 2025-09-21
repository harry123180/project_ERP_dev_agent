/**
 * 下載檔案工具函數
 */

export function downloadFile(blob: Blob, filename: string) {
  // 方法1: 使用 FileSaver.js 的實現方式（最可靠）
  if (window.navigator && window.navigator.msSaveOrOpenBlob) {
    // For IE
    window.navigator.msSaveOrOpenBlob(blob, filename)
    return
  }

  // 創建隱藏的 a 標籤
  const link = document.createElement('a')
  link.style.display = 'none'
  
  // 創建 blob URL
  const url = window.URL.createObjectURL(blob)
  link.href = url
  link.download = filename
  
  // 設置多個屬性確保下載
  link.setAttribute('download', filename)
  link.setAttribute('href', url)
  link.setAttribute('target', '_blank')
  
  // 添加到 DOM
  document.body.appendChild(link)
  
  // 觸發點擊
  const evt = new MouseEvent('click', {
    view: window,
    bubbles: true,
    cancelable: true
  })
  link.dispatchEvent(evt)
  
  // 清理
  setTimeout(() => {
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)
  }, 100)
}

/**
 * 從後端下載檔案
 */
export async function downloadFromAPI(
  url: string,
  method: string = 'GET',
  data?: any,
  filename?: string,
  token?: string
) {
  const headers: HeadersInit = {
    'Content-Type': 'application/json'
  }
  
  if (token) {
    headers['Authorization'] = `Bearer ${token}`
  }
  
  const options: RequestInit = {
    method,
    headers
  }
  
  if (data && method !== 'GET') {
    options.body = JSON.stringify(data)
  }
  
  const response = await fetch(url, options)
  
  if (!response.ok) {
    throw new Error(`Download failed: ${response.status}`)
  }
  
  const blob = await response.blob()
  
  // 嘗試從 Content-Disposition header 獲取檔名
  if (!filename) {
    const contentDisposition = response.headers.get('content-disposition')
    if (contentDisposition) {
      const filenameMatch = contentDisposition.match(/filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/)
      if (filenameMatch && filenameMatch[1]) {
        filename = filenameMatch[1].replace(/['"]/g, '')
      }
    }
  }
  
  // 如果還是沒有檔名，根據 content-type 生成
  if (!filename) {
    const contentType = response.headers.get('content-type') || ''
    const ext = contentType.includes('pdf') ? 'pdf' : 
                contentType.includes('excel') || contentType.includes('spreadsheet') ? 'xlsx' : 
                'bin'
    filename = `download_${Date.now()}.${ext}`
  }
  
  downloadFile(blob, filename)
  
  return blob
}
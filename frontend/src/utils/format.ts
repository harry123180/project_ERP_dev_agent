/**
 * Format utilities for the ERP application
 */

import dayjs from 'dayjs'

/**
 * Format currency amount
 * @param amount - The amount to format
 * @param currency - Currency symbol (default: 'NT$')
 * @returns Formatted currency string
 */
export const formatCurrency = (amount: number | string | null | undefined, currency = 'NT$'): string => {
  if (amount === null || amount === undefined || amount === '') {
    return `${currency} 0`
  }
  
  const num = typeof amount === 'string' ? parseFloat(amount) : amount
  if (isNaN(num)) {
    return `${currency} 0`
  }
  
  return `${currency} ${num.toLocaleString('zh-TW')}`
}

/**
 * Format date
 * @param date - Date to format (string, Date, or dayjs object)
 * @param format - Format string (default: 'YYYY-MM-DD HH:mm:ss')
 * @returns Formatted date string
 */
export const formatDate = (date: any, format = 'YYYY-MM-DD HH:mm:ss'): string => {
  if (!date) {
    return '-'
  }
  
  return dayjs(date).format(format)
}

/**
 * Format date (date only)
 * @param date - Date to format
 * @returns Formatted date string (YYYY-MM-DD)
 */
export const formatDateOnly = (date: any): string => {
  return formatDate(date, 'YYYY-MM-DD')
}

/**
 * Format time (time only)
 * @param date - Date to format
 * @returns Formatted time string (HH:mm:ss)
 */
export const formatTimeOnly = (date: any): string => {
  return formatDate(date, 'HH:mm:ss')
}

/**
 * Format number with specified decimal places
 * @param num - Number to format
 * @param decimals - Number of decimal places (default: 2)
 * @returns Formatted number string
 */
export const formatNumber = (num: number | string | null | undefined, decimals = 2): string => {
  if (num === null || num === undefined || num === '') {
    return '0'
  }
  
  const number = typeof num === 'string' ? parseFloat(num) : num
  if (isNaN(number)) {
    return '0'
  }
  
  return number.toFixed(decimals)
}

/**
 * Format percentage
 * @param value - Value to format as percentage (0-1)
 * @param decimals - Number of decimal places (default: 1)
 * @returns Formatted percentage string
 */
export const formatPercentage = (value: number | string | null | undefined, decimals = 1): string => {
  if (value === null || value === undefined || value === '') {
    return '0%'
  }
  
  const num = typeof value === 'string' ? parseFloat(value) : value
  if (isNaN(num)) {
    return '0%'
  }
  
  return `${(num * 100).toFixed(decimals)}%`
}

/**
 * Format file size
 * @param bytes - File size in bytes
 * @returns Formatted file size string
 */
export const formatFileSize = (bytes: number | null | undefined): string => {
  if (!bytes || bytes === 0) {
    return '0 B'
  }
  
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(1024))
  
  return `${(bytes / Math.pow(1024, i)).toFixed(2)} ${sizes[i]}`
}

/**
 * Truncate text with ellipsis
 * @param text - Text to truncate
 * @param maxLength - Maximum length (default: 50)
 * @returns Truncated text
 */
export const truncateText = (text: string | null | undefined, maxLength = 50): string => {
  if (!text) {
    return ''
  }
  
  if (text.length <= maxLength) {
    return text
  }
  
  return `${text.substring(0, maxLength)}...`
}

/**
 * Format phone number
 * @param phone - Phone number to format
 * @returns Formatted phone number
 */
export const formatPhone = (phone: string | null | undefined): string => {
  if (!phone) {
    return ''
  }
  
  // Remove all non-digits
  const cleaned = phone.replace(/\D/g, '')
  
  // Format based on length
  if (cleaned.length === 10) {
    // Mobile: 0912-345-678
    return cleaned.replace(/(\d{4})(\d{3})(\d{3})/, '$1-$2-$3')
  } else if (cleaned.length === 9) {
    // Landline: 02-1234-5678
    return cleaned.replace(/(\d{2})(\d{4})(\d{3})/, '$1-$2-$3')
  }
  
  return phone
}

/**
 * Format ID number (mask middle digits)
 * @param id - ID number to format
 * @returns Masked ID number
 */
export const formatMaskedId = (id: string | null | undefined): string => {
  if (!id || id.length < 6) {
    return id || ''
  }
  
  const start = id.substring(0, 3)
  const end = id.substring(id.length - 3)
  const middle = '*'.repeat(id.length - 6)
  
  return `${start}${middle}${end}`
}
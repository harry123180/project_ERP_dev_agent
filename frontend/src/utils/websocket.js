import { io } from 'socket.io-client'
import { useAuthStore } from '@/stores/auth'

class WebSocketManager {
  constructor() {
    this.socket = null
    this.connected = false
    this.reconnectAttempts = 0
    this.maxReconnectAttempts = 5
    this.reconnectDelay = 1000
    this.eventListeners = new Map()
  }

  connect() {
    if (this.socket?.connected) {
      console.log('[WebSocket] Already connected')
      return Promise.resolve()
    }

    return new Promise((resolve, reject) => {
      try {
        const authStore = useAuthStore()
        const token = authStore.token

        if (!token) {
          console.error('[WebSocket] No authentication token found')
          reject(new Error('No authentication token'))
          return
        }

        // Create socket connection
        this.socket = io('http://localhost:5000', {
          auth: {
            token: token
          },
          transports: ['websocket', 'polling'],
          autoConnect: false
        })

        // Connection successful
        this.socket.on('connect', () => {
          console.log('[WebSocket] Connected successfully')
          this.connected = true
          this.reconnectAttempts = 0
          resolve()
        })

        // Connection error
        this.socket.on('connect_error', (error) => {
          console.error('[WebSocket] Connection error:', error)
          this.connected = false
          reject(error)
        })

        // Disconnection
        this.socket.on('disconnect', (reason) => {
          console.log('[WebSocket] Disconnected:', reason)
          this.connected = false
          
          // Attempt to reconnect if not manually disconnected
          if (reason !== 'io client disconnect' && this.reconnectAttempts < this.maxReconnectAttempts) {
            this.attemptReconnect()
          }
        })

        // Authentication success
        this.socket.on('auth_success', (data) => {
          console.log('[WebSocket] Authentication successful:', data)
        })

        // Authentication error
        this.socket.on('auth_error', (data) => {
          console.error('[WebSocket] Authentication failed:', data)
          this.disconnect()
          reject(new Error(data.message || 'Authentication failed'))
        })

        // Start connection
        this.socket.connect()
      } catch (error) {
        console.error('[WebSocket] Connection setup failed:', error)
        reject(error)
      }
    })
  }

  disconnect() {
    if (this.socket) {
      console.log('[WebSocket] Disconnecting...')
      this.socket.disconnect()
      this.socket = null
      this.connected = false
    }
  }

  attemptReconnect() {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error('[WebSocket] Max reconnection attempts reached')
      return
    }

    this.reconnectAttempts++
    const delay = this.reconnectDelay * this.reconnectAttempts

    console.log(`[WebSocket] Attempting to reconnect... (${this.reconnectAttempts}/${this.maxReconnectAttempts})`)
    
    setTimeout(() => {
      this.connect().catch((error) => {
        console.error(`[WebSocket] Reconnection attempt ${this.reconnectAttempts} failed:`, error)
      })
    }, delay)
  }

  // Subscribe to requisition updates
  subscribeToRequisition(requisitionId) {
    if (!this.socket?.connected) {
      console.warn('[WebSocket] Cannot subscribe - not connected')
      return false
    }

    console.log(`[WebSocket] Subscribing to requisition ${requisitionId}`)
    this.socket.emit('subscribe_requisition', { requisition_id: requisitionId })
    return true
  }

  // Unsubscribe from requisition updates
  unsubscribeFromRequisition(requisitionId) {
    if (!this.socket?.connected) {
      console.warn('[WebSocket] Cannot unsubscribe - not connected')
      return false
    }

    console.log(`[WebSocket] Unsubscribing from requisition ${requisitionId}`)
    this.socket.emit('unsubscribe_requisition', { requisition_id: requisitionId })
    return true
  }

  // Listen for requisition status changes
  onRequisitionStatusChange(callback) {
    if (!this.socket) {
      console.warn('[WebSocket] Cannot add listener - socket not initialized')
      return
    }

    console.log('[WebSocket] Adding requisition status change listener')
    this.socket.on('requisition_status_changed', callback)
    
    // Store callback for cleanup
    if (!this.eventListeners.has('requisition_status_changed')) {
      this.eventListeners.set('requisition_status_changed', [])
    }
    this.eventListeners.get('requisition_status_changed').push(callback)
  }

  // Remove requisition status change listeners
  offRequisitionStatusChange(callback = null) {
    if (!this.socket) return

    if (callback) {
      this.socket.off('requisition_status_changed', callback)
      
      // Remove from stored listeners
      const listeners = this.eventListeners.get('requisition_status_changed') || []
      const index = listeners.indexOf(callback)
      if (index > -1) {
        listeners.splice(index, 1)
      }
    } else {
      // Remove all listeners
      this.socket.off('requisition_status_changed')
      this.eventListeners.delete('requisition_status_changed')
    }
  }

  // Generic event listener
  on(event, callback) {
    if (!this.socket) {
      console.warn(`[WebSocket] Cannot add listener for ${event} - socket not initialized`)
      return
    }

    this.socket.on(event, callback)
    
    // Store callback for cleanup
    if (!this.eventListeners.has(event)) {
      this.eventListeners.set(event, [])
    }
    this.eventListeners.get(event).push(callback)
  }

  // Generic event listener removal
  off(event, callback = null) {
    if (!this.socket) return

    if (callback) {
      this.socket.off(event, callback)
      
      // Remove from stored listeners
      const listeners = this.eventListeners.get(event) || []
      const index = listeners.indexOf(callback)
      if (index > -1) {
        listeners.splice(index, 1)
      }
    } else {
      // Remove all listeners for event
      this.socket.off(event)
      this.eventListeners.delete(event)
    }
  }

  // Emit event
  emit(event, data) {
    if (!this.socket?.connected) {
      console.warn(`[WebSocket] Cannot emit ${event} - not connected`)
      return false
    }

    this.socket.emit(event, data)
    return true
  }

  // Check connection status
  isConnected() {
    return this.connected && this.socket?.connected
  }

  // Cleanup all listeners
  cleanup() {
    if (this.socket) {
      // Remove all stored listeners
      for (const [event, callbacks] of this.eventListeners) {
        for (const callback of callbacks) {
          this.socket.off(event, callback)
        }
      }
      this.eventListeners.clear()
    }
  }
}

// Create singleton instance
const webSocketManager = new WebSocketManager()

export default webSocketManager
export { WebSocketManager }
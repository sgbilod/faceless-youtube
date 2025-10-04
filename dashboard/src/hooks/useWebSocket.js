import { useEffect, useState } from 'react'
import wsClient from '../api/websocket'

function useWebSocket() {
  const [isConnected, setIsConnected] = useState(false)

  useEffect(() => {
    // Connect when component mounts
    wsClient.connect()

    // Subscribe to connection events
    const unsubscribe = wsClient.subscribe('connection', (data) => {
      setIsConnected(data.connected)
    })

    // Disconnect when component unmounts
    return () => {
      unsubscribe()
    }
  }, [])

  return {
    isConnected,
    subscribe: wsClient.subscribe.bind(wsClient),
    send: wsClient.send.bind(wsClient),
  }
}

export default useWebSocket

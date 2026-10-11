import { useEffect, useState, useRef } from 'react';
import { LiveEventPayload } from '../types';

export function useLiveUpdates(onEvent?: (event: LiveEventPayload) => void) {
  const [isConnected, setIsConnected] = useState<boolean>(false);
  const [lastEvent, setLastEvent] = useState<LiveEventPayload | null>(null);
  const callbackRef = useRef(onEvent);
  callbackRef.current = onEvent;

  useEffect(() => {
    let es: EventSource | null = null;
    let reconnectTimeout: any = null;
    let isMounted = true;

    function connect() {
      if (!isMounted) return;
      try {
        const rawBase = ((import.meta.env.VITE_API_URL as string) || '').replace(/\/+$/, '');
        const sseUrl = rawBase ? `${rawBase}/api/events` : '/api/events';
        es = new EventSource(sseUrl);

        es.onopen = () => {
          if (isMounted) setIsConnected(true);
        };

        const handleMsg = (e: MessageEvent) => {
          if (!e.data || !isMounted) return;
          try {
            const data = JSON.parse(e.data);
            if (data.status === 'listening' || data.event === 'heartbeat') return;
            setLastEvent(data);
            if (callbackRef.current) {
              callbackRef.current(data);
            }
          } catch {
            // Ignore non-json comments
          }
        };

        es.onmessage = handleMsg;
        es.addEventListener('update', handleMsg);

        es.onerror = () => {
          if (isMounted) setIsConnected(false);
          if (es) {
            es.close();
            es = null;
          }
          if (isMounted) {
            reconnectTimeout = setTimeout(connect, 5000);
          }
        };
      } catch (err) {
        if (isMounted) {
          setIsConnected(false);
          reconnectTimeout = setTimeout(connect, 6000);
        }
      }
    }

    connect();

    return () => {
      isMounted = false;
      if (reconnectTimeout) clearTimeout(reconnectTimeout);
      if (es) es.close();
    };
  }, []);

  return { isConnected, lastEvent };
}

import { useEffect, useState, useRef } from 'react';
import { LiveEventPayload } from '../types';

export function useLiveUpdates(onEvent?: (event: LiveEventPayload) => void) {
  const [isConnected, setIsConnected] = useState<boolean>(false);
  const [lastEvent, setLastEvent] = useState<LiveEventPayload | null>(null);
  const callbackRef = useRef(onEvent);
  callbackRef.current = onEvent;

  const lastProcessedRef = useRef<string>('');

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
            const rawData = JSON.parse(e.data);
            if (rawData.status === 'listening' || rawData.event === 'heartbeat' || rawData.type === 'heartbeat') return;

            const evType = rawData.event || rawData.type || 'update';
            const timestamp = rawData.timestamp || new Date().toISOString();
            const dedupeKey = `${evType}_${timestamp}_${JSON.stringify(rawData.data || {})}`;

            // Deduplicate if identical event received in quick succession
            if (lastProcessedRef.current === dedupeKey) return;
            lastProcessedRef.current = dedupeKey;
            setTimeout(() => {
              if (lastProcessedRef.current === dedupeKey) lastProcessedRef.current = '';
            }, 600);

            const normalized: LiveEventPayload = {
              event: evType,
              timestamp,
              data: rawData.data || rawData,
            };

            setLastEvent(normalized);
            if (callbackRef.current) {
              callbackRef.current(normalized);
            }
          } catch {
            // Ignore non-json comments
          }
        };

        es.onmessage = handleMsg;
        es.addEventListener('update', handleMsg);
        es.addEventListener('knockout_updated', handleMsg);
        es.addEventListener('standings_updated', handleMsg);
        es.addEventListener('result_updated', handleMsg);
        es.addEventListener('match_updated', handleMsg);
        es.addEventListener('fixtures_updated', handleMsg);
        es.addEventListener('fixtures_status_updated', handleMsg);
        es.addEventListener('ceremonial_draw_applied', handleMsg);
        es.addEventListener('ceremonial_draw_reset', handleMsg);
        es.addEventListener('knockout_fixtures_cleared', handleMsg);

        es.onerror = () => {
          if (isMounted) setIsConnected(false);
          if (es) {
            es.close();
            es = null;
          }
          if (isMounted) {
            reconnectTimeout = setTimeout(connect, 3000);
          }
        };
      } catch (err) {
        if (isMounted) {
          setIsConnected(false);
          reconnectTimeout = setTimeout(connect, 4000);
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

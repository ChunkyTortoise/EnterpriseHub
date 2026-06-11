'use client';

import { useEffect, useRef, useState } from 'react';

export type BackendStatus = 'replay' | 'warming' | 'live';

const RETRY_INTERVAL_MS = 10_000;
const MAX_WAIT_MS = 120_000;

/**
 * Pings the demo backend (Render free tier, cold-starts in ~50s). The UI runs in
 * replay mode regardless; this only decides whether the LIVE upgrade is offered.
 */
export function useBackendStatus(): BackendStatus {
  const [status, setStatus] = useState<BackendStatus>('replay');
  const startedAt = useRef<number>(0);

  useEffect(() => {
    let cancelled = false;
    let timer: ReturnType<typeof setTimeout> | undefined;
    startedAt.current = Date.now();

    async function ping() {
      try {
        const response = await fetch('/api/demo/warm', { signal: AbortSignal.timeout(8_000) });
        if (cancelled) return;
        if (response.ok) {
          setStatus('live');
          return;
        }
      } catch {
        // Backend cold or unreachable; stay in replay/warming.
      }
      if (cancelled) return;
      const waited = Date.now() - startedAt.current;
      if (waited < MAX_WAIT_MS) {
        setStatus('warming');
        timer = setTimeout(ping, RETRY_INTERVAL_MS);
      } else {
        setStatus('replay');
      }
    }

    void ping();
    return () => {
      cancelled = true;
      if (timer) clearTimeout(timer);
    };
  }, []);

  return status;
}

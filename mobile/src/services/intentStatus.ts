import { useEffect, useRef, useState } from 'react';

import { getRideIntent, RideIntent } from './apiClient';

const POLL_INTERVAL_MS = 5000;

/**
 * Polls GET /intents/{id} while an intent is open, as a fallback for riders who don't (or can't)
 * receive push notifications. Stops polling once the intent leaves the `open` state
 * (matched/expired/cancelled) so the UI can react to the terminal state.
 */
export function useIntentStatus(intentId: string | null): {
  intent: RideIntent | null;
  error: Error | null;
} {
  const [intent, setIntent] = useState<RideIntent | null>(null);
  const [error, setError] = useState<Error | null>(null);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    if (!intentId) {
      return undefined;
    }

    let cancelled = false;

    const poll = async (): Promise<void> => {
      try {
        const latest = await getRideIntent(intentId);
        if (cancelled) return;
        setIntent(latest);
        if (latest.status !== 'open' && timerRef.current) {
          clearInterval(timerRef.current);
          timerRef.current = null;
        }
      } catch (err) {
        if (!cancelled) setError(err as Error);
      }
    };

    poll();
    timerRef.current = setInterval(poll, POLL_INTERVAL_MS);

    return () => {
      cancelled = true;
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, [intentId]);

  return { intent, error };
}

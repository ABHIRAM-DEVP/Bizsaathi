/**
 * Simple toast notification hook.
 */

import { useState, useCallback } from 'react';

export function useToast() {
  const [message, setMessage] = useState('');
  const [timeoutId, setTimeoutId] = useState<NodeJS.Timeout | null>(null);

  const show = useCallback((msg: string, duration = 2200) => {
    if (timeoutId) clearTimeout(timeoutId);
    setMessage(msg);
    const id = setTimeout(() => setMessage(''), duration);
    setTimeoutId(id);
  }, [timeoutId]);

  return { message, show };
}

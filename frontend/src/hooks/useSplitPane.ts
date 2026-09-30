/**
 * ==============================================================================
 * ClinSaarthi AI - Split-Pane Resizing Hook
 * ==============================================================================
 * Calculates mouse drag coordinates to resize the dual-pane workspace smoothly
 * between minimum 35% and maximum 75% width limits.
 *
 * Python/React Concepts Demonstrated:
 * 1. Event Listeners & Lifecycle: Subscribes mousemove and mouseup listeners to
 *    window on mousedown, and guarantees clean removal on unmount.
 * 2. Bounds Clamping: Enforces boundary constraints to prevent visual clipping.
 * ==============================================================================
 */

import { useState, useCallback, useEffect } from 'react';

export function useSplitPane(initialLeftPercentage = 58) {
  const [leftWidthPercent, setLeftWidthPercent] = useState<number>(initialLeftPercentage);
  const [isDragging, setIsDragging] = useState<boolean>(false);

  const startDragging = useCallback(() => {
    setIsDragging(true);
  }, []);

  const stopDragging = useCallback(() => {
    setIsDragging(false);
  }, []);

  const onMouseMove = useCallback(
    (e: MouseEvent) => {
      if (!isDragging) return;

      const totalWidth = window.innerWidth;
      const newPercent = (e.clientX / totalWidth) * 100;

      // Clamp between 35% and 75%
      const clamped = Math.max(35, Math.min(75, newPercent));
      setLeftWidthPercent(clamped);
    },
    [isDragging]
  );

  useEffect(() => {
    if (isDragging) {
      window.addEventListener('mousemove', onMouseMove);
      window.addEventListener('mouseup', stopDragging);
      document.body.style.cursor = 'col-resize';
      document.body.style.userSelect = 'none';
    } else {
      window.removeEventListener('mousemove', onMouseMove);
      window.removeEventListener('mouseup', stopDragging);
      document.body.style.cursor = '';
      document.body.style.userSelect = '';
    }

    return () => {
      window.removeEventListener('mousemove', onMouseMove);
      window.removeEventListener('mouseup', stopDragging);
      document.body.style.cursor = '';
      document.body.style.userSelect = '';
    };
  }, [isDragging, onMouseMove, stopDragging]);

  return {
    leftWidthPercent,
    isDragging,
    startDragging,
  };
}

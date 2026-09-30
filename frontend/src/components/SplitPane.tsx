import React from 'react';
import { useSplitPane } from '../hooks/useSplitPane';

interface SplitPaneProps {
  left: React.ReactNode;
  right: React.ReactNode;
  initialLeftPercentage?: number;
}

export const SplitPane: React.FC<SplitPaneProps> = ({
  left,
  right,
  initialLeftPercentage = 58,
}) => {
  const { leftWidthPercent, isDragging, startDragging } = useSplitPane(initialLeftPercentage);

  return (
    <div
      style={{
        display: 'flex',
        flex: 1,
        width: '100%',
        height: 'calc(100vh - 65px)',
        overflow: 'hidden',
        position: 'relative',
      }}
    >
      {/* Left Pane (Chat & Consultation) */}
      <div
        style={{
          width: `${leftWidthPercent}%`,
          height: '100%',
          display: 'flex',
          flexDirection: 'column',
          overflow: 'hidden',
        }}
      >
        {left}
      </div>

      {/* Resizer Divider Handle */}
      <div
        onMouseDown={startDragging}
        className={`resizer-handle ${isDragging ? 'dragging' : ''}`}
        title="Drag to adjust split-pane layout"
      />

      {/* Right Pane (Source & Bounding Box Viewer) */}
      <div
        style={{
          width: `${100 - leftWidthPercent}%`,
          height: '100%',
          display: 'flex',
          flexDirection: 'column',
          overflow: 'hidden',
        }}
      >
        {right}
      </div>
    </div>
  );
};

import React from 'react';

interface ControlPanelProps {
  isMining: boolean;
  onStart: () => void;
  onStop: () => void;
}

const ControlPanel: React.FC<ControlPanelProps> = ({ isMining, onStart, onStop }) => {
  return (
    <div className="flex space-x-4">
      <button
        onClick={onStart}
        disabled={isMining}
        className={`px-6 py-3 rounded-md font-medium ${
          isMining 
            ? 'bg-slate-700 text-gray-400 cursor-not-allowed' 
            : 'bg-emerald-400 text-slate-950 hover:bg-emerald-300'
        }`}
      >
        {isMining ? 'Mining...' : 'Start Mining'}
      </button>
      <button
        onClick={onStop}
        disabled={!isMining}
        className={`px-6 py-3 rounded-md font-medium ${
          !isMining 
            ? 'bg-slate-700 text-gray-400 cursor-not-allowed' 
            : 'bg-rose-500 text-white hover:bg-rose-400'
        }`}
      >
        Stop Mining
      </button>
    </div>
  );
};

export default ControlPanel;
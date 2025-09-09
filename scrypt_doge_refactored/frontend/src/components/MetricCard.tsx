import React from 'react';

interface MetricCardProps {
  label: string;
  value: string;
  unit: string;
  trend: 'up' | 'down' | 'neutral';
}

const MetricCard: React.FC<MetricCardProps> = ({ label, value, unit, trend }) => {
  const getTrendIcon = () => {
    switch (trend) {
      case 'up':
        return (
          <svg className="w-5 h-5 text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 15l7-7 7 7" />
          </svg>
        );
      case 'down':
        return (
          <svg className="w-5 h-5 text-rose-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        );
      default:
        return (
          <svg className="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
          </svg>
        );
    }
  };

  return (
    <div className="bg-slate-800 rounded-lg p-4 flex flex-col">
      <div className="flex justify-between items-start">
        <div>
          <h3 className="text-sm font-medium text-gray-400">{label}</h3>
          <p className="text-2xl font-bold mt-1">
            {value} <span className="text-sm font-normal text-gray-400">{unit}</span>
          </p>
        </div>
        {getTrendIcon()}
      </div>
      <div className="mt-4 h-2 bg-slate-700 rounded-full overflow-hidden">
        <div 
          className={`h-full ${trend === 'up' ? 'bg-emerald-400' : trend === 'down' ? 'bg-rose-500' : 'bg-gray-400'}`} 
          style={{ width: `${Math.min(100, Math.abs(parseFloat(value)) / 10)}%` }}
        ></div>
      </div>
    </div>
  );
};

export default MetricCard;
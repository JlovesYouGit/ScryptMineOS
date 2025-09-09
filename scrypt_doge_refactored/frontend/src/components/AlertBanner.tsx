import React from 'react';

interface AlertBannerProps {
  message: string;
}

const AlertBanner: React.FC<AlertBannerProps> = ({ message }) => {
  return (
    <div className="bg-rose-500/20 border border-rose-500/30 rounded-lg p-4 flex items-start">
      <svg className="w-5 h-5 text-rose-500 mr-3 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
      </svg>
      <div>
        <h4 className="font-medium text-rose-500">Alert</h4>
        <p className="text-sm">{message}</p>
      </div>
    </div>
  );
};

export default AlertBanner;
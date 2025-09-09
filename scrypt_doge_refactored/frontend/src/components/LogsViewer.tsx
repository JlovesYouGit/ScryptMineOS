import React, { useState, useEffect, useRef } from 'react';

interface LogEntry {
  timestamp: string;
  level: 'info' | 'warn' | 'error';
  message: string;
}

const LogsViewer: React.FC = () => {
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [followLogs, setFollowLogs] = useState(true);
  const logsEndRef = useRef<HTMLDivElement>(null);
  const eventSourceRef = useRef<EventSource | null>(null);

  // Connect to the SSE endpoint for real logs
  useEffect(() => {
    // Use HTTPS in production, HTTP in development
    const protocol = window.location.protocol === 'https:' ? 'https:' : 'http:';
    const eventSourceUrl = `${protocol}//${window.location.host}/api/logs`;
    
    console.log('Connecting to log stream at:', eventSourceUrl);
    const eventSource = new EventSource(eventSourceUrl);
    eventSourceRef.current = eventSource;

    eventSource.onopen = () => {
      console.log('Log stream connected successfully');
      // Add success log entry
      const successLog: LogEntry = {
        timestamp: new Date().toISOString(),
        level: 'info',
        message: 'Connected to log stream'
      };
      setLogs(prev => [...prev.slice(-49), successLog]);
    };

    eventSource.onmessage = (event) => {
      try {
        const logData = JSON.parse(event.data);
        const newLog: LogEntry = {
          timestamp: new Date().toISOString(),
          level: logData.level || 'info',
          message: logData.message || event.data
        };
        setLogs(prev => [...prev.slice(-49), newLog]); // Keep only last 50 logs
      } catch (e) {
        // Fallback for non-JSON messages
        const newLog: LogEntry = {
          timestamp: new Date().toISOString(),
          level: 'info',
          message: event.data
        };
        setLogs(prev => [...prev.slice(-49), newLog]);
      }
    };

    eventSource.onerror = (error) => {
      console.error('EventSource failed:', error);
      // Add error log entry with more details
      const errorLog: LogEntry = {
        timestamp: new Date().toISOString(),
        level: 'error',
        message: `Failed to connect to log stream. Check console for details.`
      };
      setLogs(prev => [...prev.slice(-49), errorLog]);
    };

    return () => {
      if (eventSourceRef.current) {
        console.log('Closing log stream connection');
        eventSourceRef.current.close();
      }
    };
  }, []);

  useEffect(() => {
    if (followLogs && logsEndRef.current) {
      logsEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [logs, followLogs]);

  const getLogLevelClass = (level: string) => {
    switch (level) {
      case 'warn':
        return 'text-yellow-500';
      case 'error':
        return 'text-rose-500';
      default:
        return 'text-gray-300';
    }
  };

  return (
    <div className="bg-slate-800 rounded-lg overflow-hidden flex flex-col h-[600px]">
      <div className="p-4 border-b border-slate-700 flex justify-between items-center">
        <h2 className="text-xl font-bold">Mining Logs</h2>
        <label className="flex items-center space-x-2">
          <input
            type="checkbox"
            checked={followLogs}
            onChange={(e) => setFollowLogs(e.target.checked)}
            className="rounded text-emerald-400 focus:ring-emerald-400"
          />
          <span>Follow logs</span>
        </label>
      </div>
      <div className="flex-1 overflow-y-auto p-4 font-mono text-sm">
        {logs.map((log, index) => (
          <div key={index} className="mb-1 flex">
            <span className="text-gray-500 mr-4">{new Date(log.timestamp).toLocaleTimeString()}</span>
            <span className={getLogLevelClass(log.level)}>[{log.level.toUpperCase()}]</span>
            <span className="ml-2">{log.message}</span>
          </div>
        ))}
        <div ref={logsEndRef} />
      </div>
    </div>
  );
};

export default LogsViewer;
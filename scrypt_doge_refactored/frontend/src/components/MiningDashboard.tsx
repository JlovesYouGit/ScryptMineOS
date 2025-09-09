import { useState, useEffect, useRef } from 'react';
import MetricCard from './MetricCard';
import ControlPanel from './ControlPanel';
import AlertBanner from './AlertBanner';

interface MiningMetrics {
  hashrate: number;
  shares: number;
  validShares: number;
  invalidShares: number;
  temperature: number;
  power: number;
  profit: number;
  is_authorized: boolean;
}

interface MiningConfig {
  ltcAddress: string;
  dogeAddress: string;
  workerName: string;
  payoutAddress: string;
  ltcPoolHost: string;
  ltcPoolPort: number;
  dogePoolHost: string;
  dogePoolPort: number;
}

interface MiningResponse {
  jobId?: string;
  state?: string;
  status?: any;
  message?: string;
  error?: string;
  detail?: {
    error?: string;
    message?: string;
  };
}

const MiningDashboard = () => {
  const [metrics, setMetrics] = useState<MiningMetrics>({
    hashrate: 0,
    shares: 0,
    validShares: 0,
    invalidShares: 0,
    temperature: 0,
    power: 0,
    profit: 0,
    is_authorized: false
  });
  const [isMining, setIsMining] = useState(false);
  const [alerts, setAlerts] = useState<string[]>([]);
  const [config, setConfig] = useState<MiningConfig>({
    ltcAddress: '',
    dogeAddress: '',
    workerName: '',
    payoutAddress: '',
    ltcPoolHost: '',
    ltcPoolPort: 8888,
    dogePoolHost: '',
    dogePoolPort: 8057
  });
  
  const wsRef = useRef<WebSocket | null>(null);

  // Fetch configuration from backend on component mount
  useEffect(() => {
    const fetchConfig = async () => {
      try {
        // Use HTTPS in production, HTTP in development
        const protocol = window.location.protocol;
        const response = await fetch(`${protocol}//${window.location.host}/api/config`);
        if (response.ok) {
          const data = await response.json();
          setConfig(data);
        } else {
          // Try to parse error response
          let errorMessage = 'Failed to fetch configuration';
          try {
            const errorData = await response.json();
            errorMessage = errorData.message || errorData.error || errorMessage;
          } catch (e) {
            // If JSON parsing fails, use status text
            errorMessage = response.statusText || errorMessage;
          }
          console.error('Failed to fetch configuration from backend:', errorMessage);
          // Use default values if backend request fails
          setConfig({
            ltcAddress: 'ltc1qpptg85asckrjy9ygygh2tfgxqwzn6672zmzq99',
            dogeAddress: 'DGKsuHU6XdghZtA2aWGqvrZrkWracQJzPd',
            workerName: 'rig01',
            payoutAddress: '',
            ltcPoolHost: 'ltc.f2pool.com',
            ltcPoolPort: 8888,
            dogePoolHost: 'doge.zsolo.bid',
            dogePoolPort: 8057
          });
        }
      } catch (error) {
        console.error('Network error while fetching configuration:', error);
        // Use default values if request fails
        setConfig({
          ltcAddress: 'ltc1qpptg85asckrjy9ygygh2tfgxqwzn6672zmzq99',
          dogeAddress: 'DGKsuHU6XdghZtA2aWGqvrZrkWracQJzPd',
          workerName: 'rig01',
          payoutAddress: '',
          ltcPoolHost: 'ltc.f2pool.com',
          ltcPoolPort: 8888,
          dogePoolHost: 'doge.zsolo.bid',
          dogePoolPort: 8057
        });
      }
    };

    fetchConfig();
  }, []);

  // Connect to WebSocket for real-time metrics
  useEffect(() => {
    // Create WebSocket connection - use wss:// in production, ws:// in development
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const ws = new WebSocket(`${protocol}//${window.location.host}/ws/metrics`);
    wsRef.current = ws;

    ws.onopen = () => {
      console.log('Connected to metrics WebSocket');
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        setMetrics(data);
        
        // Check authorization status and add alert if not authorized
        if (!data.is_authorized && !alerts.includes('Not authorized with pool')) {
          setAlerts(prev => [...prev, 'Not authorized with pool - check your payout address']);
        } else if (data.is_authorized && alerts.includes('Not authorized with pool')) {
          setAlerts(prev => prev.filter(alert => alert !== 'Not authorized with pool'));
        }
      } catch (error) {
        console.error('Failed to parse WebSocket message:', error);
      }
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };

    ws.onclose = () => {
      console.log('WebSocket connection closed');
    };

    // Clean up WebSocket connection
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [alerts]);

  const handleStart = async () => {
    try {
      // Use HTTPS in production, HTTP in development
      const protocol = window.location.protocol;
      const response = await fetch(`${protocol}//${window.location.host}/api/actions/start`, { method: 'POST' });
      
      // Check if response has content before trying to parse JSON
      const contentType = response.headers.get('content-type');
      if (contentType && contentType.includes('application/json')) {
        const data: MiningResponse = await response.json();
        
        if (response.ok) {
          setIsMining(true);
          // Add success message to alerts
          if (data.message && !alerts.includes(data.message)) {
            setAlerts(prev => [...prev, data.message || 'Mining started successfully']);
          }
        } else {
          console.error('Failed to start mining:', data);
          const errorMessage = data.detail?.message || data.message || data.error || 'Unknown error occurred';
          alert('Failed to start mining: ' + errorMessage);
          
          // Add error to alerts
          if (errorMessage && !alerts.includes(errorMessage)) {
            setAlerts(prev => [...prev, `Error: ${errorMessage}`]);
          }
        }
      } else {
        // Handle non-JSON responses
        const text = await response.text();
        if (response.ok) {
          setIsMining(true);
          const successMessage = text || 'Mining started successfully';
          if (!alerts.includes(successMessage)) {
            setAlerts(prev => [...prev, successMessage]);
          }
        } else {
          const errorMessage = text || `HTTP Error: ${response.status} ${response.statusText}`;
          console.error('Failed to start mining:', errorMessage);
          alert('Failed to start mining: ' + errorMessage);
          
          if (!alerts.includes(errorMessage)) {
            setAlerts(prev => [...prev, `Error: ${errorMessage}`]);
          }
        }
      }
    } catch (error: any) {
      console.error('Network error while starting mining:', error);
      const errorMessage = error.message || 'Network error occurred';
      alert('Failed to start mining: ' + errorMessage);
      
      // Add error to alerts
      if (errorMessage && !alerts.includes(errorMessage)) {
        setAlerts(prev => [...prev, `Error: ${errorMessage}`]);
      }
    }
  };

  const handleStop = async () => {
    try {
      // Use HTTPS in production, HTTP in development
      const protocol = window.location.protocol;
      const response = await fetch(`${protocol}//${window.location.host}/api/actions/stop`, { method: 'POST' });
      
      // Check if response has content before trying to parse JSON
      const contentType = response.headers.get('content-type');
      if (contentType && contentType.includes('application/json')) {
        const data: MiningResponse = await response.json();
        
        if (response.ok) {
          setIsMining(false);
          // Add success message to alerts
          if (data.message && !alerts.includes(data.message)) {
            setAlerts(prev => [...prev, data.message || 'Mining stopped successfully']);
          }
        } else {
          console.error('Failed to stop mining:', data);
          const errorMessage = data.detail?.message || data.message || data.error || 'Unknown error occurred';
          alert('Failed to stop mining: ' + errorMessage);
          
          // Add error to alerts
          if (errorMessage && !alerts.includes(errorMessage)) {
            setAlerts(prev => [...prev, `Error: ${errorMessage}`]);
          }
        }
      } else {
        // Handle non-JSON responses
        const text = await response.text();
        if (response.ok) {
          setIsMining(false);
          const successMessage = text || 'Mining stopped successfully';
          if (!alerts.includes(successMessage)) {
            setAlerts(prev => [...prev, successMessage]);
          }
        } else {
          const errorMessage = text || `HTTP Error: ${response.status} ${response.statusText}`;
          console.error('Failed to stop mining:', errorMessage);
          alert('Failed to stop mining: ' + errorMessage);
          
          if (!alerts.includes(errorMessage)) {
            setAlerts(prev => [...prev, `Error: ${errorMessage}`]);
          }
        }
      }
    } catch (error: any) {
      console.error('Network error while stopping mining:', error);
      const errorMessage = error.message || 'Network error occurred';
      alert('Failed to stop mining: ' + errorMessage);
      
      // Add error to alerts
      if (errorMessage && !alerts.includes(errorMessage)) {
        setAlerts(prev => [...prev, `Error: ${errorMessage}`]);
      }
    }
  };

  // Format wallet addresses for display (show first 6 and last 4 characters)
  const formatWalletAddress = (address: string) => {
    if (address.length <= 10) return address;
    return `${address.substring(0, 6)}...${address.substring(address.length - 4)}`;
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold">Mining Dashboard</h2>
        <ControlPanel 
          isMining={isMining} 
          onStart={handleStart} 
          onStop={handleStop} 
        />
      </div>

      {alerts.length > 0 && (
        <div className="space-y-2">
          {alerts.map((alert, index) => (
            <AlertBanner key={index} message={alert} />
          ))}
        </div>
      )}

      {/* Wallet and Pool Information */}
      <div className="bg-slate-800 rounded-lg p-4">
        <h3 className="text-lg font-semibold mb-4">Mining Configuration</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <div className="text-sm text-gray-400">Payout Address (Immutable)</div>
            <div className="font-mono text-emerald-400 bg-slate-700 p-2 rounded">
              {config.payoutAddress ? formatWalletAddress(config.payoutAddress) : 'Not set - please set PAYOUT_ADDR environment variable'}
            </div>
          </div>
          <div>
            <div className="text-sm text-gray-400">Worker Name</div>
            <div className="font-mono">{config.workerName || 'Loading...'}</div>
          </div>
          <div>
            <div className="text-sm text-gray-400">Litecoin Wallet</div>
            <div className="font-mono text-emerald-400">{config.ltcAddress ? formatWalletAddress(config.ltcAddress) : 'Loading...'}</div>
          </div>
          <div>
            <div className="text-sm text-gray-400">Dogecoin Wallet</div>
            <div className="font-mono text-emerald-400">{config.dogeAddress ? formatWalletAddress(config.dogeAddress) : 'Loading...'}</div>
          </div>
          <div>
            <div className="text-sm text-gray-400">Litecoin Pool</div>
            <div className="font-mono">{config.ltcPoolHost ? `${config.ltcPoolHost}:${config.ltcPoolPort}` : 'Loading...'}</div>
          </div>
          <div>
            <div className="text-sm text-gray-400">Dogecoin Pool</div>
            <div className="font-mono">{config.dogePoolHost ? `${config.dogePoolHost}:${config.dogePoolPort}` : 'Loading...'}</div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard 
          label="Hashrate" 
          value={metrics.hashrate.toFixed(2)} 
          unit="MH/s" 
          trend="up" 
        />
        <MetricCard 
          label="Valid Shares" 
          value={metrics.validShares.toString()} 
          unit="shares" 
          trend="up" 
        />
        <MetricCard 
          label="Temperature" 
          value={metrics.temperature.toFixed(1)} 
          unit="°C" 
          trend={metrics.temperature > 75 ? "down" : "neutral"} 
        />
        <MetricCard 
          label="Profit" 
          value={metrics.profit.toFixed(4)} 
          unit="USD" 
          trend="up" 
        />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="bg-slate-800 rounded-lg p-4">
          <h3 className="text-lg font-semibold mb-4">Share Statistics</h3>
          <div className="space-y-2">
            <div className="flex justify-between">
              <span>Valid Shares:</span>
              <span>{metrics.validShares}</span>
            </div>
            <div className="flex justify-between">
              <span>Invalid Shares:</span>
              <span>{metrics.invalidShares}</span>
            </div>
            <div className="flex justify-between">
              <span>Acceptance Rate:</span>
              <span>
                {metrics.shares > 0 
                  ? ((metrics.validShares / metrics.shares) * 100).toFixed(2) + '%' 
                  : '0%'}
              </span>
            </div>
          </div>
        </div>

        <div className="bg-slate-800 rounded-lg p-4">
          <h3 className="text-lg font-semibold mb-4">Power Consumption</h3>
          <div className="space-y-2">
            <div className="flex justify-between">
              <span>Power Usage:</span>
              <span>{metrics.power.toFixed(1)} W</span>
            </div>
            <div className="flex justify-between">
              <span>Efficiency:</span>
              <span>
                {metrics.power > 0 
                  ? (metrics.hashrate / (metrics.power / 1000)).toFixed(2) + ' MH/J'
                  : '0 MH/J'}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default MiningDashboard;
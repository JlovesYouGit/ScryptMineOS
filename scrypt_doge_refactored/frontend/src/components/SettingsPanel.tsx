import React, { useState, useEffect } from 'react';

interface Settings {
  workerName: string;
  maxTemperature: number;
  minProfitMargin: number;
}

const SettingsPanel: React.FC = () => {
  const [settings, setSettings] = useState<Settings>({
    workerName: '',
    maxTemperature: 80,
    minProfitMargin: 0.5
  });
  const [isLoading, setIsLoading] = useState(true);

  // Load settings from API on component mount
  useEffect(() => {
    const fetchSettings = async () => {
      try {
        // Use HTTPS in production, HTTP in development
        const protocol = window.location.protocol;
        const response = await fetch(`${protocol}//${window.location.host}/api/config`);
        if (response.ok) {
          const data = await response.json();
          setSettings(prev => ({
            ...prev,
            workerName: data.workerName || '',
            maxTemperature: 80,
            minProfitMargin: 0.5
          }));
        } else {
          console.error('Failed to fetch settings from backend');
          // Use default values if backend request fails
          setSettings(prev => ({
            ...prev,
            workerName: 'rig01',
            maxTemperature: 80,
            minProfitMargin: 0.5
          }));
        }
      } catch (error) {
        console.error('Failed to fetch settings:', error);
        // Use default values if request fails
        setSettings(prev => ({
          ...prev,
          workerName: 'rig01',
          maxTemperature: 80,
          minProfitMargin: 0.5
        }));
      } finally {
        setIsLoading(false);
      }
    };

    fetchSettings();
  }, []);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value, type } = e.target;
    const newValue = type === 'number' ? parseFloat(value) || 0 : value;
    setSettings(prev => ({
      ...prev,
      [name]: newValue
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      // Use HTTPS in production, HTTP in development
      const protocol = window.location.protocol;
      const response = await fetch(`${protocol}//${window.location.host}/api/config`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          workerName: settings.workerName,
          maxTemperature: settings.maxTemperature,
          minProfitMargin: settings.minProfitMargin
        })
      });
      if (response.ok) {
        // Save to localStorage as well
        localStorage.setItem('miningSettings', JSON.stringify(settings));
        alert('Settings saved successfully!');
      } else {
        alert('Failed to save settings');
      }
    } catch (error) {
      console.error('Failed to save settings:', error);
      alert('Failed to save settings');
    }
  };

  if (isLoading) {
    return (
      <div className="bg-slate-800 rounded-lg p-6">
        <h2 className="text-2xl font-bold mb-6">Mining Settings</h2>
        <div className="text-center py-8">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-emerald-400"></div>
          <p className="mt-2">Loading settings...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-slate-800 rounded-lg p-6">
      <h2 className="text-2xl font-bold mb-6">Mining Settings</h2>
      <form onSubmit={handleSubmit} className="space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="md:col-span-2">
            <h3 className="text-lg font-semibold mb-4">Wallet Configuration</h3>
            <div className="bg-slate-700 p-4 rounded-lg">
              <p className="text-sm text-gray-400 mb-2">Note: Wallet addresses are immutable and cannot be changed.</p>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium mb-2">Litecoin Wallet Address</label>
                  <div className="w-full bg-slate-600 border border-slate-500 rounded-md px-3 py-2 font-mono text-sm">
                    ltc1qpptg85asckrjy9ygygh2tfgxqwzn6672zmzq99
                  </div>
                </div>
                <div>
                  <label className="block text-sm font-medium mb-2">Dogecoin Wallet Address</label>
                  <div className="w-full bg-slate-600 border border-slate-500 rounded-md px-3 py-2 font-mono text-sm">
                    DGKsuHU6XdghZtA2aWGqvrZrkWracQJzPd
                  </div>
                </div>
              </div>
            </div>
          </div>
          
          <div className="md:col-span-2 mt-4">
            <h3 className="text-lg font-semibold mb-4">Worker Configuration</h3>
          </div>
          <div>
            <label className="block text-sm font-medium mb-2">Worker Name</label>
            <input
              type="text"
              name="workerName"
              value={settings.workerName}
              onChange={handleChange}
              className="w-full bg-slate-700 border border-slate-600 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-emerald-400"
            />
          </div>
          
          <div className="md:col-span-2 mt-4">
            <h3 className="text-lg font-semibold mb-4">Hardware & Economic Settings</h3>
          </div>
          <div>
            <label className="block text-sm font-medium mb-2">Max Temperature (°C)</label>
            <input
              type="number"
              name="maxTemperature"
              value={settings.maxTemperature}
              onChange={handleChange}
              className="w-full bg-slate-700 border border-slate-600 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-emerald-400"
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-2">Min Profit Margin (%)</label>
            <input
              type="number"
              name="minProfitMargin"
              value={settings.minProfitMargin}
              onChange={handleChange}
              step="0.1"
              className="w-full bg-slate-700 border border-slate-600 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-emerald-400"
            />
          </div>
        </div>
        <div className="flex justify-end">
          <button
            type="submit"
            className="px-6 py-3 bg-emerald-400 text-slate-950 font-medium rounded-md hover:bg-emerald-300 focus:outline-none focus:ring-2 focus:ring-emerald-400"
          >
            Save Settings
          </button>
        </div>
      </form>
    </div>
  );
};

export default SettingsPanel;
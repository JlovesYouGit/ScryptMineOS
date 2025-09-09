import { useState } from 'react';
import MiningDashboard from './components/MiningDashboard';
import SettingsPanel from './components/SettingsPanel';
import LogsViewer from './components/LogsViewer';

function App() {
  const [activeTab, setActiveTab] = useState<'dashboard' | 'settings' | 'logs'>('dashboard');

  return (
    <div className="min-h-screen bg-slate-950 text-white">
      <header className="border-b border-slate-800">
        <div className="container mx-auto px-4 py-4 flex justify-between items-center">
          <h1 className="text-2xl font-bold text-emerald-400">Mining OS</h1>
          <nav>
            <ul className="flex space-x-6">
              <li>
                <button 
                  onClick={() => setActiveTab('dashboard')}
                  className={`px-3 py-2 rounded-md ${activeTab === 'dashboard' ? 'bg-slate-800 text-emerald-400' : 'hover:bg-slate-800'}`}
                >
                  Dashboard
                </button>
              </li>
              <li>
                <button 
                  onClick={() => setActiveTab('settings')}
                  className={`px-3 py-2 rounded-md ${activeTab === 'settings' ? 'bg-slate-800 text-emerald-400' : 'hover:bg-slate-800'}`}
                >
                  Settings
                </button>
              </li>
              <li>
                <button 
                  onClick={() => setActiveTab('logs')}
                  className={`px-3 py-2 rounded-md ${activeTab === 'logs' ? 'bg-slate-800 text-emerald-400' : 'hover:bg-slate-800'}`}
                >
                  Logs
                </button>
              </li>
            </ul>
          </nav>
        </div>
      </header>

      <main className="container mx-auto px-4 py-8">
        {activeTab === 'dashboard' && <MiningDashboard />}
        {activeTab === 'settings' && <SettingsPanel />}
        {activeTab === 'logs' && <LogsViewer />}
      </main>
    </div>
  );
}

export default App;
import { useState, useEffect, useCallback } from "react";
import SignupForm from "./components/SignUpForm";
import StatsCards from "./components/StatsCards";
import ProviderChart from "./components/ProviderChart";
import HistoryTable from "./components/HistoryTable";
import Playground from "./components/Playground";
import { fetchStats, fetchHistory } from "./api";
import LandingPage from "./components/LandingPage";

export default function App() {
  const [apiKey, setApiKey] = useState(null);
  const [stats, setStats] = useState(null);
  const [history, setHistory] = useState([]);
  const [range, setRange] = useState("7d");
  const [started, setStarted] = useState(false);

  const loadData = useCallback(async () => {
    if (!apiKey) return;
    const [statsRes, historyRes] = await Promise.all([
      fetchStats(apiKey, range),
      fetchHistory(apiKey),
    ]);
    setStats(statsRes);
    setHistory(historyRes);
  }, [apiKey, range]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  if (!started) {
    return <LandingPage onGetStarted={() => setStarted(true)} />;
  }

  if (!apiKey) {
    return <SignupForm onSignedUp={setApiKey} />;
  }

  return (
    <div className="max-w-4xl mx-auto p-6">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-xl font-bold">LLM Gateway Dashboard</h1>
        <select
          value={range}
          onChange={(e) => setRange(e.target.value)}
          className="border rounded px-3 py-1 text-sm"
        >
          <option value="24h">Last 24h</option>
          <option value="7d">Last 7 days</option>
          <option value="30d">Last 30 days</option>
        </select>
      </div>

      <StatsCards stats={stats} />
      <ProviderChart stats={stats} />
      <HistoryTable history={history} />
      <Playground apiKey={apiKey} onRequestComplete={loadData} />
    </div>
  );
}
import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer } from "recharts";

const COLORS = ["#4f46e5", "#16a34a", "#ea580c", "#64748b"];

export default function ProviderChart({ stats }) {
  if (!stats || Object.keys(stats.provider_breakdown).length === 0) {
    return <p className="text-sm text-gray-500 mb-6">No requests yet.</p>;
  }

  const data = Object.entries(stats.provider_breakdown).map(([provider, count]) => ({
    name: provider,
    value: count,
  }));

  return (
    <div className="border rounded-lg p-4 mb-6" style={{ height: 250 }}>
      <p className="text-sm text-gray-500 mb-2">Provider Breakdown</p>
      <ResponsiveContainer width="100%" height="100%">
        <PieChart>
          <Pie data={data} dataKey="value" nameKey="name" outerRadius={80} label>
            {data.map((_, i) => (
              <Cell key={i} fill={COLORS[i % COLORS.length]} />
            ))}
          </Pie>
          <Tooltip />
        </PieChart>
      </ResponsiveContainer>
    </div>
  );
}
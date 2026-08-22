export default function StatsCards({ stats }) {
  if (!stats) return null;

  const cards = [
    { label: "Total Requests", value: stats.total_requests },
    { label: "Total Cost", value: `$${stats.total_cost.toFixed(4)}` },
    { label: "Cache Hit Rate", value: `${stats.cache_hit_rate}%` },
    { label: "Avg Latency", value: `${stats.avg_latency_ms} ms` },
  ];

  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
      {cards.map((c) => (
        <div key={c.label} className="border rounded-lg p-4">
          <p className="text-sm text-gray-500">{c.label}</p>
          <p className="text-2xl font-semibold">{c.value}</p>
        </div>
      ))}
    </div>
  );
}
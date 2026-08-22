export default function HistoryTable({ history }) {
  if (history.length === 0) {
    return <p className="text-sm text-gray-500 mb-6">No requests yet.</p>;
  }

  return (
    <div className="border rounded-lg overflow-x-auto mb-6">
      <table className="w-full text-sm">
        <thead className="bg-gray-50 text-left">
          <tr>
            <th className="p-2">Model</th>
            <th className="p-2">Provider</th>
            <th className="p-2">Cache Hit</th>
            <th className="p-2">Latency</th>
            <th className="p-2">Cost</th>
            <th className="p-2">Time</th>
          </tr>
        </thead>
        <tbody>
          {history.map((row) => (
            <tr key={row.id} className="border-t">
              <td className="p-2">{row.model}</td>
              <td className="p-2">{row.provider}</td>
              <td className="p-2">{row.cache_hit ? "Yes" : "No"}</td>
              <td className="p-2">{row.latency_ms} ms</td>
              <td className="p-2">${row.cost.toFixed(4)}</td>
              <td className="p-2">{new Date(row.created_at).toLocaleTimeString()}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
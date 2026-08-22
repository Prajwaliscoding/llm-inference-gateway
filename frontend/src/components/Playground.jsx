import { useState } from "react";
import { sendChatCompletion } from "../api";

export default function Playground({ apiKey, onRequestComplete }) {
  const [model, setModel] = useState("auto");
  const [message, setMessage] = useState("");
  const [response, setResponse] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    setResponse(null);
    try {
      const res = await sendChatCompletion(apiKey, {
        model,
        messages: [{ role: "user", content: message }],
      });
      setResponse(res);
      onRequestComplete();
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="border rounded-lg p-4">
      <p className="text-sm text-gray-500 mb-3">Playground</p>
      <form onSubmit={handleSubmit} className="space-y-3">
        <select
          value={model}
          onChange={(e) => setModel(e.target.value)}
          className="border rounded px-3 py-2 w-full"
        >
          <option value="auto">auto</option>
          <option value="gpt-4o-mini">gpt-4o-mini</option>
          <option value="gpt-4o">gpt-4o</option>
          <option value="claude-3-5-sonnet-latest">claude-3-5-sonnet</option>
        </select>
        <textarea
          required
          placeholder="Type a message..."
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          className="w-full border rounded px-3 py-2"
          rows={3}
        />
        <button
          type="submit"
          disabled={loading}
          className="bg-black text-white px-4 py-2 rounded hover:bg-gray-800 disabled:opacity-50"
        >
          {loading ? "Sending..." : "Send"}
        </button>
      </form>

      {error && <p className="text-red-600 text-sm mt-3">{error}</p>}

      {response && (
        <pre className="bg-gray-100 rounded p-3 mt-4 text-xs overflow-x-auto">
          {JSON.stringify(response, null, 2)}
        </pre>
      )}
    </div>
  );
}
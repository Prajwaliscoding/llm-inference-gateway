import { useState } from "react";
import { signup } from "../api";

export default function SignupForm({ onSignedUp }) {
  const [email, setEmail] = useState("");
  const [key, setKey] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const res = await signup(email);
      setKey(res.api_key);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  function copyAndContinue() {
    navigator.clipboard.writeText(key);
    onSignedUp(key);
  }

  if (key) {
    return (
      <div className="max-w-md mx-auto mt-20 p-6 border rounded-lg">
        <h2 className="text-lg font-semibold mb-2">Your API Key</h2>
        <p className="text-sm text-gray-500 mb-4">Save this now — it won't be shown again.</p>
        <code className="block bg-gray-100 p-3 rounded text-sm break-all mb-4">{key}</code>
        <button
          onClick={copyAndContinue}
          className="w-full bg-black text-white py-2 rounded hover:bg-gray-800"
        >
          Copy & Continue to Dashboard
        </button>
      </div>
    );
  }

  return (
    <div className="max-w-md mx-auto mt-20 p-6 border rounded-lg">
      <h2 className="text-lg font-semibold mb-4">Get your API key</h2>
      <form onSubmit={handleSubmit}>
        <input
          type="email"
          required
          placeholder="you@example.com"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          className="w-full border rounded px-3 py-2 mb-3"
        />
        {error && <p className="text-red-600 text-sm mb-3">{error}</p>}
        <button
          type="submit"
          disabled={loading}
          className="w-full bg-black text-white py-2 rounded hover:bg-gray-800 disabled:opacity-50"
        >
          {loading ? "Creating key..." : "Sign Up"}
        </button>
      </form>
    </div>
  );
}
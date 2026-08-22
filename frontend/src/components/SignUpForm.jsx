import { useState } from "react";
import { signup } from "../api";

export default function SignupForm({ onSignedUp }) {
  const [email, setEmail] = useState("");
  const [key, setKey] = useState(null);
  const [error, setError] = useState(null);
  const [isNetworkError, setIsNetworkError] = useState(false);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    setError(null);
    setIsNetworkError(false);
    setLoading(true);
    try {
      const res = await signup(email);
      setKey(res.api_key);
    } catch (err) {
      if (err.message === "Failed to fetch") {
        setIsNetworkError(true);
        setError(
          "The backend isn't running right now. This is a demo project I spin up on demand to control AWS costs. Check the code on GitHub instead."
        );
      } else {
        setError(err.message);
      }
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
    <div className="max-w-md mx-auto mt-20">
      <div className="p-6 border rounded-lg">
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
          {error && (
            <div className="mb-3">
              <p className="text-red-600 text-sm">{error}</p>
              {isNetworkError && (
                
                 <a href="https://github.com/Prajwaliscoding/llm-inference-gateway"
                  target="_blank"
                  rel="noreferrer"
                  className="text-sm text-blue-600 underline"
                >
                  View source on GitHub
                </a>
              )}
            </div>
          )}
          <button
            type="submit"
            disabled={loading}
            className="w-full bg-black text-white py-2 rounded hover:bg-gray-800 disabled:opacity-50"
          >
            {loading ? "Creating key..." : "Sign Up"}
          </button>
        </form>
      </div>

      {isNetworkError && (
        <div className="mt-4 p-4 bg-amber-50 border border-amber-200 rounded-lg text-sm text-amber-800">
          <p className="font-medium mb-1">Backend offline</p>
          <p>
            I don't run this gateway's AWS infrastructure continuously to
            control costs. The code, architecture, and a full demo video
            are on GitHub if you want to see it in action.
          </p>
        </div>
      )}

      <div className="mt-4 p-4 bg-gray-50 border rounded-lg text-sm text-gray-600">
        <p className="font-medium text-gray-700 mb-1">Note on auth</p>
        <p>
          One thing to know: the API key here is real and gets checked on every
          request. What I skipped is checking the email. You can type anything
          and still get a working key. I did that on purpose so sign up stays
          one step for the demo.
        </p>
        <p className="mt-2">
          Real accounts with email verification and
          login sessions are my next upgrade
        </p>
      </div>
    </div>
  );
}
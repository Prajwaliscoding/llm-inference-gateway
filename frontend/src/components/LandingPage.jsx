export default function LandingPage({ onGetStarted }) {
  return (
    <div className="max-w-2xl mx-auto mt-20 px-6 text-center">
      <h1 className="text-3xl font-bold mb-4">LLM Inference Gateway</h1>
        <p className="text-gray-600 mb-8">
          I built this to route LLM requests across OpenAI and Anthropic with real
          failover, caching, and per-request cost tracking. If one provider goes
          down, the gateway catches it and reroutes automatically.
        </p>

      <div className="border rounded-lg p-6 mb-8 bg-gray-50">
        <p className="text-sm text-gray-500 mb-2">Architecture</p>
        <img
          src="/architecture-diagram.png"
          alt="Gateway architecture diagram"
          className="w-full rounded"
        />
      </div>

      <div className="flex justify-center gap-4">
        <button
          onClick={onGetStarted}
          className="bg-black text-white px-6 py-2 rounded hover:bg-gray-800"
        >
          Get Started
        </button>

          <a href="https://github.com/Prajwaliscoding/llm-inference-gateway"
          target="_blank"
          rel="noreferrer"
          className="border px-6 py-2 rounded hover:bg-gray-100"
        >
          View on GitHub
        </a>
      </div>
    </div>
  );
}
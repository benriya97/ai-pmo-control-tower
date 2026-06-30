import { useState, useEffect } from "react";

function App() {
  // One "box" per piece of data we're fetching from the backend.
  const [healthScore, setHealthScore] = useState(null);
  const [risks, setRisks] = useState(null);
  const [advisor, setAdvisor] = useState(null);
  const [dependencies,setDependencies] = useState(null);

  // Fetch health score — same as before.
  useEffect(() => {
    fetch("http://127.0.0.1:8000/health")
      .then((response) => response.json())
      .then((data) => setHealthScore(data.health_score))
      .catch((error) => console.error("Error fetching health score:", error));
  }, []);

  // Fetch risks — same pattern, different endpoint.
  // Note: /risks returns a plain list, e.g. ["Tasks are delayed", "Resources are overloaded"]
  useEffect(() => {
    fetch("http://127.0.0.1:8000/risks")
      .then((response) => response.json())
      .then((data) => setRisks(data))
      .catch((error) => console.error("Error fetching risks:", error));
  }, []);

  // Fetch the AI advisor recommendation — this one takes longer since it calls Ollama,
  // so expect "Loading..." to show for a few seconds before it appears.
  useEffect(() => {
    fetch("http://127.0.0.1:8000/advisor")
      .then((response) => response.json())
      .then((data) => setAdvisor(data.recommendation))
      .catch((error) => console.error("Error fetching advisor:", error));
  }, []);

  useEffect(() => {
  fetch("http://127.0.0.1:8000/dependencies")
    .then((response) => response.json())
    .then((data) => setDependencies(data.blocked_tasks))
    .catch((error) => console.error("Error fetching dependencies:", error));
  }, []);

  return (
    <div style={{ padding: "40px", fontFamily: "sans-serif", maxWidth: "700px" }}>
      <h1>AI PMO Control Tower</h1>

      <h2>Project Health Score</h2>
      <p>{healthScore === null ? "Loading..." : `${healthScore}/100`}</p>

      <h2>Risks</h2>
      {risks === null ? (
        <p>Loading...</p>
      ) : risks.length === 0 ? (
        <p>No risks detected.</p>
      ) : (
        <ul>
          {/* .map() turns each item in the risks list into its own <li> bullet point.
              "key" is something React requires for lists, to track each item individually. */}
          {risks.map((risk, index) => (
            <li key={index}>{risk}</li>
          ))}
        </ul>
      )}

      <h2>AI Advisor Recommendation</h2>
      {/* whiteSpace: "pre-wrap" makes the \n line breaks in the AI's text actually show as line breaks */}
      <p style={{ whiteSpace: "pre-wrap" }}>
        {advisor === null ? "Loading... (this may take a few seconds)" : advisor}
      </p>

      <h2>Dependencies</h2>
        {dependencies === null ? (
          <p>Loading...</p>
        ) : dependencies.length === 0 ? (
          <p>No blocked tasks.</p>
        ) : (
          <ul>
            {dependencies.map((dep) => (
              <li key={dep.task_id}>
                <strong>{dep.task_name}</strong> is blocked by{" "}
                <strong>{dep.blocked_by}</strong> ({dep.blocked_by_progress}% complete)
              </li>
            ))}
          </ul>
        )}

    </div>
  );
}

export default App;
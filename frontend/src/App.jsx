import { useState, useEffect } from "react";

function App() {
  const [healthScore, setHealthScore] = useState(null);
  const [risks, setRisks] = useState(null);
  const [advisor, setAdvisor] = useState(null);
  const [dependencies, setDependencies] = useState(null);

  // NEW — holds what you type into the update inputs.
  // We track which task id and what new progress value.
  const [taskId, setTaskId] = useState("");
  const [newProgress, setNewProgress] = useState("");
  const [updateMsg, setUpdateMsg] = useState("");  // feedback after an update

  // --- Fetch functions pulled OUT of useEffect so we can call them again later ---
  // (Before, these lived inside useEffect and only ran once. Now they're reusable.)
  const fetchHealth = () => {
    fetch("http://127.0.0.1:8000/health")
      .then((r) => r.json())
      .then((data) => setHealthScore(data.health_score))
      .catch((e) => console.error("health:", e));
  };

  const fetchRisks = () => {
    fetch("http://127.0.0.1:8000/risks")
      .then((r) => r.json())
      .then((data) => setRisks(data))
      .catch((e) => console.error("risks:", e));
  };

  const fetchDependencies = () => {
    fetch("http://127.0.0.1:8000/dependencies")
      .then((r) => r.json())
      .then((data) => setDependencies(data.blocked_tasks))
      .catch((e) => console.error("dependencies:", e));
  };

  // Advisor is slow (Ollama), so we keep it separate and don't auto-refresh it on every update.
  const fetchAdvisor = () => {
    setAdvisor(null);  // show "Loading..." while it regenerates
    fetch("http://127.0.0.1:8000/advisor")
      .then((r) => r.json())
      .then((data) => setAdvisor(data.recommendation))
      .catch((e) => console.error("advisor:", e));
  };

  // --- Run all fetches once on page load ---
  useEffect(() => {
    fetchHealth();
    fetchRisks();
    fetchDependencies();
    fetchAdvisor();
  }, []);

  // --- NEW: send a POST to update a task's progress, then refresh the display ---
  const handleUpdateProgress = () => {
    // Basic guard: don't send if fields are empty.
    if (taskId === "" || newProgress === "") {
      setUpdateMsg("Enter both a task ID and a progress value.");
      return;
    }

    fetch("http://127.0.0.1:8000/tasks/update-progress", {
      method: "POST",                                    // POST, not GET — we're sending data
      headers: { "Content-Type": "application/json" },   // tell the server it's JSON
      body: JSON.stringify({                             // convert our data to a JSON string
        task_id: parseInt(taskId),                       // parseInt: input values are strings, backend wants ints
        progress: parseInt(newProgress),
      }),
    })
      .then((r) => r.json())
      .then((data) => {
        setUpdateMsg(data.message);   // show the backend's success/failure message
        // Refresh the numbers that this change affects:
        fetchHealth();
        fetchRisks();
        fetchDependencies();
        // (advisor not auto-refreshed — click the button below to regenerate it)
      })
      .catch((e) => {
        console.error("update:", e);
        setUpdateMsg("Update failed — is the backend running?");
      });
  };

  return (
    <div style={{ padding: "40px", fontFamily: "sans-serif", maxWidth: "700px" }}>
      <h1>AI PMO Control Tower</h1>

      <h2>Project Health Score</h2>
      <p style={{ fontSize: "24px", fontWeight: "bold" }}>
        {healthScore === null ? "Loading..." : `${healthScore}/100`}
      </p>

      {/* NEW — update controls */}
      <div style={{ background: "#f4f4f4", padding: "16px", borderRadius: "8px", margin: "16px 0" }}>
        <h3>Update Task Progress</h3>
        <input
          type="number"
          placeholder="Task ID"
          value={taskId}
          onChange={(e) => setTaskId(e.target.value)}   // onChange keeps state in sync with input
          style={{ marginRight: "8px", padding: "6px", width: "100px" }}
        />
        <input
          type="number"
          placeholder="Progress (0-100)"
          value={newProgress}
          onChange={(e) => setNewProgress(e.target.value)}
          style={{ marginRight: "8px", padding: "6px", width: "140px" }}
        />
        <button onClick={handleUpdateProgress} style={{ padding: "6px 16px", cursor: "pointer" }}>
          Update
        </button>
        {updateMsg && <p style={{ marginTop: "8px", color: "#333" }}>{updateMsg}</p>}
      </div>

      <h2>Risks</h2>
      {risks === null ? (
        <p>Loading...</p>
      ) : risks.length === 0 ? (
        <p>No risks detected.</p>
      ) : (
        <ul>
          {risks.map((risk, index) => (
            <li key={index}>{risk}</li>
          ))}
        </ul>
      )}

      <h2>AI Advisor Recommendation</h2>
      <button onClick={fetchAdvisor} style={{ padding: "6px 16px", cursor: "pointer", marginBottom: "8px" }}>
        Regenerate Advice
      </button>
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
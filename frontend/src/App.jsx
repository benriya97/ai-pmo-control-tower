import { useState, useEffect } from "react";

function App() {
  // "healthScore" holds the value we get back from the backend.
  // useState(null) means it starts as "nothing yet" until the fetch completes.
  const [healthScore, setHealthScore] = useState(null);

  // useEffect runs code automatically when the component loads on screen.
  // The empty array [] at the end means "only run this once, when the page first loads."
  useEffect(() => {
    fetch("http://127.0.0.1:8000/health")
      .then((response) => response.json())   // convert the raw response into JSON
      .then((data) => setHealthScore(data.health_score))  // store the number we got
      .catch((error) => console.error("Error fetching health score:", error));
  }, []);

  return (
    <div style={{ padding: "40px", fontFamily: "sans-serif" }}>
      <h1>AI PMO Control Tower</h1>
      <h2>Project Health Score</h2>
      {/* While healthScore is still null, show "Loading...". Once it arrives, show the number. */}
      <p>{healthScore === null ? "Loading..." : `${healthScore}/100`}</p>
    </div>
  );
}

export default App;
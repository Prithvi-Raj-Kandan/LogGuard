import FileUpload from "./components/FileUpload";
import LogViewer from "./components/LogViewer";
import InsightsPanel from "./components/InsightsPanel";

const demoFindings = [];

function App() {
  return (
    <main style={{ fontFamily: "Segoe UI, sans-serif", margin: "2rem" }}>
      <h1>LogGuard LG-101 Scaffold</h1>
      <p>Phase 1 foundation UI is ready. Analysis integration starts in LG-108.</p>
      <FileUpload />
      <LogViewer logText="No logs loaded yet." findings={demoFindings} />
      <InsightsPanel insights={["Insights panel scaffold initialized."]} />
    </main>
  );
}

export default App;

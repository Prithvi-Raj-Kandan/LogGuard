function LogViewer({ logText, findings }) {
  return (
    <section>
      <h2>Log Viewer</h2>
      <pre style={{ background: "#f6f8fa", padding: "1rem", borderRadius: "8px" }}>
        {logText}
      </pre>
      <p>Findings in current view: {findings.length}</p>
    </section>
  );
}

export default LogViewer;

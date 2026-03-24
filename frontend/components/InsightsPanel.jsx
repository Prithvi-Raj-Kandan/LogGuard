function InsightsPanel({ insights }) {
  return (
    <section>
      <h2>Insights Panel</h2>
      <ul>
        {insights.map((insight) => (
          <li key={insight}>{insight}</li>
        ))}
      </ul>
    </section>
  );
}

export default InsightsPanel;

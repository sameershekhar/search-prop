import ResultsCard from './ResultsCard';
import StatusMessage from './StatusMessage';

function ResultsList({ results, totalResults }) {
  if (results.length === 0) {
    return <StatusMessage type="empty" />;
  }

  return (
    <section className="results-list">
      <p className="results-list__count">Search Results ({totalResults})</p>
      {results.map((listing) => (
        <ResultsCard key={listing.id} listing={listing} />
      ))}
    </section>
  );
}

export default ResultsList;

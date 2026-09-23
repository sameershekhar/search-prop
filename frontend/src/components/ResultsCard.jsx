import { formatCurrency, formatSqft, formatDate, formatRelevanceScore } from '../utils/format';

function ResultsCard({ listing }) {
  return (
    <article className="results-card">
      <header className="results-card__primary">
        <h3 className="results-card__address">{listing.address}</h3>
        <span className="results-card__price">{formatCurrency(listing.price)}</span>
        <span className="results-card__location">
          {listing.city}, {listing.state} {listing.zip}
        </span>
        <span className="results-card__score">
          Relevance score: {formatRelevanceScore(listing.score)}
        </span>
      </header>

      <section className="results-card__secondary">
        <span>🛏 {listing.bedrooms} Bedrooms</span>
        <span>🛁 {listing.bathrooms} Bathrooms</span>
        <span>📐 {formatSqft(listing.sqft)}</span>
        <span className="results-card__status">{listing.status}</span>
        <span>Listed: {formatDate(listing.listedDate)}</span>
      </section>

      <section className="results-card__meta">
        <span>ID: {listing.id}</span>
        <span>Source: {listing.source}</span>
        <span>
          Location: {listing.latitude}, {listing.longitude}
        </span>
      </section>

      <p className="results-card__description">{listing.description}</p>
    </article>
  );
}

export default ResultsCard;

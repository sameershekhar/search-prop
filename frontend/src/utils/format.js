export function formatCurrency(price) {
  if (typeof price !== 'number' || Number.isNaN(price)) return '—';
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    maximumFractionDigits: 0,
  }).format(price);
}

export function formatSqft(sqft) {
  if (typeof sqft !== 'number' || Number.isNaN(sqft)) return '—';
  return `${new Intl.NumberFormat('en-US').format(sqft)} sqft`;
}

export function formatDate(isoDateString) {
  const d = new Date(isoDateString);
  if (Number.isNaN(d.getTime())) return isoDateString;
  return new Intl.DateTimeFormat('en-US', {
    year: 'numeric',
    month: 'short',
    day: '2-digit',
  }).format(d);
}

export function formatRelevanceScore(score) {
  return typeof score === 'number' ? score.toFixed(2) : '—';
}

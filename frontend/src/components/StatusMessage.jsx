function StatusMessage({ type, message }) {
  if (type === 'loading') {
    return (
      <p className="status-message status-message--loading" role="status">
        Searching listings...
      </p>
    );
  }

  if (type === 'error') {
    return (
      <p className="status-message status-message--error" role="alert">
        {message}
      </p>
    );
  }

  if (type === 'empty') {
    return (
      <p className="status-message status-message--empty" role="status">
        No listings found matching your criteria.
      </p>
    );
  }

  return null;
}

export default StatusMessage;

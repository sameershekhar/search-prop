import { useState } from 'react';
import { searchListings } from './api/searchClient';
import SearchForm from './components/SearchForm';
import ResultsList from './components/ResultsList';
import Pagination from './components/Pagination';
import StatusMessage from './components/StatusMessage';

const DEFAULT_PAGE_META = { page: 1, pageSize: 10, totalResults: 0, totalPages: 1 };

function App() {
  const [filters, setFilters] = useState(null);
  const [page, setPage] = useState(1);
  const [status, setStatus] = useState('idle');
  const [results, setResults] = useState([]);
  const [pageMeta, setPageMeta] = useState(DEFAULT_PAGE_META);
  const [errorMessage, setErrorMessage] = useState(null);

  async function runSearch(searchFilters, targetPage) {
    setStatus('loading');
    setErrorMessage(null);
    try {
      const data = await searchListings({ ...searchFilters, page: targetPage });
      setResults(data.results);
      setPageMeta({
        page: data.page,
        pageSize: data.pageSize,
        totalResults: data.totalResults,
        totalPages: data.totalPages,
      });
      setPage(data.page);
      setStatus('success');
    } catch (err) {
      setErrorMessage(err.message || 'Something went wrong.');
      setResults([]);
      setStatus('error');
    }
  }

  function handleSearchSubmit(newFilters) {
    setFilters(newFilters);
    setPage(1);
    runSearch(newFilters, 1);
  }

  function handlePageChange(newPage) {
    runSearch(filters, newPage);
  }

  const isLoading = status === 'loading';

  return (
    <div className="app-shell">
      <h1 className="app-title">Listing Search Service</h1>

      <SearchForm onSubmit={handleSearchSubmit} disabled={isLoading} />

      {status === 'loading' && <StatusMessage type="loading" />}
      {status === 'error' && <StatusMessage type="error" message={errorMessage} />}

      {status === 'success' && (
        <>
          <ResultsList results={results} totalResults={pageMeta.totalResults} />
          {results.length > 0 && (
            <Pagination
              page={pageMeta.page}
              totalPages={pageMeta.totalPages}
              onPageChange={handlePageChange}
              disabled={isLoading}
            />
          )}
        </>
      )}
    </div>
  );
}

export default App;

import { useState } from 'react';

const EMPTY_DRAFT = {
  minPrice: '',
  maxPrice: '',
  minBedrooms: '',
  city: '',
  keyword: '',
  targetBudget: '',
  pageSize: 10,
};

const NUMERIC_FIELDS = ['minPrice', 'maxPrice', 'minBedrooms', 'targetBudget', 'pageSize'];
const INTEGER_FIELDS = ['minBedrooms', 'pageSize'];

function validate(draft) {
  const errors = {};

  for (const key of NUMERIC_FIELDS) {
    const value = draft[key];
    if (value === '' || value === undefined || value === null) continue;

    if (!Number.isFinite(Number(value))) {
      errors[key] = 'Must be a number.';
      continue;
    }

    if (INTEGER_FIELDS.includes(key) && (!Number.isInteger(Number(value)) || Number(value) < 0)) {
      errors[key] = 'Must be a non-negative whole number.';
    }
  }

  return errors;
}

function SearchForm({ onSubmit, disabled }) {
  const [draft, setDraft] = useState(EMPTY_DRAFT);
  const [errors, setErrors] = useState({});

  function handleChange(event) {
    const { name, value } = event.target;
    setDraft((prev) => ({ ...prev, [name]: value }));
  }

  function handleSubmit(event) {
    event.preventDefault();
    const validationErrors = validate(draft);
    setErrors(validationErrors);
    if (Object.keys(validationErrors).length > 0) return;
    onSubmit(draft);
  }

  function handleClear() {
    setDraft(EMPTY_DRAFT);
    setErrors({});
  }

  return (
    <form className="search-form" onSubmit={handleSubmit} noValidate>
      <h2 className="search-form__title">Search Filters</h2>
      <div className="search-form__grid">
        <div className="search-form__field">
          <label htmlFor="minPrice">Min Price</label>
          <input
            id="minPrice"
            name="minPrice"
            type="text"
            inputMode="decimal"
            value={draft.minPrice}
            onChange={handleChange}
          />
          {errors.minPrice && (
            <span className="search-form__error" role="alert">
              {errors.minPrice}
            </span>
          )}
        </div>

        <div className="search-form__field">
          <label htmlFor="maxPrice">Max Price</label>
          <input
            id="maxPrice"
            name="maxPrice"
            type="text"
            inputMode="decimal"
            value={draft.maxPrice}
            onChange={handleChange}
          />
          {errors.maxPrice && (
            <span className="search-form__error" role="alert">
              {errors.maxPrice}
            </span>
          )}
        </div>

        <div className="search-form__field">
          <label htmlFor="minBedrooms">Min Bedrooms</label>
          <input
            id="minBedrooms"
            name="minBedrooms"
            type="text"
            inputMode="numeric"
            value={draft.minBedrooms}
            onChange={handleChange}
          />
          {errors.minBedrooms && (
            <span className="search-form__error" role="alert">
              {errors.minBedrooms}
            </span>
          )}
        </div>

        <div className="search-form__field">
          <label htmlFor="city">City</label>
          <input id="city" name="city" type="text" value={draft.city} onChange={handleChange} />
        </div>

        <div className="search-form__field">
          <label htmlFor="keyword">Keyword</label>
          <input
            id="keyword"
            name="keyword"
            type="text"
            value={draft.keyword}
            onChange={handleChange}
          />
        </div>

        <div className="search-form__field">
          <label htmlFor="targetBudget">Target Budget</label>
          <input
            id="targetBudget"
            name="targetBudget"
            type="text"
            inputMode="decimal"
            value={draft.targetBudget}
            onChange={handleChange}
          />
          {errors.targetBudget && (
            <span className="search-form__error" role="alert">
              {errors.targetBudget}
            </span>
          )}
        </div>

        <div className="search-form__field">
          <label htmlFor="pageSize">Page Size</label>
          <input
            id="pageSize"
            name="pageSize"
            type="text"
            inputMode="numeric"
            value={draft.pageSize}
            onChange={handleChange}
          />
          {errors.pageSize && (
            <span className="search-form__error" role="alert">
              {errors.pageSize}
            </span>
          )}
        </div>
      </div>

      <div className="search-form__actions">
        <button type="submit" disabled={disabled}>
          Search
        </button>
        <button type="button" onClick={handleClear} disabled={disabled}>
          Clear filters
        </button>
      </div>
    </form>
  );
}

export default SearchForm;

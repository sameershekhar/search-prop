const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

const NUMERIC_FIELDS = ['minPrice', 'maxPrice', 'minBedrooms', 'targetBudget', 'page', 'pageSize'];
const STRING_FIELDS = ['city', 'keyword'];

function isEmpty(value) {
  return value === '' || value === undefined || value === null;
}

function buildQueryParams(filters) {
  const params = new URLSearchParams();

  for (const key of NUMERIC_FIELDS) {
    const value = filters[key];
    if (isEmpty(value)) continue;
    params.set(key, String(Number(value)));
  }

  for (const key of STRING_FIELDS) {
    const value = filters[key];
    if (isEmpty(value)) continue;
    params.set(key, String(value).trim());
  }

  return params;
}

function normalizeErrorBody(body, status) {
  // 400 business-rule error shape: { error, field }
  if (typeof body?.error === 'string') {
    return { message: body.error, field: body.field ?? null };
  }

  // 422 Pydantic validation error shape: { detail: [{ type, loc, msg, input }, ...] }
  if (Array.isArray(body?.detail) && body.detail.length > 0) {
    const first = body.detail[0];
    const field = Array.isArray(first.loc) ? first.loc[first.loc.length - 1] : null;
    return { message: first.msg || 'Invalid search parameters.', field };
  }

  return { message: `Request failed with status ${status}.`, field: null };
}

function normalizeNetworkError() {
  return {
    message: 'Unable to reach the server. Please check your connection and try again.',
    field: null,
  };
}

export async function searchListings(filters) {
  const params = buildQueryParams(filters);
  const url = `${API_BASE_URL}/api/listings/search?${params.toString()}`;

  let response;
  try {
    response = await fetch(url, { method: 'GET' });
  } catch (networkError) {
    throw normalizeNetworkError(networkError);
  }

  let body;
  try {
    body = await response.json();
  } catch (parseError) {
    throw { message: 'Received an unexpected response from the server.', field: null };
  }

  if (!response.ok) {
    throw normalizeErrorBody(body, response.status);
  }

  return body;
}

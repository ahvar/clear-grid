import React, { useEffect, useMemo, useState } from 'react';
import { createRoot } from 'react-dom/client';

const PAGE_SIZE = 10;
const columns = [
  ['delivery_start_utc', 'Delivery Start', true],
  ['auction_unit', 'Unit', true],
  ['auction_product', 'Product', true],
  ['executed_quantity_mw', 'MW', true],
  ['clearing_price_gbp_per_mw_h', 'Price', true],
  ['technology_type', 'Technology', false],
  ['post_code', 'Postcode', false],
];

function formatValue(key, value) {
  if (key === 'delivery_start_utc') return new Date(value).toLocaleString();
  if (key === 'executed_quantity_mw') return Number(value).toFixed(3);
  if (key === 'clearing_price_gbp_per_mw_h') return `£${Number(value).toFixed(2)}`;
  return value || '';
}

function App() {
  const [rows, setRows] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(0);
  const [search, setSearch] = useState('');
  const [sort, setSort] = useState({ key: 'delivery_start_utc', direction: '+' });

  const query = useMemo(() => {
    const params = new URLSearchParams({
      start: String(page * PAGE_SIZE),
      length: String(PAGE_SIZE),
      sort: `${sort.direction}${sort.key}`,
    });
    if (search.trim()) params.set('search', search.trim());
    return params.toString();
  }, [page, search, sort]);

  useEffect(() => {
    fetch(`/api/daily-auction-results?${query}`)
      .then((response) => response.json())
      .then((payload) => {
        setRows(payload.data || []);
        setTotal(payload.total || 0);
      });
  }, [query]);

  function updateSort(key) {
    setPage(0);
    setSort((current) => ({
      key,
      direction: current.key === key && current.direction === '+' ? '-' : '+',
    }));
  }

  const lastPage = Math.max(0, Math.ceil(total / PAGE_SIZE) - 1);

  return (
    <main>
      <h1>Auction Unit Results</h1>
      <input
        aria-label="Search results"
        placeholder="Search"
        value={search}
        onChange={(event) => {
          setPage(0);
          setSearch(event.target.value);
        }}
      />
      <table>
        <thead>
          <tr>
            {columns.map(([key, label, sortable]) => (
              <th key={key}>
                {sortable ? (
                  <button type="button" onClick={() => updateSort(key)}>
                    {label}
                    {sort.key === key ? ` ${sort.direction}` : ''}
                  </button>
                ) : (
                  label
                )}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row.id}>
              {columns.map(([key]) => (
                <td key={key}>{formatValue(key, row[key])}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
      <nav>
        <button type="button" disabled={page === 0} onClick={() => setPage(page - 1)}>
          Previous
        </button>
        <span>
          Page {page + 1} of {lastPage + 1}
        </span>
        <button
          type="button"
          disabled={page >= lastPage}
          onClick={() => setPage(page + 1)}
        >
          Next
        </button>
      </nav>
    </main>
  );
}

createRoot(document.getElementById('root')).render(<App />);

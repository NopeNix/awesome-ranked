import React, { useEffect, useMemo, useState } from 'react'
import { useReactTable, getCoreRowModel, flexRender } from '@tanstack/react-table'
import { type ColumnDef } from '@tanstack/react-table'

type RepoLatestSnapshot = {
  repository_id: number
  owner: string
  name: string
  html_url: string
  repo_created_at: string | null
  github_default_branch: string | null
  stars: number
  forks: number
  watchers: number
  contributors_count_approx: number | null
  contributors_sample_size: number | null
  commit_count_default_branch: number | null
  last_commit_date: string | null
  last_commit_sha: string | null
}

type RepoListResponse = {
  total: number
  items: RepoLatestSnapshot[]
}

const API_URL = import.meta.env.VITE_API_URL as string

type SortKey =
  | 'stars'
  | 'forks'
  | 'watchers'
  | 'contributors'
  | 'commits'
  | 'last_commit'
  | 'created'

const SORT_KEYS: SortKey[] = ['stars', 'forks', 'watchers', 'contributors', 'commits', 'last_commit', 'created']

function formatMaybeDate(v: string | null | undefined) {
  if (!v) return '—'
  const d = new Date(v)
  if (Number.isNaN(d.getTime())) return '—'
  return d.toISOString().slice(0, 10)
}

function formatNumber(v: number | null | undefined) {
  if (v === null || v === undefined) return '—'
  return new Intl.NumberFormat().format(v)
}

export default function App() {
  const [sortBy, setSortBy] = useState<SortKey>('stars')
  const [order, setOrder] = useState<'asc' | 'desc'>('desc')
  const [limit] = useState(50)
  const [offset, setOffset] = useState(0)
  const [data, setData] = useState<RepoListResponse | null>(null)
  const [loading, setLoading] = useState(false)

  const sortParam = useMemo(() => {
    switch (sortBy) {
      case 'contributors':
        return 'contributors'
      case 'commits':
        return 'commits'
      case 'last_commit':
        return 'last_commit'
      default:
        return sortBy
    }
  }, [sortBy])

  useEffect(() => {
    const controller = new AbortController()
    async function load() {
      setLoading(true)
      try {
        const url = new URL(`${API_URL}/api/repos`)
        url.searchParams.set('sortBy', sortParam)
        url.searchParams.set('order', order)
        url.searchParams.set('limit', String(limit))
        url.searchParams.set('offset', String(offset))
        const res = await fetch(url.toString(), { signal: controller.signal })
        if (!res.ok) throw new Error(`HTTP ${res.status}`)
        const json = (await res.json()) as RepoListResponse
        setData(json)
      } finally {
        setLoading(false)
      }
    }
    load()
    return () => controller.abort()
  }, [API_URL, sortParam, order, limit, offset])

  const columns = useMemo<ColumnDef<RepoLatestSnapshot>[]>(
    () => [
      {
        accessorKey: 'owner',
        header: 'Repo',
        cell: ({ row }) => {
          const r = row.original
          return (
            <div className="pill">
              <a href={r.html_url} target="_blank" rel="noreferrer">
                {r.owner}/{r.name}
              </a>
            </div>
          )
        },
      },
      {
        accessorKey: 'stars',
        header: () => renderSortHeader('stars', sortBy, order, setSortBy, setOrder),
        cell: ({ row }) => formatNumber(row.original.stars),
      },
      {
        accessorKey: 'forks',
        header: () => renderSortHeader('forks', sortBy, order, setSortBy, setOrder),
        cell: ({ row }) => formatNumber(row.original.forks),
      },
      {
        accessorKey: 'watchers',
        header: () => renderSortHeader('watchers', sortBy, order, setSortBy, setOrder),
        cell: ({ row }) => formatNumber(row.original.watchers),
      },
      {
        accessorKey: 'contributors_count_approx',
        header: () => renderSortHeader('contributors', sortBy, order, setSortBy, setOrder),
        cell: ({ row }) => formatNumber(row.original.contributors_count_approx),
      },
      {
        accessorKey: 'commit_count_default_branch',
        header: () => renderSortHeader('commits', sortBy, order, setSortBy, setOrder),
        cell: ({ row }) => formatNumber(row.original.commit_count_default_branch),
      },
      {
        accessorKey: 'last_commit_date',
        header: () => renderSortHeader('last_commit', sortBy, order, setSortBy, setOrder),
        cell: ({ row }) => formatMaybeDate(row.original.last_commit_date),
      },
      {
        accessorKey: 'repo_created_at',
        header: () => renderSortHeader('created', sortBy, order, setSortBy, setOrder),
        cell: ({ row }) => formatMaybeDate(row.original.repo_created_at),
      },
    ],
    [order, sortBy],
  )

  const table = useReactTable({
    data: data?.items ?? [],
    columns,
    getCoreRowModel: getCoreRowModel(),
  })

  const total = data?.total ?? 0
  const pageCount = Math.max(1, Math.ceil(total / limit))
  const page = Math.floor(offset / limit) + 1

  return (
    <div className="container">
      <div className="header">
        <div className="title">
          <h1>Awesome Selfhosted – Ranked</h1>
          <div className="sub">Latest GitHub metrics per repo with time-series snapshots in Postgres.</div>
        </div>

        <div className="toolbar">
          <div className="control">
            <label>Sort</label>
            <select
              value={sortBy}
              onChange={(e) => {
                setSortBy(e.target.value as SortKey)
                setOffset(0)
              }}
            >
              {SORT_KEYS.map((k) => (
                <option key={k} value={k}>
                  {k}
                </option>
              ))}
            </select>
          </div>

          <button
            className="btn"
            onClick={() => {
              setOrder((v) => (v === 'asc' ? 'desc' : 'asc'))
              setOffset(0)
            }}
          >
            {order.toUpperCase()}
          </button>

          <button
            className="btn"
            disabled={loading || page <= 1}
            onClick={() => setOffset((o) => Math.max(0, o - limit))}
          >
            Prev
          </button>
          <button
            className="btn"
            disabled={loading || page >= pageCount}
            onClick={() => setOffset((o) => o + limit)}
          >
            Next
          </button>
        </div>
      </div>

      <div className="tableWrap" aria-busy={loading}>
        <table>
          <thead>
            {table.getHeaderGroups().map((hg) => (
              <tr key={hg.id}>
                {hg.headers.map((header) => (
                  <th key={header.id}>
                    {header.isPlaceholder ? null : flexRender(header.column.columnDef.header, header.getContext())}
                  </th>
                ))}
              </tr>
            ))}
          </thead>
          <tbody>
            {table.getRowModel().rows.length === 0 ? (
              <tr>
                <td colSpan={8} className="mono" style={{ padding: 18 }}>
                  {loading ? 'Loading…' : 'No data yet. Run the API scraper container once.'}
                </td>
              </tr>
            ) : (
              table.getRowModel().rows.map((row) => (
                <tr key={row.id}>
                  {row.getVisibleCells().map((cell) => (
                    <td key={cell.id}>{flexRender(cell.column.columnDef.cell, cell.getContext())}</td>
                  ))}
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      <div style={{ marginTop: 12, color: 'var(--muted)', fontSize: 12 }}>
        Showing {Math.min(limit, total - offset)} of {total} repositories • Page {page}/{pageCount}
      </div>
    </div>
  )
}

function renderSortHeader(
  key: SortKey,
  current: SortKey,
  order: 'asc' | 'desc',
  setSortBy: (v: SortKey) => void,
  setOrder: (v: 'asc' | 'desc') => void,
) {
  const active = key === current
  const indicator = active ? (order === 'asc' ? ' ▲' : ' ▼') : ''
  const label = key === 'last_commit' ? 'Last commit' : key === 'contributors' ? 'Contribs' : key === 'commits' ? 'Commits' : key
  return (
    <button
      className="btn"
      style={{
        borderRadius: 10,
        padding: '6px 8px',
        border: '1px solid transparent',
        background: 'transparent',
        color: active ? 'var(--accent)' : 'var(--muted)',
        fontWeight: 700,
      }}
      onClick={() => {
        if (active) setOrder(order === 'asc' ? 'desc' : 'asc')
        else {
          setSortBy(key)
          setOrder('desc')
        }
      }}
    >
      {label}
      {indicator}
    </button>
  )
}

# sentra (rebuilt organ v2)

A rebuilt SZL five-space organ for the szl-build-env five-organ acceptance
stack. See [HONEST_PROVENANCE.md](HONEST_PROVENANCE.md) for the exact
provenance statement: the historical sentra source repository is unavailable,
and this repository is a new, separately owned rebuild - not a restoration.

## Contract

- `GET /healthz` only. Requires a valid W3C `traceparent` request header,
  echoes exactly one `traceparent` response header with the same trace id, a
  fresh sampled span id, and exports one honest OTLP/HTTP span
  (`service.name=sentra`) for the request actually served.
- Fail-closed OTLP endpoint policy: span export is admitted only to loopback or
  cluster-local (`*.svc`, `*.svc.cluster.local`) destinations configured via
  `SZL_OTLP_ENDPOINT`. No other egress exists in this service.
- Stdlib only. No third-party runtime dependencies.

## Configuration

| Variable | Meaning |
|---|---|
| `PORT` | Listen port (default 7860) |
| `SZL_OTLP_ENDPOINT` | OTLP/HTTP base URL, e.g. `http://opentelemetry-collector.szl.svc:4318` |

## Tests

```
python -m unittest discover -s tests -v
```

## Publication

Pushes to protected main run `.github/workflows/ghcr-build-push.yml`, which
builds the root Dockerfile, pushes by immutable digest to
`ghcr.io/szl-holdings/sentra`, and keyless-signs it with the exact workflow
identity the szl-build-env supply-chain gate verifies.

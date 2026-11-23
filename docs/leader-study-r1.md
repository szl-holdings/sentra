# sentra domain leader study r1 (propose-only)

Date: 2026-11-24. Method: web-verified leader landscape + governing-seat synthesis (Kimi nonce T4-SENTRA-BRIEF). This card is documentation only; it changes no code, CI, config, or existing PR status. All absorb actions are FUTURE PROPOSALS (non-authorizing); implementation and merges remain separately reviewed and gated.

## Domain: trace-honest five-space organ (W3C traceparent echo + OTLP span export, fail-closed)

## Leaders studied (web-verified 2026-11-24)

1. OpenTelemetry Specification (https://github.com/open-telemetry/opentelemetry-specification) — moat: vendor-neutral telemetry standard (traces/metrics/logs) with semantic conventions.
2. W3C Trace Context (https://w3c.github.io/trace-context/) — moat: the cross-service distributed-tracing header standard every mainstream runtime honors.
3. Jaeger (https://github.com/jaegertracing/jaeger) — moat: battle-tested open-source distributed tracing backend with adaptive sampling.

## Absorb actions (FUTURE PROPOSALS, non-authorizing)

1. (OpenTelemetry Specification) Propose a documentation-only conformance checklist mapping sentra's single OTLP/HTTP span (service.name=sentra) and traceparent echo behavior to the specification's trace and semantic-convention requirements, without claiming compliance until separately reviewed. Cost: careful spec reading and review effort; limit: this would not add metrics/logs, widen the GET /healthz-only contract, or prove interoperability.
2. (W3C Trace Context) Propose a future test-only review of traceparent validation and echo cases against the W3C header rules, preserving exactly one response traceparent with the same trace id and a fresh sampled span id and rejecting invalid input fail-closed. Cost: additional stdlib unittest cases and edge-case analysis; limit: no new runtime dependency, endpoint, or claim of W3C certification is authorized by this card.
3. (Jaeger) Propose an optional, separately gated local verification plan for viewing sentra's exported spans in Jaeger only through the existing loopback or cluster-local SZL_OTLP_ENDPOINT admission policy. Cost: local backend setup and manual receipt review; limit: no new egress, adaptive-sampling claim, production deployment, or measured performance benefit is proposed or implied.
4. (baseline) Propose preserving HONEST_PROVENANCE.md and the README's explicit statement that the historical sentra source repository is UNAVAILABLE and that v2 is a new separately owned rebuild, not a restoration, with any future leader-inspired work required to retain that provenance and the stdlib-only runtime. Limit: this card supplies no implementation, benchmark, tracing-backend compatibility result, or change to the protected-main digest/signature gate.

## Do not do (per governing seat)

Do not merge, bypass the signature wall, or claim implementation beyond this card.

# Sentra — Cyber Resilience Command

  > Governed security and threat intelligence pack — recursive threat modeling, regulated monitoring, evidence-bound decision artifacts.

  [![CI](https://github.com/szl-holdings/szl-holdings-platform/actions/workflows/ci.yml/badge.svg)](https://github.com/szl-holdings/szl-holdings-platform/actions/workflows/ci.yml)
  [![TypeScript](https://img.shields.io/badge/TypeScript-5.9-3178C6?style=flat-square&logo=typescript&logoColor=white)](https://www.typescriptlang.org/)
  [![Gov Readiness](https://img.shields.io/badge/NYSTEC%20readiness-68%2F100-2da44e?style=flat-square)](https://github.com/szl-holdings/ouroboros/blob/main/docs/audit/szl-government-readiness.md)
[![License](https://img.shields.io/badge/license-Proprietary-red?style=flat-square)](../../LICENSE.md)

  [Live Demo](https://szlholdings.com) · [Platform Demo Video](https://szlholdings.com/szl-demo-video/) · [Investor Dashboard](https://szlholdings.com/stephen/investor) · [Architecture](../../docs/architecture/architecture.md)

  ![Sentra — Cyber Resilience Command](https://raw.githubusercontent.com/szl-holdings/.github/main/assets/screenshots/sentra-dashboard.jpg)

  ---
  ## What it does

  Sentra is the **governed security and threat intelligence pack** within the A11oy ecosystem, providing recursive threat modeling, regulated monitoring, security review, escalation workflows, and evidence-bound decision artifacts. Every Sentra conclusion ships with primary-source hash, source attribution, and an audit trail that survives replay.

  ## Government readiness — 68/100

  April 30, 2026 NYSTEC pre-briefing audit. Very strong architecture and proof chain; needs SOC 2 Type II and formal runbooks before federal/state security reviews.

  | Capability | Government alignment |
  |---|---|
  | Recursive threat loop with risk tiers R1–R4 | NIST AI RMF MEASURE + MANAGE functions |
  | Evidence pack generation | DoD documentation requirements |
  | SHA-256 primary-source hash via Katzilla | Chain-of-custody for FDA, FEMA, Federal Register |
  | Forced escalation at R4_critical | DoD Governable tenet / GSA human oversight |
  | `VAL_SECURITY_PROOF_REQUIRED` validator | No security conclusions without evidence |
  | `VAL_APPROVAL_FOR_CRITICAL_ACTION` validator | Human-in-the-loop for high-stakes actions |

  **Best-fit government use cases**: cybersecurity monitoring for state/local agencies (the NY Joint Security Operations Center covers 95,000 computers); regulatory signal monitoring via primary-source Katzilla feeds; DoD/defense subcontracting through the NYSTEC network; audit-support services using Sentra receipts as audit evidence.

  **Open gaps** (documentation/certification): SOC 2 Type II, incident response runbook, formal threat-feed catalog, penetration testing.

  ## Run locally

  ```bash
  pnpm install
  pnpm --filter @workspace/api-server dev   # API server first
  pnpm --filter @workspace/sentra dev
  ```

  **Primary route:** `/sentra/`

  ## Tech stack

  React 19 + Vite 7 + TypeScript (strict) · Express 5 (shared API server) · PostgreSQL 16 / Drizzle ORM · Recursive threat-loop kernel · Katzilla primary-source feeds (FDA, FEMA, Federal Register, CourtListener)
  
  ---

  **SZL Holdings** · [szlholdings.com](https://szlholdings.com) · [inquiries@szlholdings.com](mailto:inquiries@szlholdings.com)

  ---
  ## About this repository

  This is a public showcase of one product in the [SZL Holdings platform](https://github.com/szl-holdings/szl-holdings-platform) monorepo. It mirrors the README from the platform artifact directory; the canonical, version-controlled source — including the React app, tests, and infrastructure — lives in the platform repo.

  All seven products share the same governed substrate:

  - **[`@workspace/ouroboros`](https://github.com/szl-holdings/ouroboros)** — bounded loops with measurable convergence, v6 ecosystem layer, government readiness module (**133/133 tests**)
  - **[`@workspace/codex-kernel`](https://github.com/szl-holdings/szl-holdings-platform/tree/master/packages/codex-kernel)** — decision receipts, validators, replay, trace-hash verification
  - **The Ouroboros Thesis** — [`szl-holdings/ouroboros-thesis`](https://github.com/szl-holdings/ouroboros-thesis) — architectural rationale + v6 operational contract

  Government readiness audit (NYSTEC pre-briefing, 2026-04-30): [`docs/audit/szl-government-readiness.md`](https://github.com/szl-holdings/ouroboros/blob/main/docs/audit/szl-government-readiness.md)

  © 2026 SZL Holdings. All rights reserved.
  
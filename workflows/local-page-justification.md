# Local Ranking & Justification Sub-Pipeline

---
workflow_version: 2
phase_sequence: [1, 2, 3, 4, 5, 6, 7, 8]
report_header_rule: one_authoritative_yaml_header_first_after_title
---

Mandatory read-only research workflow for one service/location geo-child. Never invent claims.
Only orchestrator may write WordPress state.

## Phase 1 — Frame

**Entry:** Inputs available or explicitly unavailable.

1. Normalize service, city/region/country, language, search location/device, delivery mode,
   query cluster, user job, candidate URL role, canonical and city hub.
2. Define 4–8 localized/action/modifier queries. City keyword alone is not demand proof.
3. State local thesis: information changing local decision/process beyond canonical.

**Exit:** Target cluster, page job, research boundary recorded.

## Phase 2 — Dataset resolution

**Entry:** Phase 1 complete. Target crawl, sample, canonical-only read, or selected-record scope is not resolution.

1. Snapshot `retrieved_at`; declare claim-specific relevance criteria, then enumerate every
   published record in each relevant CPT using pagination to proven exhaustion. A CPT may be
   excluded only with an explicit reason tied to the claims being resolved; unrelated glossary
   or archive corpora are not mandatory by default. Record exact CPT record count; exact
   searched-field list and per-field counts; aliases; filters; page numbers; page size; total
   pages/results; truncation status; hits; and zero-result proof. `100+`, `50+`, estimates,
   omitted required fields, or selected-record-only scope set dataset resolution BLOCKED.
2. Run `wpdev voxel:fields <site> <post_type>`, then Voxel-aware reads. Search title, core
   content/excerpt, every prose field, repeaters, and service/location/person/organization
   aliases. Re-read every selected hit with `./wpdev voxel:data <site> --id=<id>`.
3. Resolve outbound/inbound relations, max two hops, visited-set cycle-safe: service-reference,
   location, post_parent/hierarchy, organization, profiles/team, testimonials/cases, videos,
   events, articles, and discovered relation fields. Re-read every selected related record and
   record path. Relation cardinality is candidate discovery only; it never proves semantics.
4. For profiles/testimonials/cases, record exact field/content semantic match to service/location
   and approval classification. Missing semantic match or approval makes claim use BLOCKED.
5. Ledger usable stored evidence as `D##`, never `B##`. Each D row is one exact field or one
   repeater row: `voxel:<site>:<post_type>:<post_id>:<field>[:row]`; SHA-256 is computed from
   that exact stored field/row value. Raw relation ID, `:*`, whole-record hash in field hash,
   or `hash not captured` is invalid. Optional record snapshot SHA-256 is separate metadata.
6. Classify `PUBLIC|INTERNAL_PUBLISHABLE|CONFIDENTIAL|RESTRICTED_PERSONAL`; unknown is
   `CONFIDENTIAL`. Record approval, dates, redacted excerpt, confidence, and relation path.
   Only PUBLIC or approved INTERNAL_PUBLISHABLE supports authoring.
7. Apply source precedence: owner-approved first-party data; official authority; public
   first-party page; recognized industry; SERP/competitor/community for intent only; inference
   never fact. Log conflict; unresolved authoritative conflict blocks claim.

| ID | Claim | Exact locator | exact_value_sha256 | relation path | semantic match/approval | classification | dates | redacted excerpt | confidence |
|---|---|---|---|---|---|---|---|---|---|

Set only `dataset_resolution_state: PASS|BLOCKED`. PASS means the declared relevant corpus was
enumerated exactly, searched without silent truncation, relation-traversed, and selected hits
were re-read with valid field locators/hashes. Approval, freshness, confidentiality,
official-registration, and publishability gaps do not change dataset PASS; record them as
separate downstream evidence/publication gates. BLOCKED means the dataset search itself is
incomplete, approximate, truncated, invalidly hashed, or missing required relation traversal.

**Exit:** Auditable declared scope and valid D ledger exist before acquisition. Separate gates
record whether resolved evidence may be published, needs approval/freshness/official proof, or
must remain confidential.

## Phase 3 — Bounded acquisitions

**Entry:** Dataset PASS.

1. Run only gap-closing SERP/conversion, official local context, competitor/gain, and
   architecture lanes.
2. Persist endpoint, scope, date, result/no-result, and blocker.
3. Snippets are leads only; acquisition cannot replace dataset resolution.

**Exit:** Bounded acquisition proof exists.

## Phase 4 — Evidence, anchors, similarity

**Entry:** Phases 2–3 complete.

1. Assign `E##` official/industry, `B##` public business-owned, `V##` volatile, and `D##` dataset
   IDs, one claim per row. D rows retain Phase-2 exact locator/hash requirements. `V##` records
   `verified_at`, affected fields, recheck, expiry/trigger; stale V blocks full mutation.
2. Confirm local anchor changes local decision/process/resources/delivery and passes city-swap.
   Exclude national law, generic demand, maps/schema/population, competitor city pages, clichés,
   tourism, boosterism, decorative landmarks, and unsupported entities. Entity name needs cited
   service consequence or DELETE.
3. Emit normalized sibling fingerprint: headings, paragraph fingerprints, FAQ purposes, timeline
   stages, card purposes; strip city/entity/personal tokens. Orchestrator alone sets
   `corpus_similarity_state: PASS|FAIL|PENDING`. FAIL or PENDING blocks READY and full mutation;
   any score is labelled `strategy_only_score` while blocked.

**Exit:** Claim boundaries, anchors, exclusions, entity matrix, fingerprint recorded.

## Phase 5 — Emergency neutralization

**Entry:** Existing live geo-child contains dangerous unsupported/invented claim.

1. Research emits exact row for every finding, or `BLOCKED` row with reason.
2. Remove/narrow with literal evidence-backed neutral text only; no positive claim. Research
   never records APPLIED.

| post_id | field | owner | type | operation | expected_before_sha256 | exact_neutral_value | evidence_ids | freshness_gate | execution_authority | neutralization_state |
|---|---|---|---|---|---|---|---|---|---|---|

3. Set `neutralization_state: NOT_REQUIRED|READY_FOR_ORCHESTRATOR|BLOCKED|APPLIED|SKIPPED_DRIFT`.
   Research may emit READY_FOR_ORCHESTRATOR or BLOCKED only.
4. Orchestrator re-reads exact stored value; mismatch is SKIPPED_DRIFT. `freshness_gate` is
   `live_sha256_matches_expected_before_sha256`; `execution_authority` is `orchestrator_only`.

**Exit:** Every dangerous finding has candidate or BLOCKED reason.

## Phase 6 — Blueprint and anti-slop

**Entry:** Phase 4 complete.

1. Align page type to SERP; define sourced information gain, URL/canonical/city-hub role,
   modules, CTA, proof, and acquisition gates.
2. Delete prose lacking sourced fact, query answer, service consequence, proof, or legitimate
   next action.
3. Record canned/fake/unsupported/redundant content as DELETE, RESEARCH, REWRITE FROM EVIDENCE,
   or KEEP with evidence IDs.

**Exit:** Non-artificial blueprint and anti-slop ledger.

## Phase 7 — Validation gate and scoring

**Entry:** Phases 5–6 complete.

1. Before scoring, validate report: one required authoritative header; exact dataset scope;
   valid D locators and exact-value SHA-256s; every closed enum valid; no duplicate state block;
   acquisitions proven; and candidate-neutralization rows current, or `neutralization_state`
   accurately APPLIED/NOT_REQUIRED/BLOCKED. Failure forces `research_state: INCOMPLETE` and
   `dataset_resolution_state: BLOCKED`; score/readiness cannot upgrade.
2. Score: SERP intent 0–3; local usefulness 0–4; local authority 0–4; delivery proof 0–3;
   information gain 0–2; architecture 0–2; proof/assets 0–2. Hard gates: dataset PASS,
   publishable evidence for each local claim, two city-swap anchors, no unsupported/equivalent
   sibling content, SERP/architecture fit, and regulated approval/registration when applicable.
3. Set closed enums only: `research_state: COMPLETE|INCOMPLETE`; `publication_state:
   READY|BLOCKED`; `mutation_state: READY|NOT_READY`; `corpus_similarity_state:
   PASS|FAIL|PENDING`; `dataset_resolution_state: PASS|BLOCKED`; `strategy_readiness:
   READY|READY_WITH_ACQUISITIONS|NOT_READY`. READY needs all gates and ≥17/20. Acquisitions
   needs PASS, ≥14/20, named feasible assets, and blocks publication/full mutation. FAIL/PENDING
   similarity blocks READY/full mutation and labels score strategy-only.

**Exit:** One current value per enum and rationale.

## Phase 8 — Report contract

**Entry:** Phase 7 complete.

1. Start report with title, then exactly one YAML header as first following content:

```yaml
artifact_version: 2
scope_id: geo:exp:<post_id>
report_path: <exact caller path>
target_post_id: <id>
canonical_post_id: <id>
service_slug: <slug>
city_slug: <slug>
generated_at: <ISO-8601>
research_state: COMPLETE|INCOMPLETE
dataset_resolution_state: PASS|BLOCKED
corpus_similarity_state: PASS|FAIL|PENDING
publication_state: READY|BLOCKED
mutation_state: READY|NOT_READY
strategy_readiness: READY|READY_WITH_ACQUISITIONS|NOT_READY
```

2. On revision, rewrite report into this one authoritative header. Alternative: add top
   supersession block before every legacy draft declaring legacy drafts non-normative; never
   retain conflicting closed states.
3. Include exact dataset proof, D ledger, semantic/approval decisions, acquisition proof,
   anchors, validation result, one closed-state block, score, blueprint, fingerprint, and
   neutralization manifest.
4. Candidate content manifest requires `mutation_state: READY` and similarity PASS (or
   undeclared campaign). Orchestrator alone writes validated/applied manifests.

**Exit:** READY may plan; acquisitions may draft only; NOT_READY halts full rewrite. Neutralization
remains independent.

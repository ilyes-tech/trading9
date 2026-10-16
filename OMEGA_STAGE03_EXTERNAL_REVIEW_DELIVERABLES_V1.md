# OMEGA Stage03 - External scientific review action sheet (NOT AN APPROVAL)

## Current scientific state: STOP
- No scientifically admitted candidate; no real-market experiment, search, MT5, live orders, holdout or autotrading authorized.
- Project: BINANCE COIN-M BTCUSD_PERP, nontrading forecast of next 300-second midquote displacement.
- Initial signed review: MISSING. Independently attested prospective evidence: MISSING. Second scientific assessment: MISSING.
- The reviewer's task is to judge novelty and validity, **not** to force approval.

## Input package already prepared on primary VPS
- Remote path: /home/trading/.local/state/tradingai/jarvis-autonomous/stage03_liquidation_source_access_v1/stage03_external_review_inputs_bundle_v1.zip
- ZIP SHA-256: f482c4636d09ebf8c18e09232cf83559a1135f435f34a29fa8100f1f928d5e9d
- Exact initial packet SHA-256: 83f8ba8a347a897a36a3ed9d241727ce7cc9cfe437074e05a207f0c1e27165fa
- Exact supplemental index SHA-256: fccad70c61848af26e593e99cc6138009fde67e48d33bbb9ef47d557c4a669af
- ZIP contains 8 original evidence files, 2 supplemental public probes, source packet, index, README and checksum manifest.
- The original packet covers 8 sources. The index adds 2 probes. Recent public probes contain 98 target COIN-M depth updates and **zero** confirmed BTCUSD_PERP target forceOrder observations. These probes are not prospective, independently attested science.

## FIRST independent reviewer - method eligibility
1. Independently examine the 8 + 2 sources, causal novelty versus exhausted BOOK_PRESSURE/trade-flow families, event timing, matched controls, and the finite development-only proposal.
2. Choose one review outcome, including REJECT or REQUEST_FIXED_DEFINITION where indicated by evidence. No positive outcome is presumed.
3. Sign the exact bytes of external_initial_review_v1.json as detached raw Ed25519 signature external_initial_review_v1.sig. Its payload must bind:
   kind=OMEGA_EXTERNAL_INITIAL_SCIENTIFIC_REVIEW_V1,
   instrument=BINANCE_COINM_BTCUSD_PERP,
   packet_sha256=83f8ba8a347a897a36a3ed9d241727ce7cc9cfe437074e05a207f0c1e27165fa,
   protocol_sha256=c00de6d4aa040954471fe99bb102d648133c43bfbd10b1095c665d70218128c3,
   supplemental_review_index_sha256=fccad70c61848af26e593e99cc6138009fde67e48d33bbb9ef47d557c4a669af,
   reviewer_id=(real reviewer), decision=(one allowed review decision).
4. An independent trusted administrator, never JARVIS/the applicant, provisions the genuine Ed25519 PUBLIC key as root-owned /etc/tradingai/omega-scientific-review-pubkey.pem, not group/world writable. The PRIVATE key remains with the independent reviewer.
5. Merely signing an 'eligible for initial review' decision does NOT admit a causal strategy or authorize data access or experimentation.

## SECOND external assessment - only after first review signature verified
1. Independently verify prospective target liquidation receipts, trusted receipt-time chronology, future preregistration, and fixed timing/control protocol. There is no substitute for genuinely collected third-party evidence.
2. The verifier expects external_prospective_source_provenance_v1.json with exactly these four named source roles:
   target_liquidation_receipts; receipt_clock_attestation; prospective_preregistration; fixed_control_protocol.
   Each source descriptor contains filename and SHA-256 of the actual independent source JSON. Files must be distinct.
3. The provenance document must bind BINANCE_COINM_BTCUSD_PERP, initial_packet_sha256 and review_index_sha256 and explicitly deny research_execution_authorized, orders_allowed, and holdout_allowed.
4. A distinct authorized assessment must sign external_scientific_assessment_v1.json with detached raw Ed25519 signature external_scientific_assessment_v1.sig. Review JSON binds:
   kind=OMEGA_EXTERNAL_STAGE03_SCIENTIFIC_ASSESSMENT_V1,
   instrument=BINANCE_COINM_BTCUSD_PERP,
   review_index_sha256=fccad70c61848af26e593e99cc6138009fde67e48d33bbb9ef47d557c4a669af,
   provenance_sha256=(SHA-256 of the exact complete provenance file),
   reviewer_id=(real reviewer), decision=(one verifier-approved assessment decision).
5. Independently provision the stage-2 trusted PUBLIC key at /etc/tradingai/omega-stage03-science-pubkey.pem under root ownership without write access for group/others.
6. A cryptographically valid second assessment is still a receipt/integrity result, NOT independent replication, scientific admission, development permission, or approval to send orders.

## Current hard external dependency and execution constraints
- No first trusted review authority or signed review files exist on the VPS.
- No second trusted assessment authority, signed assessment, or trusted prospective provenance files exist.
- Do NOT generate self-signed production approvals, fabricate source receipts, shorten the prospective window, read final holdout, activate Searcher, or place any order to unblock this state.
- Until the external actors complete their work, Stage03 remains FAIL/BLOCKED, regardless of test count or engineering readiness.

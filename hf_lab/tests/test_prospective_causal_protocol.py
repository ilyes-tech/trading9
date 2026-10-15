"""Fail-closed tests of review-only hypothesis submission; no live search or trading."""
import json
import runpy
from pathlib import Path

A = Path('/home/trading/TradingAI-HF-Lab/research_agent_v57_quantum_searcher/tools/v57_jarvis/autonomy')
NS = runpy.run_path(str(A / 'v57_prospective_causal_protocol_v1.py'))
BASE = NS['BASE']
validate = NS['validate']
FIELDS = NS['REQUIRED_HYPOTHESIS']


def complete():
    return dict(BASE, hypothesis_status='FORMULATED_FOR_REVIEW',
                hypothesis={key: 'synthetic-test-only' for key in FIELDS})


def test_existing_unformulated_protocol_stays_valid_but_not_authorized():
    assert validate(dict(BASE)) == 'PROTOCOL_VALID_NOT_AUTHORIZED'
    assert validate(dict(BASE, hypothesis_status='ADMITTED')) == 'DENY_PRETEND_EVIDENCE'


def test_complete_hypothesis_is_reviewable_not_authorized():
    p = complete()
    assert p['execution_authorized'] is False
    assert validate(p) == 'PROTOCOL_REVIEW_REQUIRED_NOT_AUTHORIZED'


def test_incomplete_or_false_evidence_cannot_pass():
    p = complete()
    p['hypothesis'].pop('falsification_rule')
    assert validate(p) == 'DENY_INCOMPLETE_HYPOTHESIS'
    p = complete()
    p['hypothesis']['mechanism'] = ' '
    assert validate(p) == 'DENY_INCOMPLETE_HYPOTHESIS'
    p = complete()
    p['evidence_status'] = 'VERIFIED'
    assert validate(p) == 'DENY_PRETEND_EVIDENCE'


def test_safety_and_validation_rules_stay_closed():
    for change in (
        {'orders_allowed': True}, {'execution_authorized': True},
        {'holdout_allowed': True}, {'mt5_allowed': True},
        {'research_execution_authorized': True},
        {'data_separation': 'UNKNOWN'},
    ):
        actual = validate(dict(complete(), **change))
        assert actual.startswith('DENY_'), (change, actual)


def test_review_file_reports_only_reviewability(tmp_path):
    review = NS['review_file']
    review.__globals__['S'] = tmp_path
    base = tmp_path / 'prospective_causal_protocol_v1.json'
    base.write_text('keep-existing-base-unchanged')
    source = tmp_path / 'submission.json'
    source.write_text(json.dumps(complete()))
    assert review(source) == 0
    output = json.loads((tmp_path / 'prospective_causal_protocol_review_v1.json').read_text())
    assert output['status'] == 'PROTOCOL_REVIEW_REQUIRED_NOT_AUTHORIZED'
    assert output['hypothesis_formulated'] is True
    assert output['research_execution_authorized'] is False
    assert output['orders_allowed'] is False
    assert base.read_text() == 'keep-existing-base-unchanged'


def test_review_file_rejects_symlink_and_oversize(tmp_path):
    review = NS['review_file']
    review.__globals__['S'] = tmp_path
    target = tmp_path / 'source.json'
    target.write_text(json.dumps(complete()))
    link = tmp_path / 'link.json'
    link.symlink_to(target)
    for item in (link,):
        try:
            review(item)
        except ValueError as e:
            assert str(e) == 'INVALID_REVIEW_FILE'
        else:
            assert False, 'review must reject symlinks'
    target.write_text(' ' * 16385)
    try:
        review(target)
    except ValueError as e:
        assert str(e) == 'INVALID_REVIEW_FILE'
    else:
        assert False, 'review must reject oversized inputs'


def test_stage03_preexperiment_review_is_separate_from_replication(tmp_path):
    """Review of a first experiment never needs fabricated replication evidence."""
    import hashlib
    ns = runpy.run_path(str(A / 'v57_hypothesis_feasibility_triage_v1.py'))
    gate = ns['first_experiment_review_status']
    gate.__globals__['PREEXPERIMENT'] = tmp_path / 'preexperiment.json'
    gate.__globals__['PREEXPERIMENT_REVIEW'] = tmp_path / 'review.json'
    assert gate() is None
    proposal = complete()
    proposal['hypothesis']['market'] = 'Binance COIN-M BTCUSD_PERP'
    raw = json.dumps(proposal).encode()
    (tmp_path / 'preexperiment.json').write_bytes(raw)
    digest = hashlib.sha256(raw).hexdigest()
    (tmp_path / 'review.json').write_text(json.dumps({
        'status': 'PROTOCOL_REVIEW_REQUIRED_NOT_AUTHORIZED',
        'submission_sha256': digest,
        'independent_evidence_verified': False,
        'research_execution_authorized': False,
        'execution_authorized': False,
        'orders_allowed': False, 'mt5_allowed': False,
        'holdout_allowed': False, 'auto_promotion_allowed': False}))
    assert gate() == digest
    proposal['hypothesis']['market'] = 'different-market'
    (tmp_path / 'preexperiment.json').write_text(json.dumps(proposal))
    assert gate() is None


def test_stage03_preexperiment_rejects_unsafe_and_tampered_review(tmp_path):
    import hashlib
    ns = runpy.run_path(str(A / 'v57_hypothesis_feasibility_triage_v1.py'))
    gate = ns['first_experiment_review_status']
    gate.__globals__['PREEXPERIMENT'] = tmp_path / 'preexperiment.json'
    gate.__globals__['PREEXPERIMENT_REVIEW'] = tmp_path / 'review.json'
    proposal = complete()
    proposal['hypothesis']['market'] = 'BTCUSD_PERP'
    proposal_raw = json.dumps(proposal).encode()
    (tmp_path / 'preexperiment.json').write_bytes(proposal_raw)
    review = dict(status='PROTOCOL_REVIEW_REQUIRED_NOT_AUTHORIZED',
                  submission_sha256=hashlib.sha256(proposal_raw).hexdigest(),
                  independent_evidence_verified=False,
                  research_execution_authorized=False,
                  execution_authorized=False, orders_allowed=False,
                  mt5_allowed=False, holdout_allowed=False, auto_promotion_allowed=False)
    (tmp_path / 'review.json').write_text(json.dumps(review))
    assert gate()
    review['research_execution_authorized'] = True
    (tmp_path / 'review.json').write_text(json.dumps(review))
    assert gate() is None
    review['research_execution_authorized'] = False
    review['submission_sha256'] = '0' * 64
    (tmp_path / 'review.json').write_text(json.dumps(review))
    assert gate() is None
    (tmp_path / 'preexperiment.json').unlink()
    (tmp_path / 'preexperiment.json').symlink_to(tmp_path / 'review.json')
    assert gate() is None


def test_stage03_public_source_status_is_provisional_and_fail_closed(tmp_path):
    import hashlib
    ns = runpy.run_path(str(A / 'v57_hypothesis_feasibility_triage_v1.py'))
    gate = ns['public_liquidation_source_status']
    path = tmp_path / 'source.json'
    gate.__globals__['SOURCE'] = path
    assert gate() is None
    doc = dict(kind='OMEGA_STAGE03_LIQUIDATION_PUBLIC_SOURCE_ACCESS_REVIEW_V1',
               status='PUBLIC_FUTURES_INSTRUMENT_AND_BOOK_REST_ACCESS_VERIFIED_LIQUIDATION_STREAM_UNTESTED',
               instrument=dict(symbol='BTCUSD_PERP', pair='BTCUSD'),
               research_execution_authorized=False, candidate_admitted=False,
               orders_allowed=False, mt5_allowed=False, holdout_allowed=False,
               auto_promotion_allowed=False)
    raw = json.dumps(doc).encode()
    path.write_bytes(raw)
    assert gate() == hashlib.sha256(raw).hexdigest()
    doc['orders_allowed'] = True
    path.write_text(json.dumps(doc))
    assert gate() is None
    path.unlink()
    path.symlink_to('/nonexistent')
    assert gate() is None


def test_global_forceorder_sample_cannot_be_misclassified_as_target_coinm(tmp_path):
    import hashlib
    ns = runpy.run_path(str(A / 'v57_hypothesis_feasibility_triage_v1.py'))
    check = ns['non_target_liquidation_sample_sha256']
    target = tmp_path / 'global.json'
    check.__globals__['GLOBAL_FORCEORDER'] = target
    assert check() is None
    sample = dict(e='forceOrder', symbol='WALUSDT', st=1, side='SELL', sha256='a' * 64)
    doc = dict(kind='OMEGA_STAGE03_GLOBAL_BINANCE_LIQUIDATION_MESSAGE_SCHEMA_TRIAGE_V1',
               status='PUBLIC_REAL_FORCEORDER_MESSAGES_OBSERVED_USDM_ONLY_NO_COINM_TARGET',
               target_symbol='BTCUSD_PERP', target_required_stream_type=2,
               target_messages_observed=0,
               liquidation_messages_verified_on_target_instrument=False,
               public_observed_message_metadata=[sample], observed_messages=1,
               research_execution_authorized=False, candidate_admitted=False,
               backtest_executed=False, search_executed=False,
               orders_allowed=False, mt5_allowed=False, holdout_allowed=False,
               auto_promotion_allowed=False)
    payload = json.dumps(doc).encode()
    target.write_bytes(payload)
    assert check() == hashlib.sha256(payload).hexdigest()
    doc['public_observed_message_metadata'][0]['st'] = 2
    target.write_text(json.dumps(doc))
    assert check() is None
    doc['public_observed_message_metadata'][0]['st'] = 1
    doc['target_messages_observed'] = 1
    target.write_text(json.dumps(doc))
    assert check() is None
    doc['target_messages_observed'] = 0
    doc['research_execution_authorized'] = True
    target.write_text(json.dumps(doc))
    assert check() is None
    target.unlink()
    target.symlink_to(tmp_path / 'missing')
    assert check() is None


def test_historical_coinm_archive_status_checks_both_bytes_not_new_admission(tmp_path):
    """Archived source integrity may advance feasibility, never execution."""
    import hashlib
    ns = runpy.run_path(str(A / 'v57_hypothesis_feasibility_triage_v1.py'))
    gate = ns['historical_coinm_archive_integrity_sha256']
    gate.__globals__['HISTORICAL'] = tmp_path / 'report.json'
    assert gate() is None
    files = []
    for date in ('2024-06-15', '2024-06-16'):
        name = 'BTCUSD_PERP-liquidationSnapshot-' + date + '.zip'
        raw = ('test-only-' + date).encode()
        (tmp_path / name).write_bytes(raw)
        files.append(dict(date=date, official_checksum_validated=True,
                          identical_duplicate_rows=12, unique_timestamp_count=12,
                          zip_sha256=hashlib.sha256(raw).hexdigest()))
    safe = dict(scientifically_independent_review=False, candidate_admitted=False,
                research_execution_authorized=False, search_executed=False,
                backtest_executed=False, orders_allowed=False, mt5_allowed=False,
                holdout_allowed=False, auto_promotion_allowed=False)
    doc = dict(kind='OMEGA_BINANCE_COINM_BTCUSD_PERP_LIQUIDATION_HISTORICAL_SOURCE_AUDIT_V1',
               status='OFFICIAL_COINM_ARCHIVES_INTEGRITY_VERIFIED_HISTORICAL_DUPLICATES_REVIEW_REQUIRED',
               market='BINANCE_COINM_BTCUSD_PERP',
               all_official_checksums_pass=True,
               first_experiment_data_available=False, archives=files, **safe)
    raw = json.dumps(doc).encode()
    (tmp_path / 'report.json').write_bytes(raw)
    assert gate() == hashlib.sha256(raw).hexdigest()
    (tmp_path / 'BTCUSD_PERP-liquidationSnapshot-2024-06-16.zip').write_bytes(b'tampered')
    assert gate() is None
    (tmp_path / 'BTCUSD_PERP-liquidationSnapshot-2024-06-16.zip').write_bytes(b'test-only-2024-06-16')
    doc['candidate_admitted'] = True
    (tmp_path / 'report.json').write_text(json.dumps(doc))
    assert gate() is None
    doc['candidate_admitted'] = False
    (tmp_path / 'report.json').write_text(json.dumps(doc))
    (tmp_path / 'report.json').unlink()
    (tmp_path / 'report.json').symlink_to(tmp_path / 'report-elsewhere')
    assert gate() is None


def test_stage03_historical_regime_coverage_tracks_checksums_but_denies_admission(tmp_path):
    """Trusted live research does not follow from historical archive metadata."""
    import hashlib
    ns=runpy.run_path(str(A/'v57_hypothesis_feasibility_triage_v1.py'))
    check=ns['historical_regime_coverage']
    report=tmp_path/'source.json'
    timing=tmp_path/'temporal.json'
    check.__globals__['HISTORICAL_REGIME']=report
    check.__globals__['HISTORICAL_TEMPORAL']=timing
    assert check() is None
    rows=[]
    for day,unique in [('2024-03-05',672),('2024-04-13',423),
                       ('2024-08-05',952),('2024-08-06',179)]:
        name=f'BTCUSD_PERP-liquidationSnapshot-{day}.zip'
        raw=day.encode()
        (tmp_path/name).write_bytes(raw)
        rows.append(dict(day=day,kind='liquidationSnapshot',zip_file=name,
                         zip_sha256=hashlib.sha256(raw).hexdigest(),
                         provider_checksum_verified=True,historical_only=True,
                         unique_timestamps=unique,exact_duplicate_rows=unique))
    name='BTCUSD_PERP-bookDepth-2024-08-05.zip'
    (tmp_path/name).write_bytes(b'book')
    rows.append(dict(day='2024-08-05',kind='bookDepth',zip_file=name,
                     zip_sha256=hashlib.sha256(b'book').hexdigest(),
                     provider_checksum_verified=True,historical_only=True))
    safe=dict(prospective_data_admitted=False,scientific_hypothesis_admitted=False,
              research_execution_authorized=False,search_executed=False,
              backtest_executed=False,orders_allowed=False,mt5_allowed=False,
              holdout_allowed=False,auto_promotion_allowed=False)
    doc=dict(kind='OMEGA_STAGE03_BTCUSD_PERP_HISTORICAL_EVENT_REGIME_AUDIT_V1',
             status='OFFICIAL_ARCHIVE_CHECKSUM_PASS_EVENT_SAMPLE_ACROSS_REGIMES_NOT_EXPERIMENT',
             instrument='BINANCE_COINM_BTCUSD_PERP',records=rows,**safe)
    raw=json.dumps(doc).encode()
    report.write_bytes(raw)
    clocks=dict(kind='OMEGA_STAGE03_COINM_HISTORICAL_TEMPORAL_COVERAGE_AUDIT_V1',
                source_audit_sha256=hashlib.sha256(raw).hexdigest(),
                book_depth_exactly_thirty_seconds_spacing=True,
                book_depth_ticks=2880,book_depth_bucket_count=10,
                august_5_unique_liquidation_snapshot_times=952,
                august_5_events_with_prior_thirty_second_book_depth_grid=952,
                future_prospective_data_verified=False,
                hypothesis_admitted=False,independent_scientific_review=False,
                research_execution_authorized=False,backtest_executed=False,
                search_executed=False,orders_allowed=False,mt5_allowed=False,
                holdout_allowed=False,auto_promotion_allowed=False)
    timing.write_text(json.dumps(clocks))
    assert check()[2]==2226
    (tmp_path/'BTCUSD_PERP-bookDepth-2024-08-05.zip').write_bytes(b'tamper')
    assert check() is None
    (tmp_path/'BTCUSD_PERP-bookDepth-2024-08-05.zip').write_bytes(b'book')
    clocks['research_execution_authorized']=True
    timing.write_text(json.dumps(clocks))
    assert check() is None
    clocks['research_execution_authorized']=False
    timing.write_text(json.dumps(clocks))
    rows[0]['unique_timestamps']=671
    doc['records']=rows
    report.write_text(json.dumps(doc))
    assert check() is None


def test_initial_external_signature_binding_is_review_only(tmp_path):
    """Test-only Ed25519 authority; never provision or forge a production reviewer."""
    import hashlib
    import subprocess
    verify = NS['verify_signed_initial_review']
    state = tmp_path / 'state'
    folder = state / 'stage03_liquidation_source_access_v1'
    folder.mkdir(parents=True)
    keys = ('protocol','review','regimes','temporal','costs','live','other_market','historical_quotes')
    evidence = {}
    for key in keys:
        file = folder / (key + '.json')
        raw = json.dumps(dict(test_only=True, evidence_type=key)).encode()
        file.write_bytes(raw)
        evidence[key] = dict(relative_file=str(file.relative_to(state)),
                             sha256=hashlib.sha256(raw).hexdigest())
    packet = folder / 'initial_method_review_handoff_v1.json'
    packet_data = dict(kind='OMEGA_STAGE03_EXTERNAL_PREEXPERIMENT_REVIEW_HANDOFF_V1',
                       status='READY_FOR_EXTERNAL_REVIEW_ONLY',
                       instrument='BINANCE_COINM_BTCUSD_PERP',
                       verified_source_files=evidence, development_authorized=False,
                       candidate_admitted=False, search_executed=False, backtest_executed=False,
                       orders_allowed=False, mt5_allowed=False, holdout_allowed=False,
                       auto_promotion_allowed=False)
    packet.write_text(json.dumps(packet_data))
    private=tmp_path/'synthetic-only-private.pem'
    public=tmp_path/'synthetic-only-public.pem'
    subprocess.run(['/usr/bin/openssl','genpkey','-algorithm','ED25519','-out',str(private)],
                   check=True,capture_output=True)
    subprocess.run(['/usr/bin/openssl','pkey','-in',str(private),'-pubout','-out',str(public)],
                   check=True,capture_output=True)
    public.chmod(0o644)
    review=folder/'external_initial_review_v1.json'
    sig=folder/'external_initial_review_v1.sig'
    values=dict(kind='OMEGA_EXTERNAL_INITIAL_SCIENTIFIC_REVIEW_V1',
                packet_sha256=hashlib.sha256(packet.read_bytes()).hexdigest(),
                protocol_sha256=evidence['protocol']['sha256'],
                instrument='BINANCE_COINM_BTCUSD_PERP',
                decision='ELIGIBLE_FOR_SCIENTIFIC_INITIAL_REVIEW_ONLY',
                reviewer_id='SYNTHETIC_ISOLATED_TEST')
    review.write_text(json.dumps(values,sort_keys=True))
    subprocess.run(['/usr/bin/openssl','pkeyutl','-sign','-inkey',str(private),
                    '-rawin','-in',str(review),'-out',str(sig)],
                   check=True,capture_output=True)
    out=verify(packet,review,sig,public)
    assert out['status']=='INITIAL_REVIEW_SIGNATURE_VERIFIED_NOT_AUTHORIZED'
    assert all(out[k] is False for k in ('research_execution_authorized','causal_novelty_proven',
                                         'independent_replication_proven','orders_allowed','mt5_allowed'))
    (folder/'regimes.json').write_text('tampered')
    assert verify(packet,review,sig,public)['status']=='DENY_INITIAL_REVIEW_EVIDENCE_TAMPERED'
    (folder/'regimes.json').write_text(json.dumps(dict(test_only=True,evidence_type='regimes')))
    values['reviewer_id']='CHANGED_AFTER_SIGNATURE'
    review.write_text(json.dumps(values,sort_keys=True))
    assert verify(packet,review,sig,public)['status']=='DENY_INITIAL_REVIEW_SIGNATURE_INVALID'
    public.chmod(0o666)
    assert verify(packet,review,sig,public)['status']=='DENY_INDEPENDENT_REVIEW_AUTHORITY_NOT_PROVISIONED'


def test_initial_external_review_requires_real_trust_key_and_safe_packet(tmp_path):
    import hashlib
    verify=NS['verify_signed_initial_review']
    state=tmp_path/'state'
    folder=state/'stage03_liquidation_source_access_v1'
    folder.mkdir(parents=True)
    names=('protocol','review','regimes','temporal','costs','live','other_market')
    files={}
    for n in names:
        file=folder/(n+'.json')
        file.write_text('test-only')
        files[n]=dict(relative_file=str(file.relative_to(state)),
                      sha256=hashlib.sha256(file.read_bytes()).hexdigest())
    packet=folder/'packet.json'
    doc=dict(kind='OMEGA_STAGE03_EXTERNAL_PREEXPERIMENT_REVIEW_HANDOFF_V1',
             status='READY_FOR_EXTERNAL_REVIEW_ONLY',instrument='BINANCE_COINM_BTCUSD_PERP',
             verified_source_files=files,development_authorized=False,candidate_admitted=False,
             search_executed=False,backtest_executed=False,orders_allowed=False,
             mt5_allowed=False,holdout_allowed=False,auto_promotion_allowed=False)
    packet.write_text(json.dumps(doc))
    review=folder/'review.json'
    sig=folder/'review.sig'
    missing=tmp_path/'not-provisioned.pem'
    assert verify(packet,review,sig,missing)['status']=='DENY_INDEPENDENT_REVIEW_AUTHORITY_NOT_PROVISIONED'
    doc['development_authorized']=True
    packet.write_text(json.dumps(doc))
    assert verify(packet,review,sig,missing)['status']=='DENY_INITIAL_REVIEW_PACKET_SCHEMA'
    doc['development_authorized']=False
    packet.write_text(json.dumps(doc))
    (folder/'protocol.json').unlink()
    (folder/'protocol.json').symlink_to('/nonexistent')
    assert verify(packet,review,sig,missing)['status']=='DENY_INITIAL_REVIEW_PACKET_UNREADABLE'


def test_historical_top_of_book_audit_is_byte_bound_not_execution(tmp_path):
    """A verified prior quote is not a live received quote or executable fill."""
    import hashlib
    ns=runpy.run_path(str(A/'v57_hypothesis_feasibility_triage_v1.py'))
    gate=ns['historical_quote_coverage']
    gate.__globals__['HISTORICAL_QUOTES']=tmp_path/'historical_pre_event_quote_coverage_v1.json'
    gate.__globals__['HISTORICAL_REGIME']=tmp_path/'historical_regime_source_audit_v1.json'
    assert gate() is None
    regime=b'test-only-regime'
    (tmp_path/'historical_regime_source_audit_v1.json').write_bytes(regime)
    body=b'test-only-zip-not-for-trading'
    source=tmp_path/'BTCUSD_PERP-bookTicker-2024-08-05.zip'
    checksum=tmp_path/'BTCUSD_PERP-bookTicker-2024-08-05.zip.CHECKSUM'
    source.write_bytes(body)
    sha=hashlib.sha256(body).hexdigest()
    checksum.write_text(sha+'  BTCUSD_PERP-bookTicker-2024-08-05.zip\n')
    safe={k:False for k in ('research_execution_authorized','backtest_executed',
                             'search_executed','orders_allowed','mt5_allowed',
                             'holdout_allowed','auto_promotion_allowed')}
    report=dict(kind='OMEGA_STAGE03_BTCUSD_PERP_ARCHIVED_QUOTES_PRE_EVENT_AUDIT_V1',
      status='HISTORICAL_BEFORE_EVENT_QUOTE_COVERAGE_CHECKED_NOT_EXECUTABLE',
      instrument='BINANCE_COINM_BTCUSD_PERP',day='2024-08-05',
      source_metadata_sha256=hashlib.sha256(regime).hexdigest(),
      source_zip_bytes=len(body),source_zip_sha256=sha,
      liquidation_unique_timestamps=952,before_event_quotes_matched=952,
      before_event_quotes_missing=0,strictly_before_exchange_event_time=True,
      quotes_are_proven_received_at_decision_time=False,
      broker_fills_verified=False,cost_model_fully_calibrated=False,
      scientific_independence_verified=False,median_quote_spread_bps=0.02,**safe)
    report_path=tmp_path/'historical_pre_event_quote_coverage_v1.json'
    raw=json.dumps(report).encode()
    report_path.write_bytes(raw)
    assert gate()==hashlib.sha256(raw).hexdigest()
    source.write_bytes(b'tampered')
    assert gate() is None
    source.write_bytes(body)
    report['research_execution_authorized']=True
    report_path.write_text(json.dumps(report))
    assert gate() is None
    report['research_execution_authorized']=False
    report['quotes_are_proven_received_at_decision_time']=True
    report_path.write_text(json.dumps(report))
    assert gate() is None
    report['quotes_are_proven_received_at_decision_time']=False
    report_path.write_text(json.dumps(report))
    checksum.write_text('0'*64+'  file.zip\n')
    assert gate() is None


def test_initial_scientific_readiness_is_fail_closed():
    ns=runpy.run_path(str(A/'v57_independent_evidence_verifier_v2.py'))
    check=ns['stage03_preexperiment_readiness']
    bad=check(None,None,'DENY_MISSING_REVIEW')
    assert bad['status']=='PREEXPERIMENT_INPUT_REJECTED'
    assert bad['new_research_authorized'] is False
    assert bad['development_experiment_authorized'] is False
    assert bad['orders_allowed'] is False
    assert bad['mt5_allowed'] is False
    assert bad['holdout_allowed'] is False


def test_preexperiment_nontrading_cost_gate_is_separate():
    """A first quote forecast needs source chronology, not broker fills."""
    check=runpy.run_path(str(A/'v57_independent_evidence_verifier_v2.py'))['stage03_preexperiment_readiness']
    packet=dict(kind='OMEGA_STAGE03_EXTERNAL_PREEXPERIMENT_REVIEW_HANDOFF_V1',
      status='READY_FOR_EXTERNAL_REVIEW_ONLY',instrument='BINANCE_COINM_BTCUSD_PERP',
      development_authorized=False,candidate_admitted=False,search_executed=False,
      backtest_executed=False,orders_allowed=False,mt5_allowed=False,
      holdout_allowed=False,auto_promotion_allowed=False)
    docs=dict(protocol=dict(kind='V57_PROSPECTIVE_CAUSAL_PROTOCOL_V1',
                            hypothesis_status='FORMULATED_FOR_REVIEW'),
      review=dict(status='PROTOCOL_REVIEW_REQUIRED_NOT_AUTHORIZED'),
      regimes=dict(instrument='BINANCE_COINM_BTCUSD_PERP'),
      temporal=dict(target='BTCUSD_PERP'),other_market=dict(),
      costs=dict(symbol='BTCUSD_PERP',reference_regular_fee_schedule=dict(account_fee_tier_verified=False)),
      live=dict(kind='OMEGA_STAGE03_COINM_WS_BOUNDED_ONE_SHOT_OBSERVATION_V1'),
      historical_quotes=dict(instrument='BINANCE_COINM_BTCUSD_PERP',
                             quotes_are_proven_received_at_decision_time=False,broker_fills_verified=False))
    out=check(packet,docs,'DENY_INDEPENDENT_REVIEW_AUTHORITY_NOT_PROVISIONED')
    assert out['status']=='PREEXPERIMENT_SCIENCE_BLOCKED'
    assert len(out['missing_prerequisites'])==7
    assert out['secondary_tradability_blockers']==['VENUE_ACCOUNT_COSTS_AND_EXECUTABLE_FILL_SEMANTICS']
    assert 'VENUE_ACCOUNT_COSTS_AND_EXECUTABLE_FILL_SEMANTICS' not in out['missing_prerequisites']
    assert out['experiment_scope']=='NONTRADING_NEXT_300S_MIDQUOTE_FORECAST_ONLY'
    assert out['development_experiment_authorized'] is False and out['orders_allowed'] is False
    packet['orders_allowed']=True
    assert check(packet,docs,'DENIED')['status']=='PREEXPERIMENT_INPUT_REJECTED'

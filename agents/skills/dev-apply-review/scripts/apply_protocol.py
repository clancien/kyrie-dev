#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# ///
"""Account for focused corrections and a simplified global closure.

Uses the full-review utility only for filesystem/hash primitives, never for
review policy, lenses or readiness. Semantic evidence is supplied by the agent.
"""
import argparse
import importlib.util
import json
from pathlib import Path
import shutil
import sys
from uuid import uuid4

SHARED = Path(__file__).resolve().parents[2] / 'dev-review-spec/scripts/review_protocol.py'
module_spec = importlib.util.spec_from_file_location('review_hashes', SHARED)
shared = importlib.util.module_from_spec(module_spec)
module_spec.loader.exec_module(shared)
require, read, write = shared.require, shared.read, shared.write
POLICY = 'apply-focused-v1'
STATES = ('active', 'ready', 'needs_user', 'incomplete_review', 'stalled', 'budget_exhausted')
DISPOSITIONS = ('open', 'applied', 'resolved', 'rejected', 'deferred')
RANK = {'minor': 0, 'major': 1, 'blocker': 2}


def findings_valid(findings):
    require(isinstance(findings, list), 'findings must be an array')
    keys = []
    for finding in findings:
        require(isinstance(finding, dict), 'finding must be an object')
        for field in ('key', 'finding', 'evidence'):
            shared.text_field(finding, field)
        require(finding.get('severity') in RANK, 'Invalid severity')
        shared.strings(finding.get('source_ids', []), 'source_ids')
        keys.append(finding['key'])
    require(len(keys) == len(set(keys)), 'Group observations by stable key')


def add_findings(state, findings):
    by_key = {d['key']: d for d in state['defects']}
    seen = set()
    for finding in findings:
        defect = by_key.get(finding['key'])
        if defect is None:
            defect = {'id': f"D{len(state['defects']) + 1}", 'key': finding['key'],
                      'severity': finding['severity'], 'state': 'open', 'history': []}
            state['defects'].append(defect)
            by_key[defect['key']] = defect
        # A currently substantiated finding reopens its defect. Refutations go
        # in checked_defects, not simultaneously in current findings.
        defect['severity'] = max(defect['severity'], finding['severity'], key=RANK.get)
        defect['state'] = 'open'
        defect['history'].append({'at': shared.now(), 'finding': finding})
        seen.add(defect['id'])
    return seen


def load_run(path):
    state = read(path)
    require(state.get('policy') == POLICY and state.get('schema_version') == 1,
            'Unsupported apply run; halt and explicitly migrate findings, history and consumed budget before resuming')
    require(state.get('status') in STATES, 'Invalid state')
    require(type(state['max_rounds']) is int and state['max_rounds'] > 0, 'Invalid round limit')
    require(0 <= state['rounds_used'] <= state['max_rounds'], 'Invalid round accounting')
    require(len(state['attempts']) == state['rounds_used'], 'Attempt accounting mismatch')
    return state


def init(document, review, snapshot_path, findings_path, max_rounds=3):
    require(max_rounds > 0, 'max_rounds must be positive')
    source = read(snapshot_path)
    shared.verify_snapshot(source)
    document = Path(document).resolve(strict=True)
    review = Path(review).resolve(strict=True)
    require(source['document'] == str(document), 'Snapshot is for another document')
    source_findings = read(findings_path)
    findings_valid(source_findings)
    folder = document.parent / '.reviews' / document.stem / ('apply-' + uuid4().hex)
    folder.mkdir(parents=True)
    shutil.copyfile(review, folder / 'input.review.md')
    metadata = review.with_suffix('.json')
    if metadata.exists():
        shutil.copyfile(metadata, folder / 'input.review.json')
    state = {'schema_version': 1, 'policy': POLICY, 'document': str(document),
             'snapshot': source, 'input_review': str(review), 'max_rounds': max_rounds,
             'rounds_used': 0, 'status': 'active', 'reason': 'Existing review ingested; no initial review',
             'defects': [], 'attempts': [], 'reports': [], 'events': []}
    add_findings(state, source_findings)
    path = folder / 'run.json'
    write(path, state, exclusive=True)
    return {'run': str(path), 'state': state}


def begin(path):
    state = load_run(path)
    require(state['status'] in ('active', 'needs_user', 'incomplete_review', 'stalled'), 'Run cannot begin repair')
    shared.verify_snapshot(state['snapshot'])
    require(state['rounds_used'] < state['max_rounds'], 'Repair budget exhausted')
    # Retries consume a new round even when a previous write was interrupted.
    state['rounds_used'] += 1
    state['attempts'].append({'number': state['rounds_used'], 'at': shared.now(), 'completed': False})
    state['status'], state['reason'] = 'active', 'Correction round consumed before writing'
    write(path, state)
    return state


def blocking(state):
    return [d for d in state['defects'] if d['severity'] != 'minor' and d['state'] not in ('resolved', 'rejected')]


def render(report):
    lines = ['# Verificación de aplicación de review', '',
             f"Política: {POLICY}; cobertura: {report['coverage']}",
             f"Estado: {report['run_status']}",
             'El cierre global es simplificado; no es una revisión de dev-review-spec.', '',
             '## Ámbito', '']
    lines.extend('- ' + path for path in report['scope'])
    lines.extend(['', '## Hallazgos vigentes', '', '| Severidad | Causa | Hallazgo | Evidencia |', '|---|---|---|---|'])
    for finding in report['findings']:
        lines.append('| ' + ' | '.join(shared.cell(finding[k]) for k in ('severity', 'key', 'finding', 'evidence')) + ' |')
    lines.extend(['', '## Disposiciones verificadas', '', json.dumps(report['checked_defects'], ensure_ascii=False, indent=2), '',
                  'Decisiones pendientes: ' + json.dumps(report['pending_decisions'], ensure_ascii=False),
                  'Fallos: ' + json.dumps(report['failures'], ensure_ascii=False)])
    if report['verdict']:
        lines.extend(['', 'Cierre: ' + report['verdict']])
    return '\n'.join(lines) + '\n'


def record(path, result_path, snapshot_path):
    state = load_run(path)
    result, source = read(result_path), read(snapshot_path)
    shared.verify_snapshot(source)
    require(source['document'] == state['document'], 'Snapshot is for another document')
    pending = bool(state['attempts'] and not state['attempts'][-1]['completed'])
    require(source['digest'] == state['snapshot']['digest'] or pending,
            'Changed contract requires consumed attempt or explicit external refresh')
    require(result.get('coverage') in ('focused', 'global'), 'Invalid coverage')
    require(result.get('status') in ('complete', 'incomplete'), 'Invalid verification status')
    for field in ('scope', 'pending_decisions', 'failures'):
        shared.strings(result.get(field), field)
    require(result['scope'], 'Verification scope required')
    scope = {str(Path(p).resolve()) for p in result['scope']}
    inventory = {f['path'] for f in source['files']}
    require(scope <= inventory, 'Scope contains files outside snapshot')
    complete = result['status'] == 'complete'
    require(not complete or not result['failures'], 'Complete verification cannot have failures')
    require(complete or result['failures'], 'Incomplete verification needs failure reason')
    if result['coverage'] == 'global' and complete:
        require(scope == inventory, 'Global closure must cover entire current inventory')
    if result['coverage'] == 'focused':
        require(pending, 'Focused verification requires a consumed correction round')
    findings_valid(result.get('findings'))
    known_ids = {d['id'] for d in state['defects']}
    seen = add_findings(state, result['findings'])
    checked = result.get('checked_defects')
    require(isinstance(checked, dict), 'checked_defects required')
    if result['coverage'] == 'global' and complete:
        require(known_ids <= set(checked), 'Global closure must recheck all prior defects')
    by_id = {d['id']: d for d in state['defects']}
    for identifier, decision in checked.items():
        require(identifier in by_id, 'Unknown defect')
        require(decision.get('state') in DISPOSITIONS, 'Invalid disposition')
        for field in ('reason', 'evidence'):
            shared.text_field(decision, field)
        require(not (identifier in seen and decision['state'] in ('resolved', 'rejected')),
                'Current finding contradicts resolution/refutation; correct triage first')
        require(decision['state'] != 'deferred' or by_id[identifier]['severity'] == 'minor',
                'Only minor findings may be deferred')
        by_id[identifier]['state'] = decision['state']
        by_id[identifier]['history'].append({'at': shared.now(), 'verification': decision})
    open_required = blocking(state)
    require(not result['pending_decisions'] or open_required,
            'Indispensable decision must be justified by an open major/blocker, not a minor preference')
    if not complete:
        status, reason = 'incomplete_review', '; '.join(result['failures'])
    elif result['pending_decisions']:
        status, reason = 'needs_user', 'Decision required by a major/blocker'
    elif result['coverage'] == 'global' and not open_required:
        status, reason = 'ready', 'Simplified global closure; zero open major/blocker'
    elif open_required and state['rounds_used'] >= state['max_rounds']:
        status, reason = 'budget_exhausted', 'Open major/blocker at correction limit'
    else:
        status, reason = 'active', 'Further correction or simplified global closure required'
    verdict = None
    if complete and result['coverage'] == 'global':
        verdict = 'NO LISTO' if open_required else ('LISTO CON OBSERVACIONES' if any(d['severity'] == 'minor' and d['state'] not in ('resolved', 'rejected') for d in state['defects']) else 'LISTO')
    index = len(state['reports'])
    output = Path(path).resolve().parent / f"check-{index:03d}.{result['coverage']}.json"
    report = {**result, 'policy': POLICY, 'snapshot': source, 'created_at': shared.now(),
              'run_status': status, 'verdict': verdict}
    write(output, report, exclusive=True)
    write(output.with_suffix('.md'), render(report), exclusive=True)
    state['reports'].append(str(output))
    state['snapshot'], state['status'], state['reason'] = source, status, reason
    if pending:
        state['attempts'][-1]['completed'] = True
    write(path, state)
    return state


def refresh(path, snapshot_path, reason):
    state = load_run(path)
    require(reason.strip(), 'External refresh reason required')
    require(not (state['attempts'] and not state['attempts'][-1]['completed']),
            'Record interrupted own correction before external refresh')
    source = read(snapshot_path)
    shared.verify_snapshot(source)
    require(source['document'] == state['document'], 'Snapshot is for another document')
    require(source['digest'] != state['snapshot']['digest'], 'No external change detected')
    state['snapshot'] = source
    state['status'], state['reason'] = 'active', 'External change: recheck affected scope and final closure'
    state['events'].append({'at': shared.now(), 'external_refresh': reason})
    write(path, state)
    return state


def stop(path, status, reason):
    require(status in STATES and status not in ('active', 'ready'), 'Invalid stop state')
    require(reason.strip(), 'Stop reason required')
    state = load_run(path)
    state['status'], state['reason'] = status, reason
    state['events'].append({'at': shared.now(), 'status': status, 'reason': reason})
    write(path, state)
    return state


def verify(path):
    state = load_run(path)
    shared.verify_snapshot(state['snapshot'])
    if state['status'] == 'ready':
        require(state['reports'] and not blocking(state), 'No verified ready closure')
        report = read(state['reports'][-1])
        require(report['coverage'] == 'global' and report['status'] == 'complete' and report['run_status'] == 'ready', 'Final global closure required')
        require(report['snapshot'] == state['snapshot'], 'Closure snapshot mismatch')
    return state


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    subs = parser.add_subparsers(dest='command', required=True)
    init_parser = subs.add_parser('init')
    init_parser.add_argument('target')
    init_parser.add_argument('--review', required=True)
    init_parser.add_argument('--snapshot', required=True)
    init_parser.add_argument('--findings', required=True)
    init_parser.add_argument('--max-rounds', type=int, default=3)
    for command in ('begin', 'verify'):
        subs.add_parser(command).add_argument('target')
    rec = subs.add_parser('record')
    rec.add_argument('target')
    rec.add_argument('--result', required=True)
    rec.add_argument('--snapshot', required=True)
    ref = subs.add_parser('refresh')
    ref.add_argument('target')
    ref.add_argument('--snapshot', required=True)
    ref.add_argument('--reason', required=True)
    halt = subs.add_parser('stop')
    halt.add_argument('target')
    halt.add_argument('--status', required=True)
    halt.add_argument('--reason', required=True)
    args = parser.parse_args()
    try:
        if args.command == 'init':
            result = init(args.target, args.review, args.snapshot, args.findings, args.max_rounds)
        elif args.command == 'record':
            result = record(args.target, args.result, args.snapshot)
        elif args.command == 'refresh':
            result = refresh(args.target, args.snapshot, args.reason)
        elif args.command == 'stop':
            result = stop(args.target, args.status, args.reason)
        else:
            result = globals()[args.command](args.target)
        print(json.dumps(result, ensure_ascii=False, allow_nan=False))
        return 0
    except (ValueError, OSError, KeyError, TypeError) as error:
        print(json.dumps({'error': str(error)}, ensure_ascii=False))
        return 1


if __name__ == '__main__':
    sys.exit(main())

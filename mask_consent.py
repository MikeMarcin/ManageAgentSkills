"""In-process consent for significant authority (RFC-MASK-0018, contract section 3).

A direct task command authorizes its ordinary scoped engine effects without a
question. When an operation needs genuinely new authority, the engine builds one
proposal, retains its plan hash inside the program and asks here. The answer is
gathered with no writer lock held; the caller reacquires the lock, recomputes the
proposal and refuses a stale hash before any effect (see ``mask.dispatch_impl``).

Kinds name the authority being asked for. ``--yes`` grants only ORDINARY kinds;
package scripts, new source identities, overwriting edited content, ref
rebinding and program contract migrations are never granted by ``--yes``. ``--expect-plan-hash``
grants exactly the frozen proposal it was produced for; NAMED kinds additionally
need every subject named by an exact ``--allow-setup SOURCE/ID:ACTION`` entry.
"""
from __future__ import annotations

import re
import sys

import mask_core as c

ORDINARY = {'readiness'}
SIGNIFICANT = {'readiness', 'source.trust', 'package.setup', 'overwrite', 'ref.rebind', 'program.migration'}
NAMED = {'package.setup'}
# Declining these leaves the rest of the task to proceed without that authority instead of aborting it.
CONTINUES_ON_DECLINE = {'package.setup'}
GRANT_RE = re.compile(r'[a-z0-9]+(?:-[a-z0-9]+)*/[a-z0-9]+(?:-[a-z0-9]+)*:[a-z0-9]+(?:-[a-z0-9]+)*')


class ConsentRequired(Exception):
    """Raised under the writer lock; the dispatcher releases the lock and asks."""

    def __init__(self, request):
        super().__init__(request['question'])
        self.request = request


def request(kind, reason, scope, actions, plan_hash, question, subjects=()):
    if kind not in SIGNIFICANT:
        c.fail('internal.invariant', 'Unknown consent kind.', 10, kind=kind)
    proposal = dict(kind=kind, reason=reason, scope=list(scope), actions=list(actions), plan_hash=plan_hash, question=question, granted_by=None)
    if kind in NAMED:
        proposal['subjects'] = list(subjects)
    return proposal


def interactive(args):
    """A human manual invocation on a usable terminal: never JSON, events or redirected streams."""
    if getattr(args, 'json', False) or getattr(args, 'event', 'manual') != 'manual':
        return False
    try:
        return all(stream is not None and stream.isatty() for stream in (sys.stdin, sys.stdout, sys.stderr))
    except (AttributeError, ValueError):
        return False


def named_grants(args):
    """Well-formed ``--allow-setup`` entries; a malformed entry names nothing."""
    return {entry for entry in getattr(args, 'allow_setup', None) or [] if isinstance(entry, str) and GRANT_RE.fullmatch(entry)}


def granted_by(args, proposal):
    """How this exact proposal is already authorized, or None."""
    consented = getattr(args, 'consented', None) or {}
    if proposal['kind'] in consented:
        if consented[proposal['kind']] != proposal['plan_hash']:
            c.fail('plan.stale', 'The proposal changed after consent; nothing was applied.', 4)
        return 'prompt'
    if getattr(args, 'expect_plan_hash', None) == proposal['plan_hash']:
        if proposal['kind'] not in NAMED:
            return 'expect-plan-hash'
        if proposal['subjects'] and set(proposal['subjects']) <= named_grants(args):
            return 'allow-setup'
        return None
    if getattr(args, 'yes', False) and proposal['kind'] in ORDINARY:
        return 'yes'
    return None


def require(args, output, proposal):
    """Return when the proposal is authorized; otherwise ask (interactive) or refuse with the typed proposal."""
    how = granted_by(args, proposal)
    if how is not None:
        output['data']['confirmation'] = dict(proposal, granted_by=how)
        return
    output['data']['confirmation'] = proposal
    if interactive(args):
        raise ConsentRequired(proposal)
    c.fail('confirmation.required', proposal['question'], 4, reason=proposal['reason'], kind=proposal['kind'])


def ask(proposal, text, *, details=None):
    """Show the proposal on stderr and read one default-no answer. EOF declines; Ctrl-C propagates."""
    import mask_present
    import mask_progress
    with mask_progress.paused():
        sys.stderr.write(mask_present.paint(text, sys.stderr, tone='review'))
        while True:
            choices = '[y/N] (d = details)' if details is not None else '[y/N]'
            sys.stderr.write(f"{proposal['question']} {choices} ")
            sys.stderr.flush()
            answer = sys.stdin.readline()
            if details is None or answer.strip().lower() != 'd':
                break
            sys.stderr.write(mask_present.paint(details, sys.stderr, tone='review'))
    if not answer:
        sys.stderr.write('\n')
    accepted = answer.strip().lower() in ('y', 'yes')
    if accepted:
        mask_progress.phase('Approved; rechecking the reviewed task')
    return accepted

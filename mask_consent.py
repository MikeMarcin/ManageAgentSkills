"""In-process consent for significant authority (RFC-MASK-0018, contract section 3).

A direct task command authorizes its ordinary scoped engine effects without a
question. When an operation needs genuinely new authority, the engine builds one
proposal, retains its plan hash inside the program and asks here. The answer is
gathered with no writer lock held; the caller reacquires the lock, recomputes the
proposal and refuses a stale hash before any effect (see ``mask.dispatch_impl``).

Kinds name the authority being asked for. ``--yes`` grants only ORDINARY kinds;
package scripts, new source identities, overwriting edited content, ref rebinding
and cross-consumer expansion are never granted by ``--yes``. ``--expect-plan-hash``
grants exactly the frozen proposal it was produced for.
"""
from __future__ import annotations

import sys

import mask_core as c

ORDINARY = {'readiness'}
SIGNIFICANT = {'readiness', 'source.trust', 'package.setup', 'overwrite', 'ref.rebind', 'scope.expand'}


class ConsentRequired(Exception):
    """Raised under the writer lock; the dispatcher releases the lock and asks."""

    def __init__(self, request):
        super().__init__(request['question'])
        self.request = request


def request(kind, reason, scope, actions, plan_hash, question):
    if kind not in SIGNIFICANT:
        c.fail('internal.invariant', 'Unknown consent kind.', 10, kind=kind)
    return dict(kind=kind, reason=reason, scope=list(scope), actions=list(actions), plan_hash=plan_hash, question=question, granted_by=None)


def interactive(args):
    """A human manual invocation on a usable terminal: never JSON, events or redirected streams."""
    if getattr(args, 'json', False) or getattr(args, 'event', 'manual') != 'manual':
        return False
    try:
        return all(stream is not None and stream.isatty() for stream in (sys.stdin, sys.stdout, sys.stderr))
    except (AttributeError, ValueError):
        return False


def granted_by(args, proposal):
    """How this exact proposal is already authorized, or None."""
    consented = getattr(args, 'consented', None)
    if consented is not None:
        if consented != proposal['plan_hash']:
            c.fail('plan.stale', 'The proposal changed after consent; nothing was applied.', 4)
        return 'prompt'
    if getattr(args, 'expect_plan_hash', None) == proposal['plan_hash']:
        return 'expect-plan-hash'
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


def ask(proposal, text):
    """Show the proposal on stderr and read one default-no answer. EOF declines; Ctrl-C propagates."""
    sys.stderr.write(text)
    sys.stderr.write(f"{proposal['question']} [y/N] ")
    sys.stderr.flush()
    answer = sys.stdin.readline()
    if not answer:
        sys.stderr.write('\n')
    return answer.strip().lower() in ('y', 'yes')

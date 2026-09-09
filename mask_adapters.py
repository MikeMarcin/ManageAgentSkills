"""Audited built-in adapter facts; data only, with no executable plugin loading.

Evidence boundary: docs/development/readiness-acceptance.md. Filesystem/native
prelaunch evidence is distinct from actual first-prompt host skill loading.
"""
from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType


@dataclass(frozen=True)
class Adapter:
    id: str
    project_path: str
    user_path: str
    project_config: str
    user_config: str
    reload: str
    gate: str
    reload_skills: bool
    stop_on_failure: bool
    reserved_names: tuple[str, ...]
    hazardous_components: tuple[str, ...]
    hazardous_files: tuple[str, ...]
    active_frontmatter: tuple[str, ...]
    dynamic_syntax: tuple[str, ...] = ()
    platform_evidence: tuple[tuple[str, str], ...] = ()
    evidence: str | None = None
    host_load: str = 'not_verified'
    host_gate_enforcement: str = 'not_verified'
    roles_path: str = ''
    role_suffix: str = ''

    def path(self, scope):
        if scope not in ('project', 'user'):
            raise ValueError('Unknown consumer scope')
        return self.project_path if scope == 'project' else self.user_path

    def config_path(self, scope):
        if scope not in ('project', 'user'):
            raise ValueError('Unknown consumer scope')
        return self.project_config if scope == 'project' else self.user_config

    def role_relative(self, scope, name):
        if scope not in ('project', 'user') or not self.roles_path:
            raise ValueError('Unsupported native role destination')
        return f'{self.roles_path}/{name}{self.role_suffix}'

    def describe(self):
        return dict(id=self.id, paths={scope: self.path(scope) for scope in ('project', 'user')},
                    native_roles=dict(path=self.roles_path or None, suffix=self.role_suffix or None, kind='native_role'),
                    startup_config={scope: self.config_path(scope) for scope in ('project', 'user')},
                    platforms=dict(self.platform_evidence),
                    discovery='directory_symlink', reload=self.reload, gate=self.gate,
                    host_load=self.host_load, host_gate_enforcement=self.host_gate_enforcement,
                    evidence=self.evidence,
                    reserved_names=list(self.reserved_names),
                    package_hazards=dict(components=list(self.hazardous_components), files=list(self.hazardous_files),
                                         frontmatter=list(self.active_frontmatter), dynamic_syntax=list(self.dynamic_syntax)))


BUILTINS = (
    Adapter('claude', '.claude/skills', '.claude/skills', '.claude/settings.local.json', '.claude/settings.json',
            'requested', 'warning', True, False, ('synced',), ('.claude', '.claude-plugin'),
            ('.mcp.json', 'mcp.json'), ('hooks', 'allowed-tools', 'mcp', 'mcpservers', 'mcp-servers', 'plugin', 'plugins'), ('!`', '```!'),
            platform_evidence=(('macos', 'native_readiness_recorded'), ('windows', 'native_readiness_recorded'), ('linux', 'best_effort_unverified')),
            evidence='docs/development/readiness-acceptance.md', roles_path='.claude/agents', role_suffix='.md'),
    Adapter('codex', '.agents/skills', '.agents/skills', '.codex/hooks.json', '.codex/hooks.json',
            'restart_may_be_required', 'documented_stop_unverified', False, True, ('synced',), ('.codex', '.agents', '.codex-plugin'),
            ('.mcp.json', 'mcp.json'), ('hooks', 'mcp', 'mcpservers', 'mcp-servers', 'plugin', 'plugins'),
            platform_evidence=(('macos', 'native_readiness_recorded'), ('windows', 'native_readiness_recorded'), ('linux', 'best_effort_unverified')),
            evidence='docs/development/readiness-acceptance.md', roles_path='.codex/agents', role_suffix='.toml'),
)
BY_ID = MappingProxyType({adapter.id: adapter for adapter in BUILTINS})
# Git and common plugin envelopes are refused regardless of the requested agent.
COMMON_COMPONENTS = frozenset({'.git'})
COMMON_FILES = frozenset({'.gitmodules'})
COMMON_SUFFIXES = (('hooks', 'hooks.json'),)
RESERVED_NAMES = frozenset(name for adapter in BUILTINS for name in adapter.reserved_names)
HAZARDOUS_COMPONENTS = COMMON_COMPONENTS | frozenset(name for adapter in BUILTINS for name in adapter.hazardous_components)
HAZARDOUS_FILES = COMMON_FILES | frozenset(name for adapter in BUILTINS for name in adapter.hazardous_files)
ACTIVE_FRONTMATTER = frozenset(name for adapter in BUILTINS for name in adapter.active_frontmatter)
DYNAMIC_SYNTAX = tuple(sorted({syntax for adapter in BUILTINS for syntax in adapter.dynamic_syntax}))


def paths(scope='project'):
    return {adapter.id: adapter.path(scope) for adapter in BUILTINS}


def relative(agent, scope, identifier):
    return BY_ID[agent].path(scope) + '/' + identifier


def role_relative(agent, scope, name):
    """Typed native-role destination: the built-in adapter, never the package, chooses the path."""
    return BY_ID[agent].role_relative(scope, name)


def capabilities():
    return [adapter.describe() for adapter in BUILTINS]


def passive_path(parts):
    names = tuple(part.casefold() for part in parts)
    return (not any(name in HAZARDOUS_COMPONENTS for name in names)
            and names[-1] not in HAZARDOUS_FILES
            and not any(names[-len(suffix):] == suffix for suffix in COMMON_SUFFIXES))

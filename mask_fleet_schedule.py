"""Opt-in scheduler entries confined to the current user's launchd or Task Scheduler."""
from __future__ import annotations

import csv
from datetime import datetime, timedelta
import os
from pathlib import Path
import plistlib
import re
import subprocess
import tempfile
from xml.etree import ElementTree as XML

import mask_core as c
import mask_fleet as fleet

TASK_NS = 'http://schemas.microsoft.com/windows/2004/02/mit/task'


def command(*argv):
    code, raw, err = c.contained_run(list(map(str, argv)), dict(os.environ, LC_ALL='C'), timeout=15,
                                     max_output=65536, max_error=16384, family='fleet.scheduler', name='Native scheduler')
    return code, raw, err


def require(*argv):
    code, raw, _ = command(*argv)
    if code:
        c.fail('fleet.scheduler_failed', 'The current-user scheduler refused the requested action.', 4)
    return raw


def windows_text(raw):
    if raw.startswith((b'\xff\xfe', b'\xfe\xff')):
        return raw.decode('utf-16')
    return raw.decode('utf-8-sig', errors='replace')


def user_id(platform):
    if platform == 'macos':
        if os.getuid() == 0:
            c.fail('fleet.scheduler_scope', 'Schedule fleet convergence as your ordinary user.', 4)
        return str(os.getuid())
    if platform == 'windows':
        answer = next(csv.reader([windows_text(require('whoami.exe', '/user', '/fo', 'csv', '/nh')).strip()]), [])
        if len(answer) != 2 or not re.fullmatch(r'S-1-[0-9-]+', answer[1]) or answer[1] == 'S-1-5-18':
            c.fail('fleet.scheduler_scope', 'Could not determine the ordinary Windows user SID.', 4)
        return answer[1]
    c.fail('fleet.scheduler_unsupported', 'Use foreground fleet sync --local on this platform.', 4)


def schedule_record(home, device, interval, argv):
    platform = fleet.local_platform()
    user = user_id(platform)
    name = 'com.mask.fleet.' + c.digest(dict(home=str(home), device=device['id'])).split(':')[1][:24]
    path = str(Path.home() / 'Library' / 'LaunchAgents' / (name + '.plist')) if platform == 'macos' else None
    return dict(schema_version=1, platform=platform, user=user, name=name, path=path,
                interval=interval, argv=argv)


def mac_plist(record):
    interval = record['interval']
    # Calendar firing coalesces during sleep. The runner's own next-run gate
    # suppresses duplicate interval/calendar firings and handles backoff.
    minutes = range(0, 60, (interval + 59) // 60)
    return plistlib.dumps(dict(Label=record['name'], ProgramArguments=record['argv'], RunAtLoad=True,
                               StartInterval=interval, StartCalendarInterval=[dict(Minute=minute) for minute in minutes],
                               ProcessType='Background'))


def mac_observe(record):
    path = Path(record['path'])
    c.parents_safe(Path.home(), path)
    kind = c.kind(path)
    if kind != 'missing' and (kind != 'file' or path.stat().st_size > 65536 or path.read_bytes() != mac_plist(record)):
        c.fail('fleet.scheduler_collision', 'The selected launchd file is not the exact owned definition.', 4)
    domain = 'gui/' + record['user']
    require('/bin/launchctl', 'print', domain)
    code, raw, error = command('/bin/launchctl', 'print', domain + '/' + record['name'])
    if code:
        if b'Could not find service' not in error + raw:
            c.fail('fleet.scheduler_failed', 'The launchd service could not be inspected.', 4)
        return kind == 'file', False
    observed = raw.decode('utf-8', errors='replace')
    if kind != 'file' or not any(line.strip() == 'path = ' + str(path) for line in observed.splitlines()):
        c.fail('fleet.scheduler_collision', 'The running launchd job does not match its owned file.', 4)
    return True, True


def win_definition(record):
    root = XML.Element('Task', version='1.4', xmlns=TASK_NS)

    def node(parent, name, text=None, **attrs):
        result = XML.SubElement(parent, name, attrs)
        result.text = text
        return result

    info = node(root, 'RegistrationInfo')
    node(info, 'Description', 'MASK fleet ownership ' + c.digest(record))
    node(info, 'URI', '\\' + record['name'])
    triggers = node(root, 'Triggers')
    schedule = node(triggers, 'TimeTrigger')
    repetition = node(schedule, 'Repetition')
    node(repetition, 'Interval', f"PT{record['interval']}S")
    node(schedule, 'StartBoundary', (datetime.now() + timedelta(minutes=1)).isoformat(timespec='seconds'))
    login = node(triggers, 'LogonTrigger')
    node(login, 'UserId', record['user'])
    principal = node(node(root, 'Principals'), 'Principal', id='CurrentUser')
    node(principal, 'UserId', record['user'])
    node(principal, 'LogonType', 'InteractiveToken')
    node(principal, 'RunLevel', 'LeastPrivilege')
    settings = node(root, 'Settings')
    node(settings, 'MultipleInstancesPolicy', 'IgnoreNew')
    node(settings, 'DisallowStartIfOnBatteries', 'false')
    node(settings, 'StopIfGoingOnBatteries', 'false')
    node(settings, 'StartWhenAvailable', 'true')
    node(settings, 'ExecutionTimeLimit', 'PT10M')
    execution = node(node(root, 'Actions', Context='CurrentUser'), 'Exec')
    node(execution, 'Command', record['argv'][0])
    node(execution, 'Arguments', subprocess.list2cmdline(record['argv'][1:]))
    return XML.tostring(root, encoding='utf-16', xml_declaration=True)


def win_observe(record):
    code, raw, err = command('schtasks.exe', '/Query', '/TN', record['name'], '/XML', '/HRESULT')
    if code:
        if code & 0xffffffff not in (2, 0x80070002) and 'cannot find the file specified' not in windows_text(err).lower():
            c.fail('fleet.scheduler_failed', 'Could not inspect the Windows scheduled task.', 4)
        return False, False
    try:
        observed = XML.fromstring(raw)
        expected = XML.fromstring(win_definition(record))
    except XML.ParseError:
        c.fail('fleet.scheduler_collision', 'The existing Windows task could not be verified.', 4)
    namespace = {'t': TASK_NS}
    fields = ('RegistrationInfo/Description', 'Actions/Exec/Command', 'Actions/Exec/Arguments',
              'Principals/Principal/UserId', 'Principals/Principal/LogonType', 'Principals/Principal/RunLevel',
              'Triggers/LogonTrigger/UserId')
    for field in fields:
        query = '/'.join('t:' + item for item in field.split('/'))
        if observed.findtext(query, namespaces=namespace) != expected.findtext(query, namespaces=namespace):
            c.fail('fleet.scheduler_collision', 'The existing Windows task differs from the owned execution definition.', 4)
    if len(observed.findall('t:Actions/*', namespace)) != 1 or len(observed.findall('t:Triggers/*', namespace)) != 2:
        c.fail('fleet.scheduler_collision', 'The existing Windows task contains foreign actions or triggers.', 4)
    return True, True


def observe(record):
    if record['user'] != user_id(record['platform']):
        c.fail('fleet.scheduler_scope', 'The scheduler record belongs to another native user.', 4)
    return mac_observe(record) if record['platform'] == 'macos' else win_observe(record)


def install(record):
    present, active = observe(record)
    if active:
        return
    if record['platform'] == 'macos':
        path = Path(record['path'])
        if not present:
            c.atomic_text(path, mac_plist(record).decode('utf-8'), None)
        require('/bin/launchctl', 'bootstrap', 'gui/' + record['user'], path)
    else:
        with tempfile.TemporaryDirectory(prefix='mask-fleet-task-') as temp:
            definition = Path(temp) / 'task.xml'
            definition.write_bytes(win_definition(record))
            require('schtasks.exe', '/Create', '/TN', record['name'], '/XML', definition)
    if not observe(record)[1]:
        c.fail('fleet.scheduler_failed', 'The reviewed native scheduler definition is not active.', 4)


def remove(record):
    present, active = observe(record)
    if not present:
        return
    if record['platform'] == 'macos':
        if active:
            require('/bin/launchctl', 'bootout', 'gui/' + record['user'] + '/' + record['name'])
        present, active = observe(record)
        if active:
            c.fail('fleet.scheduler_failed', 'The reviewed launchd job is still loaded.', 4)
        if present:
            Path(record['path']).unlink()
    else:
        require('schtasks.exe', '/Delete', '/TN', record['name'], '/F')
        if observe(record)[0]:
            c.fail('fleet.scheduler_failed', 'The reviewed Windows task is still registered.', 4)

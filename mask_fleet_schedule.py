"""Opt-in scheduler entries confined to the current user's launchd or Task Scheduler."""
from __future__ import annotations

import csv
from datetime import datetime, timedelta, timezone
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
    code, raw, error = command('/bin/launchctl', 'print', domain + '/' + record['name'])
    if code:
        if b'Could not find service' not in error + raw:
            c.fail('fleet.scheduler_failed', 'The launchd service could not be inspected.', 4)
        return kind == 'file', False
    observed = raw.decode('utf-8', errors='replace')
    if kind != 'file' or not any(line.strip() == 'path = ' + str(path) for line in observed.splitlines()):
        c.fail('fleet.scheduler_collision', 'The running launchd job does not match its owned file.', 4)
    return True, True


def windows_start_boundary():
    return (datetime.now(timezone.utc) + timedelta(minutes=1)).isoformat(timespec='seconds')


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
    node(schedule, 'StartBoundary', record['start_boundary'])
    repetition = node(schedule, 'Repetition')
    node(repetition, 'Interval', f"PT{record['interval']}S")
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


def duration_seconds(value):
    match = re.fullmatch(r'P(?:(\d{1,5})D)?(?:T(?:(\d{1,5})H)?(?:(\d{1,5})M)?(?:(\d{1,5})S)?)?', value)
    if match is None or not any(match.groups()):
        return None
    return sum(int(number or 0) * scale for number, scale in zip(match.groups(), (86400, 3600, 60, 1)))


def windows_schedule_matches(task, record, namespace):
    def setting(path, default=None):
        qualified = '/'.join('t:' + item for item in path.split('/'))
        return task.findtext(qualified, default, namespace)

    timer = 'Triggers/TimeTrigger/'
    login = 'Triggers/LogonTrigger/'
    try:
        starts = datetime.fromisoformat(setting(timer + 'StartBoundary')).astimezone(timezone.utc)
        expected = datetime.fromisoformat(record['start_boundary']).astimezone(timezone.utc)
    except (TypeError, ValueError, OverflowError):
        return False
    if starts != expected or duration_seconds(setting(timer + 'Repetition/Interval', '')) != record['interval']:
        return False
    if any(setting(prefix + 'Enabled', 'true') not in ('true', '1') for prefix in (timer, login, 'Settings/')):
        return False
    if any(duration_seconds(setting(prefix + 'ExecutionTimeLimit', 'PT72H')) != 72 * 3600 for prefix in (timer, login)):
        return False
    if any(setting('Settings/' + name, 'false') not in ('false', '0')
           for name in ('RunOnlyIfIdle', 'RunOnlyIfNetworkAvailable', 'WakeToRun')):
        return False
    if any(setting(path) is not None for path in (timer + 'EndBoundary', timer + 'Repetition/Duration',
                                                  login + 'StartBoundary', login + 'EndBoundary', login + 'Repetition')):
        return False
    if any(duration_seconds(setting(path, 'PT0S')) != 0 for path in (timer + 'RandomDelay', login + 'Delay')):
        return False
    if setting(timer + 'Repetition/StopAtDurationEnd', 'false') not in ('false', '0'):
        return False
    return (setting('Settings/MultipleInstancesPolicy', 'IgnoreNew') == 'IgnoreNew'
            and setting('Settings/StartWhenAvailable') in ('true', '1')
            and setting('Settings/DisallowStartIfOnBatteries') in ('false', '0')
            and setting('Settings/StopIfGoingOnBatteries') in ('false', '0')
            and duration_seconds(setting('Settings/ExecutionTimeLimit', '')) == 600
            and not setting('Actions/Exec/WorkingDirectory'))


def win_observe(record):
    code, raw, err = command('schtasks.exe', '/Query', '/TN', record['name'], '/XML', '/HRESULT')
    if code:
        if code & 0xffffffff not in (2, 0x80070002) and 'cannot find the file specified' not in windows_text(err).lower():
            c.fail('fleet.scheduler_failed', 'Could not inspect the Windows scheduled task.', 4)
        return False, False
    if 'start_boundary' not in record:
        c.fail('fleet.scheduler_collision', 'The existing Windows task has no recorded owned start boundary.', 4)
    try:
        try:
            observed = XML.fromstring(raw)
        except XML.ParseError:
            # schtasks may emit UTF-8 console bytes with its original UTF-16
            # declaration. Decode the transport before parsing its XML.
            observed = XML.fromstring(raw.decode('utf-8-sig'))
        expected = XML.fromstring(win_definition(record))
    except (XML.ParseError, UnicodeError):
        c.fail('fleet.scheduler_collision', 'The existing Windows task could not be verified.', 4)
    namespace = {'t': TASK_NS}
    fields = ('RegistrationInfo/Description', 'Actions/Exec/Command', 'Actions/Exec/Arguments',
              'Principals/Principal/UserId', 'Principals/Principal/LogonType', 'Principals/Principal/RunLevel',
              'Triggers/LogonTrigger/UserId')
    for field in fields:
        query = '/'.join('t:' + item for item in field.split('/'))
        default = 'LeastPrivilege' if field.endswith('/RunLevel') else None
        if observed.findtext(query, default, namespace) != expected.findtext(query, namespaces=namespace):
            c.fail('fleet.scheduler_collision', 'The existing Windows task differs from the owned execution definition.', 4)
    if len(observed.findall('t:Actions/*', namespace)) != 1 or len(observed.findall('t:Triggers/*', namespace)) != 2:
        c.fail('fleet.scheduler_collision', 'The existing Windows task contains foreign actions or triggers.', 4)
    if not windows_schedule_matches(observed, record, namespace):
        c.fail('fleet.scheduler_collision', 'The existing Windows task schedule differs from the owned definition.', 4)
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

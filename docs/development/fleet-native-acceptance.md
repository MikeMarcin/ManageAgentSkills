# Fleet transport native verification

Candidate `a46dd0d3ccab7920d5fdd77d71917d79c0514960` implemented the
[RFC-MASK-0012](../rfcs/RFC-MASK-0012-fleet-enrollment-and-transport.md)
transport. Qualification used synthetic MASK signing identities and disposable
MASK homes, source repositories and registered personal scopes. The Windows
host's existing SSH login and trusted host key were used with the owner's
authorization for this fixture run.

| Surface | Native runtime | Observation |
|---|---|---|
| macOS SSH | macOS 26.6.2, arm64, Python 3.15.0, Apple Git 2.50.1 | Actual SSH to an unprivileged, temporary high-port loopback `sshd`. Its configured PATH was `/usr/bin:/bin`. The reviewed absolute Python and MASK paths worked with spaces, an apostrophe and Unicode. |
| Windows SSH | Windows 11 build 26200, Python 3.14.7, Git 2.55.0.windows.3 | Actual strict OpenSSH to the authorized native host. The exact candidate archive was SHA-256 checked before extraction. The host used `bash.exe` as the OpenSSH default shell. Separate native subprocesses through `cmd.exe` and `powershell.exe` also preserved the fixed launcher's spaced Unicode arguments and binary signed response. |
| Local protocol and package fixtures | macOS and native Windows | The 12 identity, RPC and transport tests passed on both. These tests included malformed frames, exact Git reads from disposable bare repositories, signed forwarding, source-auth and forwarding-policy refusals, and injected partial local effects. Their mocked transports and subprocess cases are separate from the SSH results above. |

On both SSH paths, public enrollment preview and approval authenticated the
reviewed device and controller grant. `fleet ping` and `fleet capability` returned
matching signed results. Actual mismatched SSH host keys and deliberately
unavailable login credentials were refused. A local binding revocation also
refused the named peer. A malformed frame preserved the remote RPC's exit code
and wrote no stdout.

On both devices, a deliberately short transport timeout left the operation
unknown. A subsequent delivery repaired a missing managed fixture link.
The controller dropped the response stream and then recovered the durable
signed receipt by operation ID and digest. Repeating the original request
returned the same result. The separate fault-injection suite verified that a
partial local change required ordinary recovery before completion could be
reported.

The macOS listener stopped and its fixture root was removed. The Windows
candidate checkout, archives, fixture keys and state were removed. The local
qualification guard compared eight declared project, machine and SSH control
files and observed no byte changes. These checks exercised disposable enrollment
and filesystem reconciliation. Production rollout and offline catch-up are
tracked under RFC-MASK-0013.
## Two-device rollout and catch-up

Candidate `d1d87be996cd240d3cd23e11a82468b0a9b56adb` ran the same
controller CLI against distinct macOS 26.6.2 arm64 and native Windows 11
build 26200 devices. Windows received a disposable source archive with
verified SHA-256
`cf609c79d7d138041a01615f831d7f6d3fae4b999f182341e9117992f4ae3bde`.
The runtime versions matched the table above. The Mac endpoint was an
unprivileged high-port loopback listener. Both devices used disposable MASK
homes, separately generated device identities, explicitly mapped personal
scopes and an unrelated local pin. All Git publication used disposable bare
repositories. The GitHub-shaped fixture URL resolved through a local Git
adapter. Device delivery used actual host-key-pinned SSH.

| Public path | Operation | Observed result |
|---|---|---|
| `fleet install fleet-shared --mode tap --all-devices --scope user` | `d7a8b27b6715c1ee769a20be1767867b` | Both devices verified the same exact tap payload. |
| `fleet install URL --mode copy --into curated --all-devices --scope user` | `59d4c21a63ef18f2c45f6b81adae234e` | Both devices verified the curated copy. Its isolated Git commit omitted unrelated staged work and the authoring checkout stayed unchanged. |
| `fleet update fixture/fleet-shared --all-devices --scope user` with the Mac listener stopped | `163238a36813aee1bbd2e6bb6d674e28` | Exit 9. Windows returned an exact receipt and the Mac stayed queued. A newer approved update later superseded the queued Mac row. |
| Second `fleet update`, then `fleet sync --all` after restoring the Mac listener | `574980626a100ec2b2dca87115662a10` | Windows verified while the Mac stayed queued. Both verified the newest exact payload after sync, and the earlier Mac delivery remained superseded. |
| `fleet remove fixture/fleet-shared --all-devices --scope user` | `b38a08834e494ba62d06d921d093502e` | Both verified removal. Their local pins and the separate curated fleet contribution remained present. |
| Tap reinstall with a controlled Mac destination collision | `189e5e1cc33c25d14079d56675006481` | Exit 9. The Mac reported a blocker and retained the unmanaged marker. Windows returned a successful receipt. |

The latest approved desired digest was
`sha256:2a4ba31681ed9e0ac8f632f2ab38d2cb40fbda24e8673785ed1fe82153e5b2ae`.
Both devices verified the exact selected payload digest
`sha256:37e6fc9ee482c8e493e54471de634dcf175304673bde97102c587b613120195a`.
The Mac receipt operation was `5fb2a6fc336240928c8220da77489721` and Windows
was `059f14e285aa40d2bc5b5922a4dd093f`. The controller verified the signed
receipt, scope, desired digest and matching filesystem bindings for each.
No agent host loading was observed.

Native Windows also ran the foreground pull and scheduler-adapter tests
from the same archive. The macOS focused tests exercised the same public
foreground pull against separate desired and receipt repositories, and
injected scheduler operations verified ownership and disable behavior. Native
scheduler registration and removal remain open. The authorization for this
run covered disposable fixtures and existing SSH access.

The Mac listener stopped and its fixture root was removed. Windows checkout,
archives, keys and MASK fixture state were removed. The local qualification
guard compared eight declared live project, machine and SSH files and found
no byte changes.

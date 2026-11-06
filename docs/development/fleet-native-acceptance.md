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

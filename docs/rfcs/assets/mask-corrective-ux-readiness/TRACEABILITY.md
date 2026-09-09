# User correction to implementation evidence

| User concern | Required correction | RFC / implementation cards | Public cases |
|---|---|---|---|
| All output is JSON without --json | Human renderer, not pretty JSON; readable errors too | RFC18 AC02/03; MASK-0084 | C06–C12 |
| Simple operations require a long command sequence | Complete install/remove/list and update tasks | RFC18 AC01/05; MASK-0086/0087 | C01–C05, C16–C21 |
| Manual plan hashes and approvals leaked into the UX | Keep guards internally; consent within the operation | RFC18 AC04/06; MASK-0085 | C13–C15 |
| README is too complicated | Short executable everyday guide; reference material remains separate | RFC18 AC07/08; MASK-0091 | C21 and native terminal journey |
| ensure succeeded despite absent native roles | Declare/check the full prerequisite set and gate prelaunch | RFC19 AC01/06; MASK-0088/0090 | W01, W16–W22 |
| Role files should be checked in, not generated on every install | Shipped role assets and valid consumer-checked-in definitions | RFC19 AC02/03; MASK-0088 | W02–W05, W13–W15 |
| ensure should offer to run necessary scripts | Exact default-no consent, one-command execution and recheck | RFC19 AC04/05; MASK-0089 | W06–W12, W17 |
| Qualified tests missed the actual user state | No pre-rendered/registered acceptance fixture; real upstream handoff | Both RFCs AC08 plus RFC19 AC07; MASK-0083/0091/0092 | C01/C21, W01/W03/W19/W21/W22 |
| Inconsistent role identity at startup | Correct installed role set and explicit shared reporting handoff | RFC19 AC06/08; MASK-0090 and upstream handoff | W16/W19/W20; never infer effective execution from config |

MASK owns its engine/CLI and passive configured-state reporting. The shared skill
owns consistent role prompting and native dispatch preflight. No quota-saving
criterion or model-route change is smuggled into this corrective pack.

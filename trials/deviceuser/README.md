# Device User Capability Trials

This folder defines a device-user capability curriculum for a macOS device.

The goal is to teach simple reusable command-oriented capabilities that a user
typically needs when operating a device.

This curriculum follows these conventions:

* examples are macOS-specific and use concrete commands such as `open`,
  `pbcopy`, and `screencapture`
* the teaching examples are intentionally simple Python command wrappers
* each example function is always named `main`
* imports are placed inside `main`
* external dependencies are declared as inline metadata in the function
  signature using `__dependencies__`
* file-bearing device actions should prefer governed mount surfaces before
  invoking macOS brokers, so authored skills use `fs.read_mount`,
  `fs.write_mount`, or `fs.list_mount` instead of taking raw host paths
* for these examples, external dependencies are usually empty because the tasks
  can be solved with the standard library and device commands
* the executable relation must be stated in plain markdown paragraphs and
  bullets, not only in fenced code blocks, because markdown learning extracts
  encounters from text-bearing sections

Canonical teaching shape:

* function name: `main`
* signature: `main(target: str, *, __dependencies__: tuple[str, ...] = ()) -> dict[str, str]`
* imports are inside `main`
* command execution is stated directly, for example `subprocess.run(["open", target], check=True)`
* returned value is stated directly, for example `{"status": "opened", "target": target}`

The focus is not advanced application integration. The focus is bounded,
reusable, command-specific device actions.

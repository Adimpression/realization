# Realized Workstation Application

`realized-workstation-app-cli` is the installable entry package for launching
and operating the Realized workstation. It owns command syntax and dispatch;
the existing workstation application, runtime, shell, gRPC, and UI packages
own the behavior behind those commands.

```console
realized-workstation launch --root ./state/workstation --workspace "$PWD"
realized-workstation chat --root ./state/workstation
realized-workstation grpc-host --serve-root ./state/workstation
```

The command also accepts the historical `workstation-*` subcommand names for
compatibility. Importing this package does not move subject workflow,
governance, controller, model, or host-execution policy into the entry layer.

The package is also the executable composition root. `composition.py` binds the
concrete providers required by the workstation, while `runtime_controller.py`
adapts subject scope into an assembled controller state. Lower packages expose
contracts and implementations; neither module changes their behavior or owns
their policy. Optional exchange extensions, including external Markdown
learning, are installed here explicitly rather than activated by incidental
root-module import order.

The historical root `controller_entrypoints.py` and
`runtime_controller_api.py` paths remain compatibility surfaces during the
qualification period. New integrations should invoke `realized-workstation` or
import from `workstation.app.cli`.

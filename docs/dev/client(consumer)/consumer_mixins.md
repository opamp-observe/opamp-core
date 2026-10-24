# Consumer Mixins Explained

This document explains how mixins are used in the consumer and how method dispatch works in practice.

## What a mixin is

A mixin is a class that contributes behavior to another class through inheritance, without being a full standalone domain model.

In this project, mixins are used to keep `fluentbit/client.py` and `abstract_client.py` smaller by separating large behavior groups into focused files.

## Where mixins are used

`AbstractOpAMPClient` is defined as:

```python
class AbstractOpAMPClient(
    ClientTransportAuthorizationMixin,
    ClientRuntimeMixin,
    ServerMessageHandlingMixin,
    OpAMPClientInterface,
    ABC,
):
    ...
```

The mixins are:

- `ClientTransportAuthorizationMixin` in `consumer/src/opamp_consumer/client_transport_auth_mixin.py`
- `ClientRuntimeMixin` in `consumer/src/opamp_consumer/client_runtime_mixin.py`
- `ServerMessageHandlingMixin` in `consumer/src/opamp_consumer/client_server_message_mixin.py`

Compatibility re-export module:

- `consumer/src/opamp_consumer/client_mixins.py`

## Runtime lifecycle strategies

`ClientRuntimeMixin` now delegates process lifecycle operations to strategy classes selected from configuration:

- `ClientSupervisorMixin` in `consumer/src/opamp_consumer/client_supervisor_mixin.py`
- `ClientObserverMixin` in `consumer/src/opamp_consumer/client_observer_mixin.py`

Selection behavior:

- `consumer.processTracking` values:
  - `Supervisor` (default)
  - `Observer`
- Observer mode requires `consumer.processDetectionRegex`

## What each mixin owns

`ClientTransportAuthorizationMixin` owns outbound transport/auth behavior:

- transport send orchestration (`send`, `send_http`, `send_websocket`)
- auth header resolution (`none`, `env-var`, `config-var`, `idp`)
- retry-on-auth-failure behavior for `401`/`403`

`ClientRuntimeMixin` owns runtime/process and polling behavior:

- lifecycle delegation (`launch_agent_process`, `terminate_agent_process`, `restart_agent_process`)
- local status polling (`poll_local_status_with_codes`)
- version discovery (`add_agent_version`)
- heartbeat loop (`_heartbeat_loop`)
- explicit awaited shutdown (`send_disconnect`, `finalize_async`)
- synchronous compatibility shutdown (`finalize`)

Callers already running an event loop should await `finalize_async()` so the
disconnect attempt finishes before shutdown continues. Synchronous callers can
use `finalize()`, which runs cleanup directly when no loop exists and schedules
it on the caller's active loop otherwise. Object destruction only disables the
local heartbeat flag; it does not start network I/O or a background thread.

`ServerMessageHandlingMixin` owns provider message handling:

- top-level dispatch (`_handle_server_to_agent`)
- reply validation (`_validate_reply_instance_uid`)
- handlers for server payload sections (`handle_*`)
- custom message dispatch to registered handlers (`handle_custom_message`)

`AbstractOpAMPClient` keeps cross-cutting client responsibilities:

- runtime data model setup (`OpAMPClientData`)
- full update controller wiring
- agent description/capability assembly helpers
- custom-handler registry setup

## How method resolution works

Python looks for methods in MRO order (Method Resolution Order). For `OpAMPClient`, that order starts:

1. `OpAMPClient`
2. `AbstractOpAMPClient`
3. `ClientTransportAuthorizationMixin`
4. `ClientRuntimeMixin`
5. `ServerMessageHandlingMixin`
6. `OpAMPClientInterface`
7. `ABC`
8. `object`

Practical impact:

- `send()` resolves in `ClientTransportAuthorizationMixin`.
- `_heartbeat_loop()` resolves in `ClientRuntimeMixin`.
- `_handle_server_to_agent()` resolves in `ServerMessageHandlingMixin`.

## How runtime strategy dispatch works

When `ClientRuntimeMixin.launch_agent_process()` is called:

1. runtime mixin resolves lifecycle strategy lazily (`_runtime_lifecycle()`).
2. strategy is selected from `config.process_tracking`:
   - `supervisor` -> `ClientSupervisorMixin`
   - `observer` -> `ClientObserverMixin`
3. runtime mixin delegates the call to that strategy instance.

Lifecycle selection is cached per client instance.

## Why this refactor helps

- keeps each file focused and easier to review
- cleanly separates transport/auth, runtime lifecycle, and server-message handling
- enables two process-management modes without branching every runtime method
- reduces merge conflict pressure in one large concrete client module
- provides clear extension points for additional lifecycle strategies

## Related files

- `consumer/src/opamp_consumer/abstract_client.py`
- `consumer/src/opamp_consumer/client_transport_auth_mixin.py`
- `consumer/src/opamp_consumer/client_runtime_mixin.py`
- `consumer/src/opamp_consumer/client_supervisor_mixin.py`
- `consumer/src/opamp_consumer/client_observer_mixin.py`
- `consumer/src/opamp_consumer/client_server_message_mixin.py`
- `consumer/src/opamp_consumer/client_mixins.py`
- `consumer/src/opamp_consumer/fluentbit/client.py`
- `consumer/src/opamp_consumer/fluentd/client.py`

# ClawOS Initial Provisioning (0.1.1 integration candidate)

This is a one-time device workflow used before Runtime OTA can be tested.

## Inputs

1. Stable `bootstrap.lua` is placed outside the versioned Runtime tree.
2. A complete ClawOS source tree is copied to a temporary writable device directory.
3. `provision/install_initial.lua` is run as a system script with:

```text
args.source_root = <temporary ClawOS source directory>
```

## Transaction

```text
source_root
  -> clawos-runtime/staging/provision-0.1.1
  -> copy explicit Runtime file list
  -> loadfile() syntax-check every Lua file
  -> rename to clawos-runtime/releases/0.1.1
  -> write state.json.provisioning
  -> rename to state.json
  -> active_version = 0.1.1
```

The script refuses to run when `state.json`, `releases/0.1.1`, or the provisioning staging directory already exists. It never overwrites an installed Runtime.

## Verification

Run:

```text
tests/runtime_provision_check.lua
```

Expected output:

```text
runtime_provision_check: PASS active=0.1.1 ...
```

Then run the stable `bootstrap.lua`.

## OTA device smoke

Existing devices with the immutable 0.1.0 release must receive this integration candidate through a published 0.1.1 Runtime OTA manifest. Do not rerun initial provisioning or overwrite the 0.1.0 directory. After staging, verify pending 0.1.1, boot the candidate, and confirm active 0.1.1. The update server and device checklist provide the release validation steps.

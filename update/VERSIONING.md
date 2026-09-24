# ClawOS Runtime Versioning Specification v1


This file is the canonical server-side version-number policy for ClawOS Runtime releases. Device-side validation in `core/runtime_version.lua` MUST implement the same rules.


## 1. Canonical format


Allowed formats are exactly:


```text
MAJOR.MINOR.PATCH
MAJOR.MINOR.PATCH-dev.N
MAJOR.MINOR.PATCH-beta.N
MAJOR.MINOR.PATCH-rc.N
```


Examples:


```text
0.1.0
0.1.1
0.2.0-dev.1
0.2.0-beta.1
0.2.0-rc.1
1.0.0
```


Rules:


- MAJOR, MINOR and PATCH are decimal non-negative integers.
- Numeric fields MUST NOT contain leading zeros except the value `0`.
- Pre-release sequence `N` starts at 1 and MUST NOT contain leading zeros.
- Only `dev`, `beta`, and `rc` pre-release tags are allowed.
- A stable release has no suffix.
- Prefix `v` is forbidden.
- Build metadata such as `+20260922` is forbidden in v1.
- Dates and timestamps are not version numbers.
- Version is always a string, never a float.
- Maximum version-string length is 32 characters.


Valid:


```text
0.1.0
0.1.10
0.2.0-dev.1
0.2.0-beta.12
0.2.0-rc.3
1.0.0
```


Invalid:


```text
v0.1.0
0.01.0
0.1
0.1.0-alpha.1
0.1.0-beta
0.1.0-beta.0
0.1.0-beta.01
0.1.0+build.4
2026.09.22
latest
```


## 2. Channel mapping


The manifest `channel` MUST exactly match the version suffix:


| channel | version form |
|---|---|
| stable | `X.Y.Z` |
| rc | `X.Y.Z-rc.N` |
| beta | `X.Y.Z-beta.N` |
| dev | `X.Y.Z-dev.N` |


A server MUST reject a manifest such as `channel=stable, version=0.2.0-beta.1`.


## 3. Ordering


Compare MAJOR, then MINOR, then PATCH numerically.


For the same MAJOR.MINOR.PATCH base:


```text
dev.N < beta.N < rc.N < stable
```


Within the same prerelease channel, N compares numerically.


Example:


```text
0.2.0-dev.1
<
0.2.0-dev.2
<
0.2.0-beta.1
<
0.2.0-rc.1
<
0.2.0
<
0.2.1
```


Do not compare version strings lexically.


## 4. Meaning of MAJOR / MINOR / PATCH


Before ClawOS 1.0:


- PATCH: bug fix only, no intentional public API break.
- MINOR: new feature; may include an explicitly documented pre-1.0 breaking API change.
- MAJOR remains 0 until the Runtime/App API is declared stable.


After ClawOS 1.0:


- PATCH: backward-compatible bug fix.
- MINOR: backward-compatible feature.
- MAJOR: breaking public Runtime/App API or incompatible persisted-state format.


## 5. Promotion


Promotion never edits an already published release.


Example:


```text
0.2.0-dev.7
0.2.0-beta.1
0.2.0-beta.2
0.2.0-rc.1
0.2.0
```


Each item above is a distinct immutable release.


## 6. Server publication rules


The release server MUST enforce all of the following:


1. A published version is immutable.
2. A version string can be published only once for the same product + board.
3. The same `release_id` can never be reused.
4. Re-uploading different files under an existing version is forbidden.
5. Fixing a bad release requires a new version.
6. The `latest` pointer for a channel can only move forward according to the ordering rules.
7. Automatic update responses MUST NOT offer a version less than or equal to the device's current version.
8. Rollback does not publish an older version as latest; rollback is device-local using `previous_version`.
9. Server time/order never overrides semantic version precedence.
10. Deleted/deprecated releases may stop being offered, but their version identity must never be reassigned.


## 7. release_id


Canonical format:


```text
clawos:<board>:<version>
```


Example:


```text
clawos:esp-mosaico:0.1.1
clawos:esp-mosaico:0.2.0-beta.1
```


Manifest rule:


```text
release_id == product + ":" + board + ":" + version
```


## 8. Release manifest minimum version fields


Required:


```json
{
  "schema": 1,
  "product": "clawos",
  "board": "esp-mosaico",
  "channel": "stable",
  "version": "0.1.1",
  "release_id": "clawos:esp-mosaico:0.1.1",
  "min_bootstrap": "0.1.0"
}
```


`min_bootstrap` uses the same version grammar.


## 9. Server latest API behavior


Recommended query:


```text
GET /v1/clawos/releases/latest?board=esp-mosaico&channel=stable&current=0.1.0
```


Server behavior:


- Return the newest compatible release only when `version > current`.
- Return no-update when there is no newer compatible release.
- Never use the literal string `latest` as a version.
- Device MUST still validate the returned manifest with `core/runtime_version.lua`.


## 10. Hotfix examples


Current stable:


```text
0.1.3
```


Bug fix:


```text
0.1.4
```


New feature:


```text
0.2.0
```


Release candidate for the feature:


```text
0.2.0-rc.1
```


A bad `0.1.4` is never replaced in place. Publish `0.1.5`.
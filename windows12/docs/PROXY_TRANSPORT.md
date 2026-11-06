# Managed proxy transport for the builder guest

Network-enabled command execution can reach the inherited proxy and Debian
metadata. Ordinary restricted command execution could not open the proxy socket;
that earlier curl 7 result did not establish a broken upstream service. Keep the
configured proxy and TLS trust. No direct-route or alternative-origin fallback
is used.

The previous controller translated only `localhost` and `127.0.0.1` proxy
addresses. This environment supplies an HTTP proxy named `proxy`, so the guest
would receive no proxy configuration or build CA. `scripts/guest-proxy.py` now
exposes that same configured proxy through an ephemeral listener bound only to
host `127.0.0.1`; QEMU user networking reaches it through `10.0.2.2`. The relay
forwards bytes unchanged to the one configured upstream host and port. It does
not resolve requested HTTP destinations, terminate guest TLS, log payloads, or
provide another egress route.

The helper bounds concurrent connections, connection and idle timeouts, preserves
TCP half-closes, and closes its listener and connections on shutdown. Existing
localhost proxy mapping is retained. Unsupported proxy schemes, credential-bearing
URLs, paths and queries fail before a fresh builder disk is created. Provenance
records the mode, upstream host/port and helper hash, without request contents or
credentials. The controller injects the configured public build CA as before;
the target-image cleanup and final ISO leakage audit remain required.

## Verification

The first current-source disposable guest passed all 36 tests and built preview4
twice identically. This includes five proxy tests covering exact bytes and
half-close handling, malformed URLs, localhost mapping, connection limits and
active shutdown. Evidence:
`artifacts/overlay-check-29ef3917036e8e6e483675c9ed5ba943/`.

Package: `windows12-desktop_0.1.0~preview4_all.deb`, 9,970 bytes,
SHA256 `cf4652f5ef2054388a6377e908c2673c78a7c003cee9362e003a9c61f4aa8075`.
Guest shutdown was confirmed. Package inspection passed; no desktop GUI or ISO
claim follows from these tests. The welcome page now describes the optional
Windows Applications entry without implying validated Windows app support.

An operational host HTTPS request through the relay returned 200 with normal
TLS verification. To check the actual guest path explicitly, use:

```bash
python3 -B scripts/check-overlay-vm.py --probe-proxy --timeout 900
```

This optional mode requires the cached authenticated tools and pinned cloud input,
the inherited proxy, and its configured public `CODEX_PROXY_CERT`. The default
checker remains an offline check using cached inputs. Probe mode fetches at most
512 KiB from the fixed Debian trixie InRelease URL through the relay, refuses
redirects, verifies TLS with the public build CA, and verifies the Debian archive
signature using the guest's installed verifier/keyring. It then executes the
ordinary guest tests and deterministic package checks. There is no package
installation. Results distinguish this metadata proof from a complete native APT
transaction and full image construction.

The explicit guest probe also passed in
`artifacts/overlay-check-56926e9e1c18e27f16c827b57d458590/`: TLS and the Debian
archive signature verified, all 36 tests passed, and the package digest remained
identical. Metadata SHA256:
`0584fba32e13e0ab8285fb16c27adea1ec03a73669c18702821094fd6ca86675`.
The guest stopped successfully. A subsequent host-only provenance refinement
records the hash of the bytes actually compiled rather than rereading the helper.

## Storage prerequisite

The current filesystem has only 7.84 GiB total capacity. The existing disposable
installation gate requires at least 8 GiB free, while build/export and ISO audit
need additional simultaneous storage. The user is arranging an expansion to
40+ GiB. Do not lower release gates or the storage monitor's 6 GiB safeguard to
fit the smaller filesystem. Reconcile actual capacity, workers and locks before
launching the full fresh build.

The fresh-build controller now refuses less than 8 GiB free before dependency
access or disk creation. This is a minimum refusal threshold, not a promise that
8 GiB can hold a full build. Preparation/probe and retained-disk recovery remain
available; they must retain their own job/storage guards.

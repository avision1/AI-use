# Verified guest package cache delivery

`build/import-package-cache.py` imports the reviewed missing-archive plan into the retained target cache. It requires root and the regular, single-link `/run/windows12-build-vm` marker inside the contained builder VM. It never invokes APT, dpkg, live-build, mount, recovery or install stages. The controller owns VM isolation, fresh boot, job exclusion, delivery-server lifecycle, plan review and subsequent native APT verification. Do not execute this helper on the host.

Inside the already contained, quiescent guest:

```
python3 -B /root/windows12-checks/build/import-package-cache.py \
  --nonce FRESH_IMPORT_32_LOWERCASE_HEX \
  --plan-nonce ORIGINAL_PLAN_32_LOWERCASE_HEX \
  --manifest-sha256 REVIEWED_PLAN_64_LOWERCASE_HEX
```

The nonce arguments must differ. Exclusive `/project-output/package-cache-import-NONCE` and `/root/windows12-build/package-cache-staging-NONCE` directories consume the import nonce. A preexisting top-level `/project-output/package-cache-import.json` is refused before import; preserve/export prior evidence and explicitly manage that lifecycle before another run. No helper action removes prior reports, staging files, existing target entries, locks or stage flags.

## Fixed local delivery contract

The only manifest URL is `http://10.0.2.2:8765/package-plan.json`; the only archive URL form is `http://10.0.2.2:8765/package-cache/SHA256.deb`. There are no URL, host, port, proxy or destination override arguments. The explicit opener disables environment proxies and all redirects. Remote Debian URLs in the manifest are evidence strings and are never fetched by this helper. The controller must expose only the intended reviewed manifest and verified content-addressed cache on that local server; general host forwarding is outside this helper's authority.

The manifest is capped at 2 MiB and must match the explicitly supplied SHA256 before JSON is accepted. Duplicate JSON members, wrong schema/purpose/plan nonce, duplicate archive names, conflicting digest sizes and unsafe basename strings are refused. Schema 1 requires `planning_only: true`; each planned archive has exactly `url`, `filename`, `size`, `sha256`, `package`, and `version`. Safe ASCII basenames retain Debian `+`, `%`, epoch `:`, and `~` spellings. Limits are 4,096 archives, 512 MiB per archive and 8 GiB aggregate. Each transfer also has a 30-second socket timeout and a checked 600-second elapsed limit.

## State preservation and publication

The helper validates only fixed build-root provenance locations: target status/extended state, target APT configuration, build configuration and stage files. It requires the retained 19 empty stage flags, enumerates the complete planned configuration/stage membership, and checks the package queue, Debian archive keyring, retained signed InRelease bytes and compressed index bytes against the reviewed plan. Hook symlinks are permitted only at the exact exporter-reviewed configuration paths, with exact pinned upstream target literals and target SHA256; other aliases are refused. The keyring path is restricted to the real regular `/usr/share/keyrings/debian-archive-keyring.pgp` or `/usr/share/keyrings/debian-archive-keyring.gpg` file; aliases remain refused. Signed-catalog verifier evidence is retained planning metadata and is not executed during import. It does not independently rerun signature verification: trust is the controller-approved exact manifest hash and unchanged catalog/keyring bytes from the signature-verified planning pass.

Pre-import cache inventory records file metadata and SHA256, including existing archives omitted by APT's missing-archive plan and any partial subtree. Symlinks, hardlinks and special files are refused. Bounds apply to inventory entry counts and bytes. Existing planned filenames are accepted only at their exact planned size and SHA256; conflicting existing bytes cause refusal without replacement. All unlisted existing entries must compare unchanged after import.

A missing archive downloads into an exclusive staging file contained under the guest build root. Exact received size/SHA256, fsync, root ownership, mode 0644 and a single regular-file link are required. Canonical ancestry and content are checked around publication. Linux `renameat2(RENAME_NOREPLACE)` publishes atomically without replacing an existing filename or creating hardlinks; unsupported publication semantics fail closed. Source and destination directories are fsynced. Target provenance/catalog bytes are fully hashed before import and after all publications. Stable device/inode/size/mtime/ctime/mode/owner/link-count identities and canonical ancestry are cheaply checked around each publication. This avoids rehashing all catalogs per archive. Added configuration members or byte changes are detected by the final full provenance check; races between point-in-time checks still require controller-enforced quiescence. A bounded `/proc` package/build-process scan and target mount check also refuse a nonquiescent build. These point-in-time checks supplement the controller's fresh-boot/exclusive-job requirement; they are not a concurrency lock.

## Evidence and failure

Atomic, fsynced `/project-output/package-cache-import.json` and a nonce-specific `report.json` checkpoint include import nonce, original plan nonce, exact manifest SHA256, cache inventories, and each planned file's expected SHA256 and delivery status. Reports are capped at 32 MiB. `import_performed` becomes true only after every planned archive and preservation check succeeds. `native_apt_verified` and `installation_verified` always remain false.

A failure checkpoints available state and leaves any already published verified archives intact. There is no rollback, cache deletion or automatic retry; failed or interrupted staging bytes remain in their nonce directory. The next explicitly authorized run must use a fresh import nonce and review existing evidence. A process crash or disk failure can prevent a final checkpoint; inspect the retained filesystem and previous report before proceeding. Import success does not certify package installation, native APT authentication, live-build recovery or ISO success.

Source authoring validation: AST parsing only. No helper/module execution, VM launch, host test suite, package installation or native APT verification was performed by the source-authoring agent. Independent source review and contained guest runtime validation remain required.

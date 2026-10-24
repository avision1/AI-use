# Cloud image authentication research

Owner `/root/release_inputs`; W12-008 bounded research, 2026-10-24. Only this document was modified. All work remained within `/workspace/scratch/3c38ab731138/AI-use/windows12/`; HTTP bodies were examined in memory/stdout with project-local HOME/TMP/XDG/GNUPGHOME. No packages were extracted or installed, no GnuPG verification was run, and no VM/device/source/lock/Git operation was performed. The current builder is unchanged.

## Result

**The exact pinned cloud release does not publish a detached checksum signature in its directory listing.** Its conventional `SHA512SUMS.sign` and `SHA512SUMS.gpg` URLs both returned HTTP404. Debian's current official cloud index explains that current per-distribution images use TLS/checksum delivery, distinguishes legacy OpenStack signatures, and invites checksum-signing contributions. [1][2]

No authorized cloud-signing fingerprint or applicable detached signature was established. Therefore detached-signature verification of this existing cloud input cannot be completed simply by installing a keyring. This is an upstream availability blocker under the presently documented distribution scheme, not evidence that this project's wrapper forgot a known signature file. No broader claim that every possible out-of-band signature is absent is made.

Do not apply Debian CD/live ISO signing keys to the cloud manifest, create a local signature and call it an upstream signature, substitute legacy OpenStack signatures, disable TLS, or restart the running build to pursue this unavailable file. The existing assurance remains **official HTTPS retrieval plus a pinned manifest digest and image SHA512**, exactly as the tracked lock says. DNSSEC validation by this environment was not established; the upstream recommendation is not proof that this project's resolver performed it.

## Direct primary-source observations

HTTP research completed successfully through the normal TLS-verifying curl path; no `-k`/insecure flag or custom trust replacement was used. HTTP bodies were not preserved as separate files by this task; these hashes describe the bytes observed, not signed attestations.

| URL | HTTP | Body bytes | SHA256 | Relevant observation |
|---|---:|---:|---|---|
| `https://cloud.debian.org/images/cloud/` | 200 | 10582 | `91b99e3a3717377c236d4a758be55310c6430ed4524840ca80cd67703fc828af` | Current official index documents TLS/DNSSEC recommendation; separates legacy signatures from current images. |
| `https://cloud.debian.org/images/cloud/trixie/20261021-2638/` | 200 | 20620 | `a53594675f89a87608671194f4d376f63d0edc309f6faf3a124dc6d2b1be716a` | Actual listing includes SHA512SUMS and dated genericcloud image/JSON/raw/tar files; no signature link (`.sign`, `.gpg`, `.sig`). |
| `https://cloud.debian.org/images/cloud/trixie/20261021-2638/SHA512SUMS.sign` | 404 | 317 | `003785ff824667d7c50029de1554ca6a22ab7701cad753671646973b6461db27` | Conventional Debian detached-signature URL is not available. |
| `https://cloud.debian.org/images/cloud/trixie/20261021-2638/SHA512SUMS.gpg` | 404 | 317 | `003785ff824667d7c50029de1554ca6a22ab7701cad753671646973b6461db27` | Alternative conventional URL also unavailable. |

The web retrieval tool could not fetch the cloud directory; the direct read-only HTTP check above supplied the actual evidence. Historical mailing-list text and third-party mirror copies helped locate the issue but are not the basis for current directory assertions.

## What the Ubuntu keyring route can and cannot do

Canonical's official Noble file list for `debian-keyring` includes `/usr/share/keyrings/debian-role-keys.gpg`. [4] Debian's current **CD/installation/live ISO** verification guide instead refers to `debian-role-keys.pgp` in current Debian packaging; do not assume the filename across versions. [3]

An authenticated Ubuntu package chain could establish the bytes of its packaged keyring: trusted Ubuntu archive keyring -> verified InRelease -> exact Packages index SHA256 -> selected debian-keyring archive SHA256 -> extracted role-keyring bytes. It would still require an applicable detached signature and an independently authorized image-signing fingerprint. This task did not fetch/extract that package or audit the keyring's members, so it makes **no claim that it contains a current cloud key**. Package availability in the tool bootstrap's current main-only indexes was not checked; adding an unauthenticated package URL is not an acceptable shortcut.

For contrast, Debian's CD verification page authorizes these identities for its own media, not this cloud manifest: [3]

- `10460DAD76165AD81FBC0CE9988021A964E6EA7D` — Debian CD signing key.
- `DF9B9C49EAA9298432589D76DA87E80D6294BE9B` — Debian CD signing key.
- `F41D30342F3546695F65C66942468F4009EA8AC3` — Debian Testing CDs automatic signing key.

A keyserver result, matching short key ID, or a successful signature made by an unrelated key would not close the cloud-input assurance gap.

## Concrete verification plan for the existing input

The current wrapper already implements manifest/image digest verification. Preserve those checks and the original manifest/image, then record any rerun as checksum verification, never detached-signature verification. This proposed command is read-only and has **not** been run by this research task; execute only after parent review, from `AI-use/windows12`, with the runbook's project-local environment:

```sh
python3 -B - <<'VERIFY'
from pathlib import Path
import hashlib, json, re
root = Path.cwd().resolve()
lock = json.loads((root / 'build/builder-image.lock.json').read_text())
work = root / '.work/builder'
manifest = work / 'pinned-SHA512SUMS'
image = work / lock['filename']
legacy = work / lock['legacy_cache_name']
if not image.exists() and legacy.exists():
    image = legacy
for path in (manifest, image):
    if path.is_symlink() or not path.resolve().is_relative_to(root) or not path.is_file():
        raise SystemExit('Unexpected cached input path')
if hashlib.sha256(manifest.read_bytes()).hexdigest() != lock['manifest_sha256']:
    raise SystemExit('Pinned manifest mismatch')
entries = [line.split() for line in manifest.read_text().splitlines()]
matching = [parts for parts in entries if len(parts) == 2 and parts[1] == lock['filename']]
if len(matching) != 1 or matching[0][0] != lock['sha512'] or not re.fullmatch('[0-9a-f]{128}', lock['sha512']):
    raise SystemExit('Exact manifest entry mismatch')
with image.open('rb') as stream:
    actual = hashlib.file_digest(stream, 'sha512').hexdigest()
if actual != lock['sha512']:
    raise SystemExit('Pinned image mismatch')
print(json.dumps({'checksum_verification': 'passed', 'detached_signature': 'unavailable in observed upstream release',
                  'assurance': 'HTTPS plus previously pinned manifest/image digests', 'image': str(image)}))
VERIFY
```

Expected recorded lock values remain the existing `manifest_sha256=5e22239e7bcb7ac4056324aa1829620f2853bff0c3b77b3af8c4578642c0f359` and the full SHA512 already in `build/builder-image.lock.json`. Do not edit them to make a failed verification pass. Reading the immutable backing image may add I/O while the builder runs; parent should choose timing and avoid unnecessary repeated scans.

If upstream later publishes an applicable signature, proceed only after all of these are established:

1. Exact signature URL, content digest and matching immutable manifest bytes; reject an HTML error page.
2. Official cloud-signing identity and full fingerprint, its validity/revocation status and acceptable date context. Do not reuse CD fingerprints by analogy.
3. Authenticated key distribution, including actual package/member/hash records if using an extracted keyring. Keep every writable GnuPG directory and temporary file inside the project.
4. `gpgv --status-fd` evidence for the exact signature/manifest and a `VALIDSIG` whose signing/primary fingerprints match the approved identity; nonzero/error/missing identity must fail closed. A display-name/GOODSIG string alone is insufficient.
5. Existing manifest pin, exact filename entry and streamed image SHA512 checks still pass. Persist provenance without overstating the chain.

## Alternatives requiring a separate decision

If an independently signed bootstrap image is required for release policy, use a differently authenticated bootstrap input or build the builder from signed Debian installation media/repository metadata in a new contained disk. That is a new, tested build-input decision; it is not accomplished by swapping a key file underneath this running VM. Signed official Debian installation/live media have a documented signature route, but changing the builder may entail a rebuild and does not by itself make the final derivative ISO reproducible or signed.

Local preservation and project-generated release checksums/signatures can protect the project's own later artifacts, but cannot retroactively prove upstream authorship of a cloud image. Full input snapshot pinning, target package provenance, final ISO verification and functional install tests remain separate work.

## Sources and resume

1. Current official cloud index: https://cloud.debian.org/images/cloud/ (direct HTTPS200 observed2026-10-24).
2. Exact dated cloud release: https://cloud.debian.org/images/cloud/trixie/20261021-2638/ (direct HTTPS200; signature404 checks above).
3. Debian, verifying installation/live media: https://www.debian.org/CD/verify (web retrieval successful; page last modified2026-02-20).
4. Canonical, Noble debian-keyring file list: https://packages.ubuntu.com/noble/all/debian-keyring/filelist (web retrieval successful).

Research complete; no implementation/runtime cryptographic verification performed. Parent can record the upstream signature availability blocker, retain the explicit current assurance wording, and prioritize functional image validation without touching the active VM. Do not repeat keyring extraction work until an applicable signature and authorized identity exist.

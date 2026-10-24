# Restart brief
Goal: real installable Windows-style Linux distribution, not a web mockup.
Read AGENTS.md and all memory files, inspect main branch and project-only changes, check existing jobs, continue W12-003/004.
Absolute project: /workspace/scratch/3c38ab731138/AI-use/windows12.
Repo upstream initially bcf129f34a3d15b50043c8615acf99167e449fa3. Root README/LICENSE are tracked but deliberately absent locally; never stage unrelated deletions.
No image or GUI tests yet. Isolation probes bwrap/unshare/Landlock failed; QEMU missing, /dev/kvm absent; network Debian/GitHub works. No permission to modify host or install physically.
Active work: investigate contained userspace VM build; source-backed architecture/compatibility research; implement target overlay. Detailed tasks in TASKS.md. Do not claim release completion.

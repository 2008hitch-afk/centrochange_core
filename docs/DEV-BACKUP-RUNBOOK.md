# Synthetic DEV backup

CC-CAP-035 uses native `bench backup --with-files --compress` for database, public/private files and configuration. GOAL-01 is DEV-only; this is not a production custody, retention or disaster-recovery policy.

```sh
sg docker -c 'python3 infra/dev_backup.py --destination /tmp/centrochange-dev-backups'
```

The script refuses repository destinations and requires the private synthetic DEV bootstrap guard. It invokes the fixed `centrochange-dev-backend-1`/`centrochange.local` target, checks four native components, records only size/hash inventory, encrypts with GnuPG AES256, verifies authenticated decryption through a pipe and removes plaintext archive and exact invocation-specific native/raw files. Output directory is 0700; encrypted backup and local DEV-only key are 0600 and remain outside Git. Keep both to decrypt the DEV archive; losing the key makes it unusable.

A failure is explicit. The cleanup removes plaintext even on a failed component/encryption verification. No broad runtime volume removal occurs. Backup failure is not success merely because some files exist.

Evidence: `docs/evidence/WAVE-04-2026-10-05.md`. This test proves component coverage, encryption/integrity and no raw artifact in Git. It does **not** prove restore/DR, production key separation or production retention; CC-CAP-036 full DR remains deferred and production preparation requires its own authorized goal.

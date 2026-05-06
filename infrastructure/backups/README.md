# Backup Artifacts Policy

Database dumps and restore artifacts are local/private operational files. They are not source code, portfolio evidence, or public review material.

Do not commit:

- `*.dump`
- `*.sql`
- `*.rdb`
- encrypted or compressed backup payloads
- restore scratch output

Store real backups in private infrastructure such as an encrypted bucket, managed database snapshots, or a secure incident-response vault. Keep only backup strategy, restore procedures, and sanitized examples in this repository.

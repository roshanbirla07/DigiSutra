# RDS PostgreSQL Production Checklist

Use this checklist before enabling production traffic for DigiSutra on Amazon
RDS PostgreSQL.

References checked on 2026-08-11:
- AWS RDS PostgreSQL SSL/TLS:
  https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/PostgreSQL.Concepts.General.SSL.html
- AWS RDS instances in a VPC:
  https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/USER_VPC.WorkingWithRDSInstanceinaVPC.html
- AWS RDS security features:
  https://aws.amazon.com/rds/features/security/

## Required Configuration

- Engine is PostgreSQL 18.3.
- Database name is `digisutra`.
- Application user uses SCRAM-compatible authentication, not MD5-only
  credentials.
- Instance class is sized for expected traffic. `db.t4g.micro` is acceptable
  only for low-traffic staging or a very small launch; validate CPU credits,
  memory, storage I/O, and connection usage before production traffic.
- Storage autoscaling is enabled with a defined maximum.
- Automated backups are enabled with a production retention window.
- Point-in-time recovery is enabled and a restore drill has been completed.
- Deletion protection is enabled for production.
- Maintenance window and backup window are defined outside peak traffic.
- Enhanced Monitoring or CloudWatch monitoring is enabled.
- Alarms exist for CPU, free memory, free storage, connection count, storage
  burst balance or I/O pressure, replication/storage lag where applicable, and
  failed connections.

## Network And Access

- RDS is in private subnets and is not publicly accessible.
- The DB subnet group has at least two Availability Zones and enough spare IP
  capacity for RDS recovery actions.
- The DB security group allows inbound PostgreSQL only from the API runtime
  security group.
- No broad CIDR ranges such as `0.0.0.0/0` are allowed on port 5432.
- Administrative access uses a controlled path such as VPN, SSM, or a bastion
  with audited access.

## SSL And Connection Policy

- `rds.force_ssl` is enabled in the active DB parameter group. AWS enables this
  by default for RDS PostgreSQL 15 and later, but verify the applied parameter.
- Application configuration uses `POSTGRES_SSLMODE=require` for initial RDS
  rollout.
- Certificate-verifying SSL mode is tracked as a follow-up once RDS CA bundle
  distribution is wired into deployment.
- Connection pools are sized below the instance connection capacity, with room
  for admin sessions, migrations, and background jobs.

## Migration Gate

- Take a database backup or verify point-in-time recovery before migration.
- Run `scripts/smoke_postgres_18_3.sh` against an empty PostgreSQL 18.3
  database before deploying schema changes.
- Run `alembic upgrade head` against production before starting new API code.
- Confirm `alembic current` matches head after the upgrade.
- Start the API with `ENABLE_DB_CREATE_ALL` unset.
- Run health and application smoke tests before enabling traffic.

## Rollback

- Code rollback may be performed through the deployment system.
- Schema rollback for migrations that widen or add identifier/provider fields
  should use point-in-time restore or a pre-migration backup when the migration
  marks downgrade as unsafe.
- Record the restore target time, operator, reason, and validation result in
  the deployment log.

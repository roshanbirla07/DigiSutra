# API startup and HTTPS routing

The API container serves the Flask WSGI application with Gunicorn on HTTP port 5000. Flask's interactive debugger must not be enabled on a reachable deployment.

## Deploy a rebuilt API image

After updating the checkout on the EC2 instance, run:

```bash
docker compose up -d --build app
docker compose ps app
docker compose logs app --tail=50
curl -i http://127.0.0.1:5000/health
```

`docker compose restart app` only restarts the existing container. It does not rebuild the image to apply changes to the Dockerfile or Python dependencies.

## HTTPS

Gunicorn on port 5000 speaks **HTTP**. Serve HTTPS from a load balancer or reverse proxy on port 443 and forward its requests to HTTP port 5000. Configure that proxy's target health check as HTTP `/health`. Do not configure clients or target health checks to send TLS directly to port 5000.

Restrict direct inbound access to port 5000 to the trusted proxy or load balancer. If the proxy runs on the same EC2 host, the Compose port mapping may be bound to `127.0.0.1:5000:5000`. If the load balancer reaches the EC2 host over the VPC, preserve the host bind and restrict ingress in its security group to the load balancer instead. Apply the same access review to the exposed PostgreSQL port.

Binary request logs beginning with `\\x16\\x03\\x01` typically represent a TLS ClientHello delivered to this HTTP listener. A `GET /` 404 is expected because the API implements `/health` and `/v1/...` routes, not a root page; the web frontend runs separately on port 3000. Unknown internet requests to `/mcp`, `/sse`, and `/favicon.ico` do not identify an API failure.

A 200 from `/health` verifies the process and database query. It does not by itself validate DNS, TLS termination, frontend routing, or product/payment flows.

## Instance-local PostgreSQL image and credentials

Compose defaults to PostgreSQL 18.3 for a fresh installation. If the existing EC2 data volume was initialized on PostgreSQL 17, keep that major version in the ignored `.env` file before recreating containers:

```dotenv
POSTGRES_IMAGE=postgres:17-alpine
POSTGRES_DB=digisutra
POSTGRES_USER=postgres
POSTGRES_PASSWORD=<instance-specific-password>
```

Check the running major version with `docker compose exec postgres psql -U postgres -d digisutra -Atqc 'SHOW server_version;'`. Never point a PostgreSQL 18 image at a PostgreSQL 17 data directory without a planned backup and migration. `docker compose restart` does not apply Compose image or configuration changes; `docker compose up -d --build app` rebuilds the API without recreating PostgreSQL.

## S3 signed URL behavior

The S3 gateway now signs requests against the configured AWS Region using SigV4 and virtual-hosted bucket URLs. This affects URL format and signature validation, not IAM authorization: the signing IAM principal still needs `s3:PutObject` for uploads and `s3:GetObject` for downloads on the relevant key prefixes. Browser uploads must send the exact signed `Content-Type` header, and the S3 bucket CORS policy must allow the web origin and `PUT`.

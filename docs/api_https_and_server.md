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

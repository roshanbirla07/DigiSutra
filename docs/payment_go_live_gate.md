# Payment and seller payout go-live gate

This repository records seller earnings in PostgreSQL. `seller_balance` is not a funded wallet and the manual payout endpoints do not transfer money to a bank account.

## Changes in the payment safety baseline

- Checkout confirmation fetches the Razorpay payment after validating its signature and grants access only when the payment is captured for the exact order, amount and currency. Signed capture webhooks apply the same amount and currency checks. Order rows are locked during confirmation and webhook processing to avoid two credits for a concurrent callback.
- Only admins can initiate a refund through the order endpoint. Customers should contact support with the order and payment reference. The default customer refund is the gross purchase price; seller liability is the corresponding share of net earnings, including for a partial refund.
- Refunded seller debt stays visible as a negative available balance, rather than disappearing at zero. An admin cannot mark a pending manual payout paid while that debt remains. Outstanding payout reservations stay reserved until an operator cancels or reconciles them.
- Docker Compose binds PostgreSQL to the EC2 loopback address. Keep port 5432 closed in the instance security group as well.

## Still required before accepting live payments

1. Put the web app and API behind an HTTPS domain and reverse proxy/load balancer. Do not expose ports 3000, 5000, or 5432 to the internet. The checked-in Compose setup still publishes the HTTP web and API ports and mounts live source directories; use an immutable deployment image and a restricted proxy for production.
2. Verify production Razorpay credentials, automatic capture, and live webhook signature secret. Subscribe to `payment.captured`, `refund.processed`, and `refund.failed`. Test a completed purchase, duplicate callback, authorized-but-uncaptured payment, failed payment, and a delayed webhook end to end.
3. Reconcile Razorpay captures, refunds, chargebacks, gateway fees, and settlements against orders and the actual receiving bank account. The app does not yet consume provider settlement reports or block payout requests until settlement. The reconciliation summary currently reports database state only.
4. Complete seller KYC and real fund-account verification. Execute manual payouts outside DigiSutra and match each payout to a bank transfer before an admin records it as paid. Do not treat a `paid` database status as evidence of a transfer. Add a provider payout integration or bank reference and automated reconciliation before offering self-service withdrawal.
5. Define and review marketplace tax invoices, GST treatment, fee refunds, chargebacks, partial refunds, seller debt collection, and customer refund policy with the responsible finance/legal owner. The current order calculation sets `tax_amount` to zero.
6. Back up the database, run `alembic upgrade head`, smoke-test `/health`, and verify payment, delivery, refund, and payout flows on the deployed version before routing live traffic. Monitor webhook failures and outstanding balances.

# Marketplace Financials, Risk, and Operations Plan

## Summary
Build the product as a digital marketplace with a real internal ledger, not just payment collection. Razorpay handles incoming payments first; the platform owns seller earnings, commission, refunds, delivery access, moderation, and payout tracking. For your stage, start with manual or semi-manual seller payouts, but design the schema so you can later switch to Razorpay Payouts/Route without rewriting the financial model.

## Key Changes
- Add a seller payout layer separate from buyer payments:
  - `seller_balance`
  - `pending_payout`
  - `available_for_payout`
  - `payout_batch`
  - `payout_status`
  - payout failure/retry logs
- Extend the order ledger to store marketplace economics:
  - gross amount
  - platform commission
  - taxes if applicable
  - net seller amount
  - refund amounts
- Decide commission policy now:
  - flat percentage is the safest MVP default
  - keep the schema flexible for tiered/category-based commissions later
- Keep payment provider abstraction, but do not add multiple gateways now:
  - Razorpay for collection
  - separate payout mechanism later
- Add product delivery protection:
  - signed/expiring download URLs
  - access tied to purchase order
  - access revocation on refund
  - download policy and re-download rules
- Add refund and dispute mechanics:
  - buyer-requested refund
  - creator approval flow
  - admin override
  - partial refund support
  - content access revocation on refund
- Add moderation and abuse controls:
  - creator listing approval or flagging
  - seller suspension
  - fraud/risk signals
  - payout hold on suspicious accounts
- Add notification events:
  - order success
  - payment failure
  - delivery ready
  - refund processed
  - payout initiated
  - payout failed
  - dispute updated
- Add operational separation:
  - Razorpay test vs live configuration
  - webhook failure logging
  - payment and payout alerting
  - reconciliation reports

## Recommended Payout Strategy
- Use manual or semi-manual payouts at first.
- Do not block launch on Route or automated split payouts.
- Track seller earnings in your own ledger from day one.
- Pay sellers out in batches after review.
- Keep payout status and seller balance first-class in the schema so you can later move to Razorpay Route or Payouts API.

This is the right stage-based approach:
- fastest to launch
- simplest seller onboarding
- keeps review/control over fraud and disputes
- preserves a migration path to automated payouts later

## Priority Order
1. Marketplace ledger
- internal order record
- commission calculation
- seller balance tracking
- refund bookkeeping

2. Razorpay payment collection
- checkout/order creation
- webhook verification
- idempotent payment confirmation

3. Digital fulfillment
- access grant after payment
- signed download links
- access revocation on refund

4. Seller payout system
- manual batch payout workflow
- payout ledger
- payout hold/retry/failure handling

5. Tax and invoice foundation
- invoice/receipt generation per order
- invoice number sequence
- tax fields in ledger

6. Moderation and support
- listing review
- fraud flags
- disputes
- account suspension

7. Dashboard
- sales
- payout owed
- payout paid
- refunds
- disputes
- product performance

## Important Schema/Interface Additions
- Orders should include:
  - `gross_amount`
  - `platform_fee`
  - `tax_amount`
  - `net_seller_amount`
  - `payment_status`
  - `delivery_status`
  - `refund_status`
- Seller payout records should include:
  - `seller_id`
  - `amount`
  - `status`
  - `payout_method`
  - `batch_id`
  - `failure_reason`
  - `processed_at`
- Product access records should include:
  - `order_id`
  - `asset_id`
  - `access_status`
  - `download_count`
  - `revoked_at`
- Notification/event records should include:
  - `event_type`
  - `entity_type`
  - `entity_id`
  - `delivery_status`
  - `payload_snapshot`

## Test Plan
- Buyer payment success creates a ledger entry and seller net amount.
- Duplicate webhook events do not duplicate revenue or access.
- Refund reverses seller earnings and revokes access if required.
- Manual payout batch marks seller payout as paid once.
- Payout failure moves to retry/hold state.
- Signed content URLs expire and are tied to order access.
- Suspended sellers cannot list new content or receive payouts.
- Test-mode and live-mode Razorpay settings are isolated.

## Assumptions
- Razorpay is the first and only payment collector for launch.
- Seller payouts start manual or semi-manual, not Route-based.
- A flat commission is the MVP default.
- GST/invoice support should be designed now, even if the full tax workflow is implemented later.
- Compliance around holding funds should be reviewed before scaling payouts, but the product should not wait for automated payout integration to launch.

## Next Build Sequence
- Define the marketplace ledger models.
- Add product listing and delivery models.
- Implement Razorpay order/webhook flow.
- Add refund and access revocation.
- Add manual seller payout workflow.
- Add notifications and moderation.
- Build the seller dashboard on top of stable financial data.

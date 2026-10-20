# SDK User Commands 11 — Stripe Retrieve Customer

This document teaches the bounded Python capability of retrieving one customer
through the Stripe SDK.

## 1. Core capability

When a user wants customer data from Stripe, the reusable capability is Stripe
customer retrieval by API key and customer ID.

## 2. Executable Python relation

This capability should be learned as a reusable Python ability artifact.

```python
def main(
    api_key: str,
    customer_id: str,
    *,
    __dependencies__: tuple[str, ...] = ("stripe",),
) -> dict[str, object]:
    import stripe

    stripe.api_key = api_key
    customer = stripe.Customer.retrieve(customer_id)
    return {"status": "ok", "customer_id": customer["id"], "email": customer.get("email")}
```

## 3. Inputs and outputs

Inputs:

* `api_key`: the Stripe API key
* `customer_id`: the Stripe customer identifier

Output:

* status, customer ID, and selected customer fields

## 4. Natural-language paraphrases

* retrieve the Stripe customer `cus_123`
* fetch one Stripe customer with the Python SDK
* look up customer data from Stripe

## 5. One-sentence summary

Retrieving one Stripe customer by API key and customer ID is a reusable Python
SDK billing-read capability.

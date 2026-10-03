# Step 26 RE2-SS Topology Preflight

Date: 2026-10-03
Status: PASS before any RE2-SS raw-data access.

Expected repository HEAD: `d840a5a23197fde54b3e8c2586a3fecb7eba41fc`.
Verified repository HEAD matched before this preflight.

Frozen Sock Shop topology source:
`microservices-demo/microservices-demo@9dff06fae4981921caec6a62393a6ebfce4b3e3f`.

The exact commit was fetched from the upstream GitHub repository and resolved to
`9dff06fae4981921caec6a62393a6ebfce4b3e3f` (commit title: `Add deprecation notice`).
Primary topology manifests are under `deploy/kubernetes/manifests-policy/`.

The pinned network policies imply these caller -> dependency edges:
- `front-end -> carts` (`cart-access`, with frozen `cart -> carts` normalization)
- `orders -> carts` (`cart-access`, same normalization)
- `front-end -> catalogue`
- `front-end -> orders`
- `orders -> payment`
- `orders -> shipping`
- `front-end -> user`
- `orders -> user`
- `shipping -> rabbitmq`
- `queue-master -> rabbitmq`
- `carts -> carts-db` (`cart-db-access`, source `cart -> carts` normalization)
- `catalogue -> catalogue-db`
- `orders -> orders-db`
- `user -> user-db`

These exactly match Section 12.2 of the frozen Phase A specification. No missing,
extra, reversed, or differently normalized frozen edge was found. Therefore the
topology preflight gate passes. No RE2-SS benchmark case or label was accessed.

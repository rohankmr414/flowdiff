---
tags: [flowdiff]
max_turns: 30
timeout_seconds: 900
allowed_tools: [Read, Glob, Grep, Skill, Write, Edit, Bash]
---

Can you review shop.patch for me? It's a PR against our little order service (the code after the patch is in shop/). I don't want a wall of text, I want to see how the request flows change, function by function, and what actually changed inside each function. Flag anything that looks risky.
Input files: shop.patch, shop/api.py, shop/orders.py, shop/inventory.py, shop/payments.py, shop/pricing.py

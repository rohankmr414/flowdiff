---
type: llm
focus: trace
weight: 1
---

The review flags that the job is enqueued before db.commit(), so the worker can look the user up before it exists and drop the job

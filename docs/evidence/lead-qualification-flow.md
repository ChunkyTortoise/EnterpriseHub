# Lead Qualification Flow Evidence

```mermaid
flowchart LR
    intake["Lead intake\nSMS / webhook"] --> signature["Signature verification\nand schema parsing"]
    signature --> routing["Bot routing\nlead / buyer / seller"]
    routing --> compliance["Compliance pipeline\nTCPA / FHA / RESPA / SMS limits"]
    compliance --> crm["CRM sync\nGHL tags, fields, tasks"]
    crm --> telemetry["Eval and telemetry\nrubrics, cache, cost, outcomes"]
```

Use this as the short architecture path in interviews: the backend boundary receives untrusted lead events, validates them, routes them to the correct bot workflow, applies deterministic compliance controls, syncs CRM actions, and leaves evidence for evals and telemetry.

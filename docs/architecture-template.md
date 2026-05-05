# Architecture Template

## Business Problem

Describe the business problem in plain language.

## Users

Describe the intended users or stakeholders.

## System Overview

```mermaid
flowchart LR
    A[Input] --> B[Processing]
    B --> C[Retrieval Or Tool Layer]
    C --> D[AI Or Rules Engine]
    D --> E[Output]
    E --> F[Evaluation And Logs]
```

## Components

| Component | Responsibility |
|---|---|
| App UI | User interaction |
| Data Layer | Synthetic or public data |
| Retrieval Layer | Search, filtering, or context lookup |
| AI Layer | LLM, rules, or agent workflow |
| Evaluation Layer | Tests, metrics, and review |

## Tradeoffs

List technical and business tradeoffs.

## Limitations

List what the project does not prove.

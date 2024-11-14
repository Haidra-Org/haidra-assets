# AI-Horde Job Lifecycle

You can also download the [job_lifecycle.mermaid file here](job_lifecycle.mermaid).

``` mermaid

graph TD
    A[User Submits Request] --> B{Server Validates Request}
    B -->|Valid| C{Kudos Check}
    C -->|Sufficient Kudos| D[Subtract Kudos]
    C -->|Allow Downgrade| E{Adjusted Parameters Acceptable}
    E -->|Yes| D
    E -->|No| F[Reject Request]
    C -->|Insufficient Kudos| F
    D --> G[Break into Jobs]
    G --> H[Add Jobs to Queue]

    H --> I[Worker Pops Jobs]
    I --> J{Job Available}
    J -->|Yes| K[Process Job]
    J -->|No| L{Is Queue Full}
    L -->|Yes| M[Wait]
    L -->|No| I
    M --> L
    K --> N{Retry or Abandon Job}
    N -->|Retry| I
    N -->|Abandon| O[Update Request Status]
    K --> P[Submit Final Payload]
    P --> L
    P --> Q[Request Complete]

    Q --> R[Update Request Status]
    O --> R
    R --> S[User Retrieves Results]
    R --> T[Award Kudos to Worker]
    T --> I

```

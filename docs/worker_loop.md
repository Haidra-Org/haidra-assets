# Worker Loop

You can also download the [worker_loop.mermaid file here](worker_loop.mermaid).

```mermaid
graph TD
    A[Worker Startup] --> B{Maintenance Mode}
    B -->|Yes| C[Maintenance]
    C --> D{Operator Resumes}
    D -->|Yes| B
    D -->|No| C
    
    B -->|No| E[Worker Polls for Jobs]
    E --> F{Job Available}
    F -->|Yes| G{Matches Worker Capabilities}
    G -->|Yes| H[Worker Receives Job]
    G -->|No| I{Is Queue Full}
    H --> J{Worker Queue}
    J -->|Has Capacity| K[Load Model]
    J -->|At Capacity| L[Queue Job]
    L --> I
    K --> M[Process Job]
    
    M --> N{Postprocessing Needed}
    N -->|Yes| O[Perform Postprocessing]
    N -->|No| P{Content Check}
    O --> P
    
    P -->|Image Generation| Q{NSFW Filtering}
    Q -->|Requested| R[Filter NSFW Content]
    Q -->|Not Requested| S{Illegal Content Check}
    R --> S
    P -->|Text Generation| S
    
    S -->|Pass| T[Prepare Job Submit Payload]
    S -->|Fail| U[Delete Image, Prepare Warning]
    
    T --> V{Upload Results}
    V -->|Success| W[Submit Final Payload]
    V -->|Failure| X{Retry or Abandon Job}
    X -->|Retry| Y{Retry Count Exceeded}
    Y -->|No| E
    Y -->|Yes| Z{Excessive Faults}
    X -->|Abandon| AA[Update Request Status]
    U --> W
    
    W --> I{Is Queue Full}
    I -->|Yes| AB[Wait]
    I -->|No| E
    AB --> I
    W --> AC[Request Complete]
    
    AC --> AA
    AA --> AD[Award Kudos to Worker]
    AD --> AE{Excessive Faults}
    AE -->|Yes| B
    AE -->|No| E
    
    Z -->|Yes| B
    Z -->|No| AF[Worker Shutdown]
    AF --> AG[Worker Unavailable]

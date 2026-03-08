# User Experience

## Overall Flow

```mermaid
flowchart TD
    A["Install self-consciousness skill in OpenClaw"] --> B["First run: choose or create user_id"]
    B --> C["Register user_id with backend and receive 500 credits"]
    C --> D["Create local workspace under ~/.self-consciousness/users/<user_id>/"]
    D --> E{"Choose onboarding mode"}
    E --> F["Structured Alignment Workspace"]
    E --> G["Playful Alignment Experience"]
    F --> H["Local conversations: record consciousness in the moment"]
    G --> H
    H --> I["Daily alignment runs locally inside OpenClaw"]
    I --> J["Write local consciousness_records / snapshots / scores"]
    J --> K{"Want to explore the community?"}
    K --> L["Ask backend for shared gameplay recommendation using coarse context only"]
    K --> M["Stay local and continue current gameplay"]
    L --> N{"User wants to try it?"}
    N --> O["Pull gameplay markdown to ~/.self-consciousness/users/<user_id>/gameplay_cache/"]
    O --> P["Activate or iterate local gameplay"]
    N --> M
    P --> Q["Optional: publish a new gameplay draft to backend"]
    Q --> R["Optional: create, solve, review, and settle shared tasks"]
    R --> S["Optional: use image/video tools billed by credits"]
```

## Backend Communication

```mermaid
flowchart LR
    subgraph Local["OpenClaw + Local Workspace"]
        A["OpenClaw agent"]
        B["SKILL.md protocol"]
        C["~/.self-consciousness/profile.json"]
        D["~/.self-consciousness/users/<user_id>/consciousness.db"]
        E["gameplay_cache / gameplay_drafts / artifacts"]
    end

    subgraph Cloud["Shared Backend"]
        F["/api/v1/onboarding"]
        G["/api/v1/gameplays"]
        H["/api/v1/tasks"]
        I["/api/v1/credits"]
        J["/api/v1/tools"]
    end

    A --> B
    B --> C
    B --> D
    B --> E

    A -->|register user_id, save preference| F
    A -->|list, get, recommend, pull shared gameplays| G
    A -->|create, claim, solve, review, settle tasks| H
    A -->|read balance and credit transactions| I
    A -->|image.generate / video.generate| J

    D -.->|"private only: consciousness_records, snapshots, scores"| A
    D -.->|"not uploaded"| Cloud
```

## Privacy Boundary

- Local only: daily alignment, raw consciousness records, snapshots, private scores, local visualization.
- Shared backend: onboarding, shared gameplay discovery, gameplay publish, tasks, credits, media tool jobs.
- Cloud recommendation uses only coarse context such as onboarding mode, preferred gameplay ids, desired tags, current gameplay id, excluded ids, available tools, and stage band.

# Switch Wiring Diagram

```
┌──────────────────────┐   ┌──────────────────┐
│      Yellow Box      │   │    Black Box     │
└─────┬──────────┬─────┘   └───────┬──────────┘
      │ (14)     │ (4)             │ (5)
      │          └──────┐   ┌──────┘
      │                 ▼   ▼
      │        ┌──────────────────────────────────┐
      │        │             Gray Box              │
      │        └──────────────────────────────────┘
      │
      ▼
┌──────────────────────────────────┐
│              Switch              │
└──────────────────────────────────┘
```

## Port Mapping

| Component          | Port | Connects To |
|---------------------|------|-------------|
| Yellow Box (left out)  | 14   | Switch      |
| Yellow Box (right out) | 4    | Gray Box    |
| Black Box           | 5    | Gray Box    |
| Switch              | 1    | Ground      |
| Switch              | 3    | D_103       |
| Switch              | 7    | D_104       |


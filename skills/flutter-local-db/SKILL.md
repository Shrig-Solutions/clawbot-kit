---
name: flutter-local-db
description: Implement and maintain local persistence in Flutter apps using Hive and Drift, including service-wrapper architecture, initialization, user-scoped databases, encrypted boxes, typed box access, query methods, streams, and lifecycle management. Use when adding or editing local storage, offline persistence, cached app state, media/file metadata stores, or wrapper services around Hive or Drift. When working in Fishtechy, use its HiveDBService, FishDatabaseService, and MediaDatabaseService as the reference implementation.
---

# Flutter Local DB

Implement local persistence in the style already used by the target Flutter app.

## Choose the right storage layer

### Use Hive for lightweight app state and preferences

Use Hive when storing:
- preferences and flags
- auth/session snapshots
- small typed objects
- lightweight cached user data
- hydrated state support

Typical fits:
- current user
- credentials
- theme/font settings
- onboarding/tutorial flags
- per-user feature preferences

### Use Drift for relational or query-heavy local data

Use Drift when the feature needs:
- structured tables
- filtering/sorting/pagination
- joins or derived views
- reactive query streams
- larger local collections
- queue-like behavior and update workflows

Typical fits:
- local media records
- upload/measurement queues
- offline searchable entities
- relational cache layers

## Prefer service-wrapper architecture

Do not scatter raw `Hive.box(...)` or raw Drift database access across widgets and Cubits.

Prefer a wrapper/service layer that owns:
- initialization
- dependency injection
- encryption setup
- user scoping
- lifecycle and close behavior
- app-friendly methods and streams

Pattern examples:
- `HiveDBService` wrapping Hive boxes
- `FishDatabaseService` wrapping a Drift database instance
- `MediaDatabaseService` wrapping a user-scoped Drift DB with higher-level workflows

## Hive conventions

### Centralize boxes in one service

Prefer a single service like `HiveDBService` to:
- declare boxes
- open boxes
- register adapters
- hydrate initial subjects/streams
- expose typed getters/setters
- hide box names from feature code

### Use encryption intentionally

Sensitive boxes such as credentials should be encrypted.

A good pattern is:
- create/read the encryption key from secure storage
- open selected boxes with `HiveAesCipher`
- keep encryption setup inside the wrapper service

### Expose typed app APIs, not box internals

Prefer methods like:
- `setCredentials(...)`
- `setCurrentUser(...)`
- `clearUserData()`
- `setPushnotificationsEnable(...)`

instead of making callers write directly to boxes.

### Expose streams for reactive app state

If features react to local state changes, expose streams from the wrapper service.

Examples:
- `credentialsStream`
- `userStream`
- preference watch streams mapped to typed values

## Drift conventions

### Keep raw DB classes separate from service wrappers

A healthy structure is:
- raw Drift database definition and generated code in `*_db.dart`
- wrapper service in `*_db_service.dart`

The wrapper service should expose feature-oriented methods and hide direct DB plumbing from callers.

### Use service wrappers for domain behavior

A Drift service wrapper is the right place for:
- insert/update helpers
- pagination helpers
- query filters
- stream-based accessors
- user-specific file/database switching
- migration/copy logic around database files
- ranking/queue orchestration that sits above raw SQL/table code

### Support user-scoped databases when needed

If local data belongs to a logged-in user, let the service own switching behavior.

Typical responsibilities:
- detect current user
- open the correct database file
- copy/migrate default DBs if needed
- close/reset DB on logout

### Expose app-level result shapes

Instead of leaking low-level table rows everywhere, prefer wrapper methods that return:
- domain models
- view models
- paginated result types
- streams of feature-ready values

## Lifecycle and initialization

### Use DI-friendly initialization

If the app uses dependency injection, initialize local DB services with lifecycle hooks like `@PostConstruct(preResolve: true)`.

This is a good place to:
- initialize Hive
- build HydratedBloc storage
- register adapters
- open boxes
- open Drift databases
- hydrate initial in-memory subjects

### Always own close behavior

If a service owns a DB connection, it should also own shutdown.

Typical patterns:
- `Future<void> close()` on database services
- `@disposeMethod` for DI-managed cleanup
- reset in-memory handles after closing

## State-management integration

Cubits and other feature logic should depend on wrapper services, not on raw Hive or Drift primitives.

Prefer:
- `HiveDBService` for session/preferences state
- `MediaDatabaseService` / `FishDatabaseService` for local relational data

This keeps storage concerns centralized and testable.

## Decision guide

Before adding local persistence, decide:
1. Is this lightweight key-value state or relational/query-heavy data?
2. Should it live in Hive or Drift?
3. Does the app already have a wrapper service where this belongs?
4. Does the data need encryption?
5. Is the data user-scoped?
6. Does the feature need streams, pagination, or query helpers?

## Avoid these mistakes

- Do not access raw Hive boxes all over the codebase.
- Do not expose raw Drift DB objects to every caller unless the architecture explicitly wants that.
- Do not mix initialization logic into widgets.
- Do not forget user switching and close/reset behavior for user-scoped DBs.
- Do not store query-heavy relational data in Hive just because it is fast to start.
- Do not duplicate box names and keys across unrelated files.

## Build step

If you edit Drift schemas or generated-model wiring, regenerate code from the Flutter project root:

```bash
dart run build_runner build -d
```

## Fishtechy reference

When working in the Fishtechy app, read `references/fishtechy-patterns.md` for concrete examples of:
- `HiveDBService` for Hive wrapper structure
- `FishDatabaseService` for Drift wrapper structure
- `MediaDatabaseService` for user-scoped Drift service workflows

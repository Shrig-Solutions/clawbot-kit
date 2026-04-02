# Fishtechy reference patterns for Flutter local DB

## Overview

Fishtechy uses both Hive and Drift, but importantly it does not let feature code talk to storage layers directly everywhere. It wraps each local database concern in service classes.

## Hive wrapper structure

Primary file:
- `lib/core/services/hive_db/hive_db_service.dart`

### `HiveDBService`

Pattern highlights:
- annotated as `@singleton`
- initialized with `@PostConstruct(preResolve: true)`
- calls `Hive.initFlutter()`
- configures `HydratedBloc.storage`
- registers Hive adapters
- opens all boxes in one place
- hides box names behind typed APIs
- hydrates in-memory subjects for auth/user state
- exposes streams for reactive consumers

Responsibilities include:
- encrypted boxes for sensitive data like credentials/login creds
- standard boxes for user/profile/theme/preferences
- current user/session reads
- typed setter/getter methods
- cleanup methods like `clearUserData()`

Good takeaway:
- use a single Hive service as the app-facing wrapper for key-value local state

## Drift wrapper structure

Fishtechy splits Drift into raw database classes plus wrapper services.

### Fish DB

Files:
- `lib/core/services/drift_db/fish/fish_db.dart`
- `lib/core/services/drift_db/fish/fish_db_service.dart`

`FishDatabaseService` pattern:
- annotated as `@singleton`
- owns a private `FishDatabase _db`
- initializes the DB in `initialize()`
- exposes feature-oriented methods like:
  - `insertOrUpdateAllFish(...)`
  - `getFishes(...)`
  - `getFishById(...)`
- owns `close()`

Good takeaway:
- keep Drift schema/query code in the DB class and expose app-friendly operations through a service wrapper

### Media DB

Files:
- `lib/core/services/drift_db/media/media_db.dart`
- `lib/core/services/drift_db/media/media_db_service.dart`

`MediaDatabaseService` pattern:
- annotated as `@lazySingleton`
- owns nullable `MediaDatabase? _db`
- exposes guarded access through `db`
- initializes via `switchToCurrentUser()`
- depends on other services (`HiveDBService`, ranker, directory service access)
- owns user-scoped DB switching and migration logic
- exposes high-level workflow methods instead of raw SQL access
- exposes reactive streams for latest items and counts
- uses `@disposeMethod` for cleanup

Responsibilities include:
- opening the correct user-specific DB
- copying/migrating a default DB file into a user-specific DB path
- creating/updating/deleting media records
- managing queue ranks
- handling paginated reads
- exposing local streams for latest pending/saved records
- closing and resetting the DB on logout/dispose

Good takeaway:
- use a richer Drift wrapper service when the feature has workflow logic beyond simple CRUD

## Architectural guidance distilled

### Use Hive when
- data is key-value oriented
- values are relatively small
- preferences/session/profile snapshots are enough
- hydration and simple watch streams are useful

### Use Drift when
- data behaves like tables
- you need pagination/filtering/search
- local workflows are queue-based or relational
- query streams and derived views matter

### Always prefer services as wrappers

In Fishtechy, the wrapper service is the public boundary. Feature code should call service methods, not care about:
- box names
- DB filenames
- encryption setup
- database switching logic
- migration/copy logic
- internal table/query plumbing

## Suggested implementation recipe

1. Choose Hive or Drift based on data shape and query needs.
2. Add or extend a wrapper service first.
3. Keep raw schema/box details private to that layer.
4. Expose typed methods and streams from the service.
5. Handle initialization and cleanup inside the service lifecycle.
6. Regenerate code if Drift definitions changed.

## Smells to avoid

- direct `Hive.openBox` calls scattered across feature code
- raw Drift DB queries in Cubits/widgets
- per-feature reinvention of encryption/user switching logic
- missing `close()` ownership for DB-backed services

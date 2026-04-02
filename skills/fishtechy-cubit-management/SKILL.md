---
name: fishtechy-cubit-management
description: Implement and maintain Fishtechy-style Cubits and state classes for Flutter features using flutter_bloc, injectable, BaseCubit, BaseAsyncCubit, BaseSearchAsyncCubit, AsyncValue, and freezed state models. Use when adding or editing feature Cubits, async loading flows, debounced search/pagination state, stream-backed app state, or feature-level state management in the Fishtechy app.
---

# Fishtechy Cubit Management

Implement Cubits the way the Fishtechy app already does, not as generic Bloc boilerplate.

## Choose the right Cubit shape

### Use plain `Cubit<T>`

Use plain `Cubit<T>` when state is local, synchronous, or stream-backed and does not need `api`/`database` helpers.

Examples in the app include simple selection, toggles, and session state holders.

### Use `BaseCubit<T>`

Use `BaseCubit<T>` when the Cubit needs shared access to:
- `RestApiService api`
- `HiveDBService database`

This is the default choice for feature Cubits that need service access but do not use `AsyncValue`.

### Use `BaseAsyncCubit<T>`

Use `BaseAsyncCubit<T>` when the Cubit performs async work and should standardize:
- loading/data/message lifecycle
- Dio exception handling
- platform exception handling
- retaining previous data while surfacing errors

This is the preferred pattern for request-driven features.

### Use `BaseSearchAsyncCubit<T>`

Use `BaseSearchAsyncCubit<T>` when the feature needs:
- debounced search
- paginated results
- refresh/reset behavior
- cancelable in-flight requests
- sort/query state tracked with results

Do not rebuild this machinery ad hoc in feature Cubits.

## Core project conventions

### Prefer injectable Cubits

Feature Cubits commonly use:

```dart
@injectable
class MyCubit extends BaseCubit<MyState> {
  MyCubit(RestApiService api, HiveDBService database)
    : super(const MyState(...), api, database);
}
```

Match local constructor style and keep dependency order aligned with nearby files.

### Put state in its own file when state is non-trivial

If state has multiple variants or several fields, use a dedicated state file, often with freezed.

Examples:
- `app/app_cubit/app_state.dart`
- `core/base/search/base_search_state.dart`

For tiny local state, a direct type like `Cubit<User?>` or `Cubit<bool>` is acceptable if surrounding code already does that.

### Use freezed for expressive state

Prefer freezed when state needs:
- unions like authenticated/unauthenticated
- immutable copy semantics
- structured feature state with several fields

Keep `part` directives and generated files correct.

### Reuse `AsyncValue` for async state

Fishtechy already defines:
- `initial`
- `loading`
- `data`
- `message`

Use that shape instead of inventing a new loading wrapper unless the feature genuinely needs something else.

Pattern:

```dart
class ExampleCubit extends BaseAsyncCubit<MyData> {
  ExampleCubit(super.api, super.database);

  Future<void> load() async {
    emit(AsyncValue.loading(data: state.data));
    await runguarded(() async {
      return api.fetchSomething();
    });
  }
}
```

### Preserve previous data during refresh/error when helpful

A key Fishtechy pattern is keeping `state.data` available while loading or showing an error message. Prefer:

```dart
emit(AsyncValue.loading(data: state.data));
```

instead of wiping the state unless the UX requires a full reset.

### Manage streams and timers explicitly

If a Cubit listens to streams or uses timers/debounce logic:
- store the subscription/timer on the Cubit
- cancel it in `close()`
- avoid leaks and late emits

Examples in the app include token listeners, user listeners, and debounced search.

### Guard emits when lifecycle matters

Base async helpers already check `isClosed` before emitting. Preserve that behavior in custom async or callback-heavy logic.

## Search and pagination pattern

When implementing searchable lists, prefer extending `BaseSearchAsyncCubit<T>`.

Implement the domain fetcher only:

```dart
@override
Future<Paginated<Item>> fetcher({
  required int page,
  required BaseSearchState<Item> searchState,
  required CancelToken cancelToken,
}) {
  return api.fetchItems(
    page: page,
    limit: 20,
    query: searchState.query,
    sortBy: searchState.sortBy,
    order: searchState.sortOrder,
    cancelToken: cancelToken,
  );
}
```

Let the base class own:
- debounce
- reset
- request cancellation
- merging paginated results
- refresh behavior

## State design rules

Before creating a new Cubit/state pair, decide:
1. Is this local synchronous state, stream-backed state, async request state, or searchable paginated state?
2. Does it need `BaseCubit`, `BaseAsyncCubit`, or `BaseSearchAsyncCubit`?
3. Should state be a direct type, a freezed data class, or a freezed union?
4. Does the UI benefit from preserving old data during loading/errors?
5. Does the Cubit own any subscriptions, timers, or cancel tokens?

## Avoid these mistakes

- Do not create a brand-new async wrapper when `AsyncValue` already fits.
- Do not duplicate search debounce/cancel/pagination logic outside `BaseSearchAsyncCubit` without a strong reason.
- Do not use a huge mutable Cubit state object when a small freezed model is clearer.
- Do not forget to cancel `StreamSubscription`, `Timer`, or request cancellation resources in `close()`.
- Do not emit after disposal.

## Build step

If you add or edit freezed state files, regenerate code from the Flutter project root:

```bash
dart run build_runner build -d
```

## References

Read `references/patterns.md` for concrete Fishtechy Cubit patterns before implementing a new feature state flow.

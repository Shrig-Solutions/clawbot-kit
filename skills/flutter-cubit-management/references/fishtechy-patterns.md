# Fishtechy reference patterns for Flutter Cubit management

## Core base classes

### `BaseCubit<T>`

Location:
- `lib/core/base/base_cubit.dart`

Purpose:
- standard dependency access to `RestApiService` and `HiveDBService`

Shape:

```dart
abstract class BaseCubit<T> extends Cubit<T> {
  final RestApiService api;
  final HiveDBService database;
  BaseCubit(super.initialState, this.api, this.database);
}
```

Use when state is feature-specific but shared services are needed.

### `BaseAsyncCubit<T>`

Location:
- `lib/core/base/base_cubit.dart`
- `lib/core/base/base_state.dart`

Purpose:
- unify async state as `AsyncValue<T>`
- standardize Dio/platform/general error handling

Important behavior:
- `runguarded` emits `AsyncValue.data(...)` on success
- emits `AsyncValue.message(...)` on failure
- often preserves existing `state.data`

### `AsyncValue<T>`

Location:
- `lib/core/base/base_state.dart`

Variants:
- `initial`
- `loading`
- `data`
- `message`

Helpers:
- `isLoading`
- `isMessage`

## Concrete repo examples

### Auth/session state Cubit

File:
- `lib/app/app_cubit/app_cubit.dart`

Pattern:
- extends `BaseCubit<AppState>`
- maps persisted credentials into a simple union state
- listens to a database stream
- cancels subscription in `close()`

State file:
- `lib/app/app_cubit/app_state.dart`

Uses freezed union:

```dart
@freezed
sealed class AppState with _$AppState {
  const factory AppState.authenticated() = _Authenticated;
  const factory AppState.unauthenticated() = _UnAuthenticated;
}
```

### Stream-backed direct-type Cubit

File:
- `lib/app/profile_info_cubit/profile_info_cubit.dart`

Pattern:
- extends `Cubit<User?>`
- initializes from current database value when available
- attaches a stream listener
- performs side effects when the user changes
- cancels subscription in `close()`

Use this style only when a direct type is genuinely enough.

### Search/pagination base Cubit

Files:
- `lib/core/base/search/base_search_cubit.dart`
- `lib/core/base/search/base_search_state.dart`

Pattern provides:
- debounced `onSearch`
- reset behavior
- cancel token management
- paginated merge logic
- query/sort state in a freezed state model

State shape:

```dart
@freezed
abstract class BaseSearchState<T> with _$BaseSearchState<T> {
  const factory BaseSearchState({
    required Paginated<T> paginated,
    required String query,
    SortOrder? sortOrder,
    String? sortBy,
  }) = _BaseSearchState<T>;
}
```

## Decision guide

### Choose `Cubit<T>` when
- state is trivial
- no shared base behavior is needed
- stream-backed local/session data is enough

### Choose `BaseCubit<T>` when
- services are needed
- async wrapper is not necessary
- state is simple but feature-specific

### Choose `BaseAsyncCubit<T>` when
- a feature loads/submits data through API calls
- you want standard loading + error messages
- the UI should react to `AsyncValue`

### Choose `BaseSearchAsyncCubit<T>` when
- users search/filter a remote list
- results are paginated
- cancelable requests matter

## Recommended implementation recipe

1. Identify the smallest correct base class.
2. Model state as either:
   - direct type
   - freezed data class
   - freezed union
3. Keep side effects and subscriptions inside the Cubit.
4. Use `close()` to clean up listeners/timers.
5. Regenerate code if freezed files changed.

## Smells to avoid

- business logic spread between widget and Cubit
- multiple overlapping loading flags when `AsyncValue` already encodes the status
- duplicating search pagination machinery in feature Cubits
- mutable state objects with manual field mutation

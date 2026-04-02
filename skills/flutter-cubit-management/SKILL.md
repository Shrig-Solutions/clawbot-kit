---
name: flutter-cubit-management
description: Implement and maintain Flutter Cubits and state classes using flutter_bloc, injectable, shared base Cubits, async state wrappers, debounced search/pagination helpers, and freezed state models. Use when adding or editing feature Cubits, async loading flows, searchable paginated state, stream-backed app state, or feature-level state management in a Flutter app. When working in Fishtechy, use its existing BaseCubit, BaseAsyncCubit, BaseSearchAsyncCubit, and AsyncValue patterns as the reference implementation.
---

# Flutter Cubit Management

Implement Cubits in the style already used by the target Flutter app, not as generic Bloc boilerplate.

## Choose the right Cubit shape

### Use plain `Cubit<T>`

Use plain `Cubit<T>` when state is local, synchronous, or stream-backed and does not need shared service helpers.

Examples include simple selection, toggles, and small session state holders.

### Use a shared base Cubit

Use a shared base Cubit like `BaseCubit<T>` when the app already centralizes common dependencies or helpers there.

This is often the right choice for feature Cubits that need service access but do not need an async wrapper.

### Use an async base Cubit

Use a shared async Cubit like `BaseAsyncCubit<T>` when the feature performs async work and should standardize:
- loading/data/message lifecycle
- API exception handling
- platform/general exception handling
- retaining previous data while surfacing errors

This is the preferred pattern for request-driven features when the app already has such a base class.

### Use a search/pagination base Cubit

Use a shared searchable base Cubit like `BaseSearchAsyncCubit<T>` when the feature needs:
- debounced search
- paginated results
- refresh/reset behavior
- cancelable in-flight requests
- sort/query state tracked with results

Do not rebuild this machinery ad hoc in feature Cubits if the app already has a reusable base.

## Core conventions

### Prefer injectable Cubits when the app uses DI

Feature Cubits commonly use dependency injection annotations like `@injectable`.

Pattern:

```dart
@injectable
class MyCubit extends BaseCubit<MyState> {
  MyCubit(MyApi api, MyDatabase database)
    : super(const MyState(...), api, database);
}
```

Match local constructor style and dependency ordering.

### Put state in its own file when state is non-trivial

If state has multiple variants or several fields, use a dedicated state file, often with freezed.

For tiny local state, a direct type like `Cubit<bool>` or `Cubit<User?>` can be fine if that matches surrounding code.

### Use freezed for expressive state

Prefer freezed when state needs:
- unions
- immutable copy semantics
- structured feature state with several fields

Keep `part` directives and generated files correct.

### Reuse the app’s async state wrapper

If the app already defines a common async wrapper such as `AsyncValue`, reuse it instead of inventing a new loading wrapper unless the feature genuinely needs something else.

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

A strong UX pattern is keeping `state.data` available while loading or showing an error message.

Prefer:

```dart
emit(AsyncValue.loading(data: state.data));
```

instead of wiping the state unless the feature requires a full reset.

### Manage streams and timers explicitly

If a Cubit listens to streams or uses timers/debounce logic:
- store the subscription/timer on the Cubit
- cancel it in `close()`
- avoid leaks and late emits

### Guard emits when lifecycle matters

Preserve `isClosed` checks or equivalent lifecycle safety in custom async or callback-heavy logic.

## Search and pagination pattern

When implementing searchable lists, prefer extending the app’s existing searchable base Cubit if one exists.

Implement only the domain fetcher and let the base class own:
- debounce
- reset
- request cancellation
- merging paginated results
- refresh behavior

## State design rules

Before creating a new Cubit/state pair, decide:
1. Is this local synchronous state, stream-backed state, async request state, or searchable paginated state?
2. Does it need a plain Cubit, shared base Cubit, async base Cubit, or search base Cubit?
3. Should state be a direct type, a freezed data class, or a freezed union?
4. Does the UI benefit from preserving old data during loading/errors?
5. Does the Cubit own any subscriptions, timers, or cancel tokens?

## Avoid these mistakes

- Do not create a brand-new async wrapper when the app already has one that fits.
- Do not duplicate search debounce/cancel/pagination logic outside the shared base class without a strong reason.
- Do not use a huge mutable Cubit state object when a small freezed model is clearer.
- Do not forget to cancel `StreamSubscription`, `Timer`, or request cancellation resources in `close()`.
- Do not emit after disposal.

## Build step

If you add or edit freezed state files, regenerate code from the Flutter project root:

```bash
dart run build_runner build -d
```

## Fishtechy reference

When working in the Fishtechy app, read `references/fishtechy-patterns.md` for concrete Cubit patterns built around `BaseCubit`, `BaseAsyncCubit`, `BaseSearchAsyncCubit`, and `AsyncValue`.

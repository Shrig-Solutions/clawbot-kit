---
name: flutter-retrofit-implementation
description: Implement and update Flutter Retrofit API clients using dio, retrofit annotations, injectable factory wiring, typed request/response models, query/path/body mapping, CancelToken support, streaming endpoints, and generated service code. Use when adding or editing REST endpoints in a Flutter app. When working in Fishtechy, use its existing RestApiService as the reference implementation.
---

# Flutter Retrofit Implementation

Implement endpoints in the same style already present in the target Flutter app.

## Quick workflow

1. Open the existing Retrofit service for the feature area.
2. Add or edit endpoint methods in place instead of creating parallel client abstractions unless the architecture clearly needs that split.
3. Reuse existing DTOs and models where possible.
4. Add new DTOs/models first if the request or response contract needs them.
5. Regenerate Retrofit output after changes.

## Default conventions

### Keep annotation-driven services cohesive

A common Flutter Retrofit pattern is a single injectable interface or a few grouped service interfaces.

Pattern:

```dart
@singleton
@RestApi()
abstract class RestApiService {
  @factoryMethod
  factory RestApiService(Dio dio, {String baseUrl}) = _RestApiService;
}
```

Prefer extending the existing service structure instead of introducing another abstraction layer without a strong reason.

### Match Retrofit annotations to the backend contract

Use the narrowest appropriate annotation:
- `@GET`
- `@POST`
- `@PATCH`
- `@DELETE`
- `@Headers`
- `@Body`
- `@Path`
- `@Query`
- `@Queries`
- `@CancelRequest`
- `@DioResponseType`

Keep paths literal and consistent with adjacent methods.

### Prefer typed responses

Return concrete models whenever the backend response shape is known.

Typical return shapes:
- `Future<Model>`
- `Future<List<Model>>`
- `Future<Paginated<Model>>`
- `Future<void>` for empty responses

Use `dynamic` only for genuinely untyped or streaming cases.

### Body/query/path rules

- Use `@Body()` for JSON payloads
- Use `@Path()` for route segments
- Use `@Query()` for scalar query parameters
- Use `@Queries()` for already-assembled query maps
- Keep parameter names aligned with backend names when explicit values are provided in the annotation

### Use named params when that area already does

For multi-argument endpoints, named params are usually clearer. Match the surrounding service style.

### Support cancellation where the UX expects it

When an endpoint is used in searchable, pageable, upload, or user-interruptible flows, consider exposing:

```dart
@CancelRequest() CancelToken? cancelToken
```

Reuse this pattern instead of inventing manual Dio cancellation wrappers.

### Support streaming explicitly

For server-sent events or streamed responses, use both headers and response type annotations.

Pattern:

```dart
@Headers({'Accept': 'text/event-stream'})
@DioResponseType(ResponseType.stream)
Future<dynamic> streamSomething(...)
```

### Keep special converters on Retrofit params

If a query parameter needs project-specific serialization, annotate the Retrofit param directly instead of moving formatting logic to call sites.

## Endpoint authoring checklist

Before adding a method, decide:
1. exact HTTP verb
2. exact route path
3. whether payload is body, path, query, or mixed
4. whether the response is typed, empty, paginated, or streamed
5. whether cancellation is needed
6. whether any field/query converters are required

## Build step

After editing Retrofit methods or related DTOs, regenerate code from the Flutter project root:

```bash
dart run build_runner build -d
```

## Fishtechy reference

When working in the Fishtechy app, read `references/fishtechy-patterns.md` for concrete endpoint shapes from its existing `RestApiService` before adding a new API surface.

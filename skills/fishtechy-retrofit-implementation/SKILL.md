---
name: fishtechy-retrofit-implementation
description: Implement and update Fishtechy-style Retrofit API clients using dio, retrofit annotations, injectable factory wiring, typed request/response models, query/path/body mapping, CancelToken support, streaming endpoints, and generated service code. Use when adding or editing REST endpoints in the Fishtechy Flutter client.
---

# Fishtechy Retrofit Implementation

Implement endpoints in the same style as `lib/core/services/rest_api/rest_api_service.dart`.

## Quick workflow

1. Open the existing Retrofit service in `lib/core/services/rest_api/rest_api_service.dart`.
2. Add or edit endpoint methods in place instead of creating parallel client abstractions.
3. Reuse existing DTOs and models where possible.
4. Add new DTOs/models first if the request or response contract needs them.
5. Regenerate Retrofit output after changes.

## Project conventions

### Keep one annotation-driven service

The current client uses a single injectable Retrofit interface:

```dart
@singleton
@RestApi()
abstract class RestApiService {
  @factoryMethod
  factory RestApiService(
    @Named('nodeDio') Dio dio,
    @Named('nodeBaseUrl') String baseUrl,
  ) => _RestApiService(dio, baseUrl: baseUrl);
}
```

Prefer extending this service instead of introducing another REST abstraction unless the codebase clearly needs separation.

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

Keep endpoint paths literal and consistent with adjacent methods.

### Prefer typed responses

Return concrete models whenever the backend response shape is known.

Examples used in the client:
- `Future<User>`
- `Future<Paginated<Feed>>`
- `Future<ServerMessage>`
- `Future<void>` for empty responses

Use `dynamic` only for intentionally untyped or streaming cases already constrained by the backend behavior.

### Body/query/path rules

- Use `@Body()` for JSON payloads
- Use `@Path()` for route segments
- Use `@Query()` for scalar query parameters
- Use `@Queries()` for already-assembled query maps
- Keep parameter names aligned with backend names when explicit values are provided in the annotation

Examples:

```dart
@GET('/users/{id}')
Future<UserPublicProfile?> getUserProfile(@Path() String id);

@PATCH('/auth/verify')
Future<LoginResponse> verifyEmailOtp({
  @Body() required VerifyEmailParams params,
});

@GET('/v2/leaderboard/{challengeId}')
Future<Paginated<LeaderboardItem>> fetchLeaderboard({
  @Path() required String challengeId,
  @Queries() required Map<String, dynamic> winnerType,
  @Query('page') required int page,
  @Query('limit') required int limit,
});
```

### Use named params when that area already does

The file commonly uses named parameters for readability on multi-argument endpoints. Match nearby style rather than mixing positional and named inconsistently.

### Support cancellation where the repo already expects it

When an endpoint is used in searchable, pageable, upload, or user-interruptible flows, consider exposing:

```dart
@CancelRequest() CancelToken? cancelToken
```

Reuse the existing pattern instead of inventing manual Dio cancellation wrappers.

### Support streaming explicitly

For server-sent events or streamed responses, use both headers and response type annotations, matching the current implementation:

```dart
@Headers({'Accept': 'text/event-stream'})
@DioResponseType(ResponseType.stream)
Future<dynamic> sendMessage(...)
```

### Keep special converters on Retrofit params

If a query parameter needs project-specific serialization, annotate the Retrofit param directly.

Example:

```dart
@Query('startDate') @NullableLocalDateTimeConverter() DateTime? startDate
```

Do not move that logic into ad hoc string formatting at call sites.

## Endpoint authoring checklist

Before adding a method, decide:
1. Exact HTTP verb
2. Exact route path
3. Whether payload is body, path, query, or mixed
4. Whether the response is typed, empty, paginated, or streamed
5. Whether cancellation is needed
6. Whether any field/query converters are required

## Build step

After editing Retrofit methods or related DTOs, regenerate code from the Flutter project root:

```bash
dart run build_runner build -d
```

## References

Read `references/patterns.md` for concrete endpoint shapes from the existing client before adding a new API surface.

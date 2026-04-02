# Fishtechy reference patterns for Flutter Retrofit implementation

## Service location

Primary service file:
- `lib/core/services/rest_api/rest_api_service.dart`

Generated output:
- `lib/core/services/rest_api/rest_api_service.g.dart`

## Base structure

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

Keep this wiring intact.

## Typical endpoint patterns

### Basic GET with path

```dart
@GET('/users/{id}')
Future<UserPublicProfile?> getUserProfile(@Path() String id);
```

### GET with pagination queries

```dart
@GET('/feeds/{type}')
Future<Paginated<Feed>> getFeed({
  @Path() required String type,
  @Query('page') required int page,
  @Query('limit') required int limit,
  @Query('includeFields') required String includeFields,
});
```

### POST with typed body

```dart
@POST('/feedbacks')
Future<FeedbackTicket> sendFeedback(@Body() FeedbackParams param);
```

### PATCH with named body/path params

```dart
@PATCH('/challenges/{challengeId}')
Future<Challenge> updateChallenge({
  @Path() required String challengeId,
  @Body() required CreateUpdateChallengeParams params,
});
```

### Void delete

```dart
@DELETE('/users')
Future<void> deleteCurrentUser();
```

### Query map passthrough

```dart
@GET('/v2/leaderboard/{challengeId}')
Future<Paginated<LeaderboardItem>> fetchLeaderboard({
  @Path() required String challengeId,
  @Queries() required Map<String, dynamic> winnerType,
  @Query('page') required int page,
  @Query('limit') required int limit,
});
```

### Cancelable request

```dart
@POST('/fish-evaluation/presigned')
Future<S3ConfigResponse> fishEvaulationPresigned(
  @Body() PresignedUrlParams params,
  @CancelRequest() CancelToken? cancelToken,
);
```

### Streaming response

```dart
@POST('/conversation')
@Headers({'Accept': 'text/event-stream'})
@DioResponseType(ResponseType.stream)
Future<dynamic> createNewConversation(
  @Body() CreateNewConversationParams params,
);
```

## Query converter example

```dart
@GET('/notifications/unread/challenges')
Future<ChallengeNotificationCount> fetchUnreadChallengeNotification({
  @Query('startDate') @NullableLocalDateTimeConverter() DateTime? startDate,
  @Query('endDate') @NullableLocalDateTimeConverter() DateTime? endDate,
});
```

## Return type guidance

- Use `Future<void>` for empty success responses.
- Use `Future<Model>` for known object payloads.
- Use `Future<Paginated<T>>` or `Future<Unpaginated<T>>` when the backend wrapper already exists.
- Use `Future<dynamic>` only for streaming or genuinely variable payloads.

## Smells to avoid

- Duplicating an endpoint in a new service without a strong architectural reason
- Returning `dynamic` when a typed model already exists
- Manually building query strings when Retrofit annotations can express them
- Hiding backend naming mismatches in callers instead of annotations/models

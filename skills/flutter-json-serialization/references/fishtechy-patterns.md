# Fishtechy reference patterns for Flutter JSON serialization

## Locations

- DTOs: `lib/core/services/rest_api/dtos/`
- Domain models: `lib/core/models/`
- Common converters/utilities:
  - `lib/core/util/local_date_converter.dart`
  - `lib/core/util/hex_color_converter.dart`
  - `lib/core/services/rest_api/utils/fish_measurement_converter.dart`

## Common class shapes

### Basic request DTO

```dart
@JsonSerializable()
class EmailParams {
  final String email;

  EmailParams({required this.email});

  factory EmailParams.fromJson(Map<String, dynamic> json) =>
      _$EmailParamsFromJson(json);

  Map<String, dynamic> toJson() => _$EmailParamsToJson(this);
}
```

### Partial update DTO with null omission

```dart
@JsonSerializable(includeIfNull: false)
class UpdateTeamParams {
  final String? name;
  final bool? private;
  final TeamCountry? country;
  @HexColorConverter()
  final Color? color;

  UpdateTeamParams({this.name, this.private, this.country, this.color});

  factory UpdateTeamParams.fromJson(Map<String, dynamic> json) =>
      _$UpdateTeamParamsFromJson(json);

  Map<String, dynamic> toJson() => _$UpdateTeamParamsToJson(this);
}
```

### Response-only DTO

```dart
@JsonSerializable(createToJson: false)
class LoginResponse {
  final String accessToken;
  final DateTime accessTokenExpiry;
  final String refreshToken;
  final DateTime refreshTokenExpiry;
  final User user;

  LoginResponse(
    this.accessToken,
    this.accessTokenExpiry,
    this.refreshToken,
    this.refreshTokenExpiry,
    this.user,
  );

  factory LoginResponse.fromJson(Map<String, Object?> json) =>
      _$LoginResponseFromJson(json);
}
```

## JsonKey naming examples

```dart
@JsonKey(name: 'ContentType')
String contentType;

@JsonKey(name: 'ContentLength')
int contentLength;
```

Use explicit names whenever backend keys differ from the Dart property name.

## Date handling

Prefer the existing converter for nullable local dates:

```dart
@NullableLocalDateTimeConverter()
DateTime? orderDate;
```

This appears in both REST DTOs and Retrofit query params.

## Flattened/manual serialization pattern

`ModerateFishEvaluationParams` uses generated JSON plus manual merging for converter-driven flattened fields.

Pattern:

```dart
Map<String, dynamic> toJson() {
  final json = _$ModerateFishEvaluationParamsToJson(this);

  if (moderatedEstimated != null) {
    final map = const ModeratedEstimatedConverter().toJson(moderatedEstimated);
    if (map != null) {
      json.addAll(map);
    }
  }

  return json;
}
```

Use this only when plain generated serialization cannot express the backend payload shape.

## Copy style

Some DTOs use hand-written `copyWith`, especially plain mutable-ish request objects. Preserve that style when editing an existing class instead of mixing patterns in the same area.

## Do not do these without cause

- Do not introduce a different serialization library.
- Do not convert an entire existing file from plain classes to freezed just for preference.
- Do not default every model to `includeIfNull: false`; use it intentionally.
- Do not hand-write JSON parsing if json_serializable plus converters can express it.

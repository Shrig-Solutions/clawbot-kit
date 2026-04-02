---
name: fishtechy-json-serialization
description: Implement and maintain Fishtechy-style Dart JSON models using json_serializable and optional freezed integration. Use when adding or editing request/response DTOs, model serialization, JsonKey mappings, custom converters, nullable handling, generated part files, or build_runner-compatible data classes in the Fishtechy REST API client.
---

# Fishtechy JSON Serialization

Implement JSON models the way the Fishtechy client already does.

## Quick workflow

1. Find the target layer:
   - Request/response DTOs usually live in `lib/core/services/rest_api/dtos/`
   - Domain models usually live in `lib/core/models/`
2. Match the surrounding style before inventing a new pattern.
3. Add or update imports, `part` directives, annotations, fields, constructors, and `fromJson`/`toJson` methods.
4. Use custom converters when the API shape is not a direct Dart-to-JSON mapping.
5. Regenerate code with `build_runner` after edits.

## Project conventions

### Prefer json_serializable defaults already in use

Follow the local pattern from nearby files instead of introducing a new serialization style.

Common patterns in this repo:
- `@JsonSerializable()` for straightforward DTOs
- `@JsonSerializable(includeIfNull: false)` for patch/update/request payloads where null fields should be omitted
- `@JsonSerializable(createToJson: false)` for response-only models
- `factory Model.fromJson(Map<String, dynamic> json) => _$ModelFromJson(json);`
- `Map<String, dynamic> toJson() => _$ModelToJson(this);`

### Keep generated wiring correct

For non-freezed classes, ensure the file includes the correct part directive:

```dart
part 'dto.g.dart';
```

For standalone model files, match the file name:

```dart
part 'app_config.g.dart';
```

If the file also uses freezed, keep both part files and the usual freezed factory shape.

### Use explicit API naming when backend keys differ

Use `@JsonKey(name: 'serverField')` whenever the backend contract does not match the Dart field name.

Examples already used in the client:
- PascalCase request keys like `ContentType`, `ContentLength`
- snake/camel mismatches
- flattened or redirected values through custom readers/converters

### Omit nulls for partial update payloads

For PATCH-style params or optional request bodies, prefer:

```dart
@JsonSerializable(includeIfNull: false)
```

This matches current DTO usage like update, report, feedback, and moderation payloads.

### Use response-only models when serializing back is unnecessary

If the app only reads a model from the backend and never sends it back, prefer:

```dart
@JsonSerializable(createToJson: false)
```

## Converters and special mapping

When the JSON contract is not direct, reuse an existing converter before creating a new one.

Check nearby utilities first, especially:
- `lib/core/util/local_date_converter.dart`
- `lib/core/util/hex_color_converter.dart`
- `lib/core/services/rest_api/utils/fish_measurement_converter.dart`

Use patterns like:
- `@NullableLocalDateTimeConverter()` for nullable date query/body values
- `@HexColorConverter()` for `Color`
- custom `JsonKey(readValue: ...)` and manual `toJson()` merging when backend payloads are flattened

If a custom converter is needed:
1. Put it in the closest existing utility area.
2. Keep it narrow and deterministic.
3. Reuse it through annotations instead of hand-parsing across multiple models.

## Freezed interplay

Use freezed when the surrounding models already use it or when immutable unions/copy semantics matter.

If the local area already uses freezed:
- keep the existing freezed pattern
- do not rewrite a plain json_serializable class into freezed without a reason
- ensure both generated files remain in sync

If the local area uses plain classes plus `copyWith`, keep that style unless there is a strong benefit to change.

## Manual toJson is acceptable when the API shape is weird

Fishtechy already has cases where generated output is extended manually.

Use manual `toJson()` only when needed, for example when:
- a converter expands one field into several payload keys
- a field is excluded from generated JSON and added manually
- nested data must be flattened for the backend

When doing this:
1. Start from generated JSON.
2. Add the custom keys.
3. Keep behavior obvious and localized.

Pattern:

```dart
Map<String, dynamic> toJson() {
  final json = _$ExampleToJson(this);
  // add or override custom fields here
  return json;
}
```

## Review checklist

Before finishing a serialization change, verify:
- field names match backend contract
- null omission behavior is intentional
- request vs response generation settings are correct
- converter annotations are present where needed
- `part` directives are correct
- imports are minimal and valid
- generated files were regenerated successfully

## Build step

From the Flutter project root, run:

```bash
dart run build_runner build -d
```

If the repo convention specifically uses Flutter tooling in context, `flutter pub run build_runner build -d` is also acceptable, but prefer the local documented command first.

## References

Read `references/patterns.md` for concrete repo-specific examples before designing a new DTO shape from scratch.

---
name: flutter-json-serialization
description: Implement and maintain Flutter and Dart JSON models using json_serializable and optional freezed integration. Use when adding or editing request/response DTOs, model serialization, JsonKey mappings, custom converters, nullable handling, generated part files, or build_runner-compatible data classes in a Flutter app. When working in Fishtechy, use its existing REST DTO and model files as the reference implementation.
---

# Flutter JSON Serialization

Implement JSON models using the conventions already present in the target Flutter app.

## Quick workflow

1. Find the target layer:
   - request/response DTOs
   - domain models
   - shared converter utilities
2. Match surrounding style before introducing a new pattern.
3. Add or update imports, `part` directives, annotations, fields, constructors, and `fromJson`/`toJson` methods.
4. Use custom converters when the API shape is not a direct Dart-to-JSON mapping.
5. Regenerate code with `build_runner` after edits.

## Default conventions

### Prefer `json_serializable` patterns already in use

Common patterns:
- `@JsonSerializable()` for straightforward DTOs
- `@JsonSerializable(includeIfNull: false)` for patch/update/request payloads where null fields should be omitted
- `@JsonSerializable(createToJson: false)` for response-only models
- `factory Model.fromJson(Map<String, dynamic> json) => _$ModelFromJson(json);`
- `Map<String, dynamic> toJson() => _$ModelToJson(this);`

Follow the local file style unless there is a strong reason to improve it consistently across that area.

### Keep generated wiring correct

For non-freezed classes, ensure the file includes the correct part directive matching the filename.

Examples:

```dart
part 'dto.g.dart';
part 'app_config.g.dart';
```

If the file also uses freezed, keep both generated parts and the usual freezed factories aligned.

### Use explicit API naming when backend keys differ

Use `@JsonKey(name: 'serverField')` whenever the backend contract does not match the Dart field name.

Use additional `JsonKey` options when needed for defaults, excluded fields, or custom readers.

### Omit nulls intentionally for partial updates

For PATCH-style params or optional request bodies, prefer:

```dart
@JsonSerializable(includeIfNull: false)
```

Use this intentionally, not by default on every class.

### Use response-only models when serializing back is unnecessary

If the app only reads a model from the backend and never sends it back, prefer:

```dart
@JsonSerializable(createToJson: false)
```

## Converters and special mapping

When the JSON contract is not direct, reuse an existing converter before creating a new one.

Typical converter cases:
- `DateTime` formatting/parsing
- `Color`
- enum variants with nonstandard wire values
- flattened or redirected values through custom readers/converters

If a custom converter is needed:
1. Put it in the closest shared utility area.
2. Keep it narrow and deterministic.
3. Reuse it through annotations instead of hand-parsing in multiple models.

## Freezed interplay

Use freezed when the surrounding models already use it or when immutable unions/copy semantics matter.

If the local area already uses plain classes plus `copyWith`, keep that style unless there is a clear benefit to change the whole pattern consistently.

## Manual `toJson()` is acceptable when the API shape is odd

Use manual `toJson()` only when needed, for example when:
- a converter expands one field into several payload keys
- a field is excluded from generated JSON and added manually
- nested data must be flattened for the backend

Pattern:

```dart
Map<String, dynamic> toJson() {
  final json = _$ExampleToJson(this);
  // add or override custom fields here
  return json;
}
```

Keep this localized and obvious.

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

If the repo convention specifically uses Flutter tooling in context, `flutter pub run build_runner build -d` is also acceptable.

## Fishtechy reference

When working in the Fishtechy app, read `references/fishtechy-patterns.md` for concrete DTO/model examples before designing a new JSON shape from scratch.

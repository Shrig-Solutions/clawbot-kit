---
name: nodejs-nestjs-backend
description: Build and review Node.js and NestJS backend services with strong API design, validation, auth, database integration, observability, and production-minded patterns.
metadata: {"clawdbot":{"emoji":"🛠️","requires":{"bins":["node"]}}}
---

# Node.js NestJS Backend

Use this skill when working on backend services built with Node.js or NestJS.

## Use this skill for

- designing or reviewing REST APIs
- adding NestJS modules, controllers, services, guards, pipes, or interceptors
- implementing authentication and authorization
- validating request payloads and environment config
- integrating databases, queues, caches, or third-party APIs
- improving logging, error handling, testing, and production readiness

## Working approach

### 1. Understand the app shape first

Before changing code, inspect the current backend structure:

```bash
rg --files | rg 'package.json|tsconfig|src|test|prisma|typeorm|drizzle|mikro-orm'
rg -n "@Module|@Controller|@Injectable|@Resolver|class-validator|ConfigModule|Passport" src
```

Check:

- framework version and package manager
- module boundaries and ownership
- validation and auth patterns already in use
- database access layer and migration tooling
- test layout and local scripts

Match the existing architecture unless there is a clear bug or scaling problem.

### 2. Prefer clean NestJS boundaries

Keep responsibilities separated:

- controllers handle transport concerns
- services contain business logic
- repositories or data access layers handle persistence
- DTOs validate and document request shapes
- guards enforce access control
- interceptors and filters handle cross-cutting behavior

Avoid putting business logic directly in controllers.

### 3. Validate every external input

For NestJS apps, prefer DTOs with `class-validator` and `class-transformer`.

Example:

```ts
import { IsEmail, IsString, MinLength } from 'class-validator';

export class CreateUserDto {
  @IsEmail()
  email!: string;

  @IsString()
  @MinLength(12)
  password!: string;
}
```

If the app uses a global validation pipe, preserve that pattern. If not, add validation deliberately rather than inconsistently.

### 4. Make error handling explicit

Prefer predictable HTTP responses:

- use NestJS exceptions for expected client and auth failures
- log unexpected failures with enough context for debugging
- do not leak secrets, tokens, SQL, or stack traces to clients

Examples of appropriate exceptions:

- `BadRequestException`
- `UnauthorizedException`
- `ForbiddenException`
- `NotFoundException`
- `ConflictException`

### 5. Treat auth and secrets as first-class concerns

When touching authentication or authorization:

- verify ownership and role checks on every sensitive route
- avoid trusting client-supplied identifiers without server-side checks
- read secrets from environment variables or the app config layer
- never hardcode credentials, tokens, or signing keys
- prefer short-lived tokens and clear refresh flows where relevant

### 6. Keep data access disciplined

For database work:

- prefer parameterized queries or ORM APIs
- avoid N+1 query patterns
- keep transactions around multi-step writes that must succeed together
- add indexes when new filters or uniqueness constraints depend on them
- keep schema changes and app changes aligned

If the app uses Prisma, TypeORM, Drizzle, or raw SQL already, follow the existing stack instead of mixing styles.

### 7. Design for operability

Backend changes should be observable and debuggable.

Prefer:

- structured logs over ad hoc strings
- correlation or request IDs when available
- health checks for critical dependencies
- timeouts and retries for outbound network calls
- idempotency for webhooks, jobs, and payment-like workflows

### 8. Test the risky path

At minimum, add or update tests for:

- request validation
- auth and permission checks
- success path behavior
- failure and edge cases
- regression coverage for the bug being fixed

Typical commands:

```bash
npm test
npm run test:e2e
npm run lint
```

Use the repo's actual scripts if they differ.

## NestJS implementation guidance

### Module design

- keep modules cohesive and feature-oriented
- export only what other modules truly need
- avoid circular dependencies where possible
- if `forwardRef()` appears necessary, check whether the design can be simplified first

### Controllers

- keep handlers thin
- return stable response shapes
- use explicit route params, query DTOs, and body DTOs
- avoid hidden behavior in decorators unless the codebase already relies on it

### Services

- keep service methods focused and composable
- inject dependencies through constructors
- move repeated cross-service logic into shared helpers only when reuse is real

### Guards, pipes, and interceptors

- guards for access decisions
- pipes for transformation and validation
- interceptors for response shaping, metrics, caching, or tracing

Do not overload one mechanism to do another job.

## API design defaults

Prefer APIs that are:

- consistent in naming
- explicit about pagination and filtering
- clear about nullable vs required fields
- versioned carefully when breaking changes are introduced

For write endpoints:

- validate inputs
- authorize early
- perform the write atomically when needed
- return a predictable shape

## Review checklist

When reviewing a Node.js or NestJS backend change, look for:

- missing validation on inbound data
- authz gaps or trust of client input
- swallowed errors or misleading success responses
- race conditions and retry hazards
- blocking or slow work on request paths
- missing transaction boundaries
- insufficient test coverage on new behavior
- config drift between code and docs

## Safety rules

- do not introduce new dependencies without clear need
- do not silently change public API behavior without updating callers or docs
- do not log secrets or full sensitive payloads
- do not bypass existing auth, validation, or audit patterns for convenience
- do not mix unrelated refactors into bug-fix work unless required

## Output style

When using this skill:

- explain backend risks in concrete terms
- reference affected routes, modules, and services
- prefer precise fixes over broad rewrites
- call out missing tests explicitly

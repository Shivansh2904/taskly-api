# Taskly API

![TypeScript](https://img.shields.io/badge/TypeScript-3178C6?style=flat&logo=typescript&logoColor=white)
![Fastify](https://img.shields.io/badge/Fastify-000000?style=flat&logo=fastify&logoColor=white)
![Prisma](https://img.shields.io/badge/Prisma-2D3748?style=flat&logo=prisma&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-4169E1?style=flat&logo=postgresql&logoColor=white)
![Vitest](https://img.shields.io/badge/Vitest-6E9F18?style=flat&logo=vitest&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-2496ED?style=flat&logo=docker&logoColor=white)
![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)
![CI](https://img.shields.io/github/actions/workflow/status/Shivansh2904/taskly-api/ci.yml?label=CI)

Production-ready task management REST API — JWT auth with refresh token rotation, typed request validation, Docker-ready.

---

## Features

- **JWT access tokens** (15 min expiry) + **refresh tokens** (7 day expiry) with rotation on every refresh
- **Projects and tasks** with status, priority, and tag support
- **Ownership enforcement** — users can only access and modify their own resources
- **Pagination and filtering** — query tasks by status, priority, tag, or assignee
- **Zod validation** on all request bodies and query parameters with structured error responses
- **Prisma ORM** with full type safety and migration support
- **Docker Compose** setup with PostgreSQL for zero-friction local development
- **GitHub Actions CI** running lint, type-check, and tests on every push and pull request

---

## API Endpoints

| Method   | Path                             | Auth     | Description                                      |
|----------|----------------------------------|----------|--------------------------------------------------|
| `POST`   | `/auth/register`                 | Public   | Register a new user account                      |
| `POST`   | `/auth/login`                    | Public   | Log in and receive access + refresh tokens       |
| `POST`   | `/auth/refresh`                  | Public   | Exchange a refresh token for a new token pair    |
| `POST`   | `/auth/logout`                   | Bearer   | Revoke the current refresh token                 |
| `GET`    | `/auth/me`                       | Bearer   | Get the authenticated user's profile             |
| `GET`    | `/projects`                      | Bearer   | List all projects owned by the current user      |
| `POST`   | `/projects`                      | Bearer   | Create a new project                             |
| `GET`    | `/projects/:id`                  | Bearer   | Get a single project by ID                       |
| `PATCH`  | `/projects/:id`                  | Bearer   | Update a project's name or description           |
| `DELETE` | `/projects/:id`                  | Bearer   | Delete a project and all its tasks               |
| `GET`    | `/projects/:id/tasks`            | Bearer   | List tasks in a project (supports filtering)     |
| `POST`   | `/projects/:id/tasks`            | Bearer   | Create a new task inside a project               |
| `GET`    | `/tasks/:id`                     | Bearer   | Get a single task by ID                          |
| `PATCH`  | `/tasks/:id`                     | Bearer   | Update task fields (status, priority, tags, etc) |
| `DELETE` | `/tasks/:id`                     | Bearer   | Delete a task                                    |
| `GET`    | `/tasks`                         | Bearer   | List all tasks for the current user              |
| `GET`    | `/tags`                          | Bearer   | List all tags used by the current user           |

### Query Parameters for Task Listing

| Parameter    | Type     | Example              | Description                          |
|--------------|----------|----------------------|--------------------------------------|
| `status`     | string   | `?status=TODO`       | Filter by status (TODO, IN_PROGRESS, DONE, CANCELLED) |
| `priority`   | string   | `?priority=HIGH`     | Filter by priority (LOW, MEDIUM, HIGH, URGENT) |
| `tag`        | string   | `?tag=backend`       | Filter by tag name                   |
| `page`       | number   | `?page=2`            | Page number (default: 1)             |
| `limit`      | number   | `?limit=20`          | Results per page (default: 10, max: 100) |

---

## Quick Start

```bash
git clone https://github.com/Shivansh2904/taskly-api
cd taskly-api && cp .env.example .env
docker-compose up -d postgres
npm install && npm run db:migrate && npm run dev
```

The API will be available at `http://localhost:3000`.

### Environment Variables

Copy `.env.example` to `.env` and fill in the values:

```env
DATABASE_URL="postgresql://postgres:postgres@localhost:5432/taskly"
JWT_ACCESS_SECRET="your-access-secret-here"
JWT_REFRESH_SECRET="your-refresh-secret-here"
JWT_ACCESS_EXPIRES_IN="15m"
JWT_REFRESH_EXPIRES_IN="7d"
PORT=3000
NODE_ENV=development
```

---

## Example curl Flows

### Register and log in

```bash
# Register a new account
curl -s -X POST http://localhost:3000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"dev@example.com","password":"s3cur3pass","name":"Dev User"}' | jq

# Log in and save tokens
TOKENS=$(curl -s -X POST http://localhost:3000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"dev@example.com","password":"s3cur3pass"}')

ACCESS=$(echo $TOKENS | jq -r '.accessToken')
REFRESH=$(echo $TOKENS | jq -r '.refreshToken')
```

### Create a project

```bash
PROJECT=$(curl -s -X POST http://localhost:3000/projects \
  -H "Authorization: Bearer $ACCESS" \
  -H "Content-Type: application/json" \
  -d '{"name":"My First Project","description":"Getting things done"}')

PROJECT_ID=$(echo $PROJECT | jq -r '.id')
echo "Created project: $PROJECT_ID"
```

### Create a task

```bash
curl -s -X POST http://localhost:3000/projects/$PROJECT_ID/tasks \
  -H "Authorization: Bearer $ACCESS" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Implement authentication",
    "description": "Add JWT-based login flow",
    "status": "TODO",
    "priority": "HIGH",
    "tags": ["backend", "auth"]
  }' | jq
```

### List tasks with a status filter

```bash
curl -s "http://localhost:3000/projects/$PROJECT_ID/tasks?status=TODO&priority=HIGH&page=1&limit=10" \
  -H "Authorization: Bearer $ACCESS" | jq
```

### Refresh tokens

```bash
NEW_TOKENS=$(curl -s -X POST http://localhost:3000/auth/refresh \
  -H "Content-Type: application/json" \
  -d "{\"refreshToken\":\"$REFRESH\"}")

ACCESS=$(echo $NEW_TOKENS | jq -r '.accessToken')
REFRESH=$(echo $NEW_TOKENS | jq -r '.refreshToken')
```

---

## Data Model

```
User
 ├── id          UUID (PK)
 ├── email       String (unique)
 ├── name        String
 ├── password    String (bcrypt hash)
 ├── createdAt   DateTime
 └── projects    Project[]
      ├── id          UUID (PK)
      ├── name        String
      ├── description String?
      ├── ownerId     UUID (FK → User)
      ├── createdAt   DateTime
      ├── updatedAt   DateTime
      └── tasks       Task[]
           ├── id          UUID (PK)
           ├── title       String
           ├── description String?
           ├── status      Enum (TODO | IN_PROGRESS | DONE | CANCELLED)
           ├── priority    Enum (LOW | MEDIUM | HIGH | URGENT)
           ├── projectId   UUID (FK → Project)
           ├── ownerId     UUID (FK → User)
           ├── dueDate     DateTime?
           ├── createdAt   DateTime
           ├── updatedAt   DateTime
           └── tags        Tag[]  (many-to-many)
                ├── id    UUID (PK)
                └── name  String (unique per user)
```

### Relationships

- A **User** owns many **Projects** and many **Tasks**.
- A **Project** belongs to one **User** and contains many **Tasks**.
- A **Task** belongs to one **Project** and one **User** (owner).
- **Tags** are many-to-many with **Tasks** and are scoped to the owning user.
- Deleting a **Project** cascades to delete all its **Tasks**.

---

## Testing

```bash
npm test
```

Runs the full test suite with [Vitest](https://vitest.dev/). Tests cover:

- Auth flows (register, login, refresh, logout, invalid tokens)
- Project CRUD and ownership enforcement
- Task CRUD, filtering, and pagination
- Zod validation error responses
- Token expiry and rotation edge cases

To run tests in watch mode:

```bash
npm run test:watch
```

To generate a coverage report:

```bash
npm run test:coverage
```

---

## Project Structure

```
taskly-api/
├── prisma/
│   ├── schema.prisma          # Database schema and models
│   └── migrations/            # Auto-generated migration files
├── src/
│   ├── config/
│   │   └── env.ts             # Validated environment config (Zod)
│   ├── plugins/
│   │   ├── auth.ts            # JWT plugin and Bearer hook
│   │   └── prisma.ts          # Prisma client plugin
│   ├── routes/
│   │   ├── auth/
│   │   │   ├── auth.routes.ts
│   │   │   ├── auth.schema.ts
│   │   │   └── auth.service.ts
│   │   ├── projects/
│   │   │   ├── projects.routes.ts
│   │   │   ├── projects.schema.ts
│   │   │   └── projects.service.ts
│   │   └── tasks/
│   │       ├── tasks.routes.ts
│   │       ├── tasks.schema.ts
│   │       └── tasks.service.ts
│   ├── lib/
│   │   ├── jwt.ts             # Token sign / verify helpers
│   │   ├── hash.ts            # bcrypt helpers
│   │   └── errors.ts          # Typed HTTP error helpers
│   ├── types/
│   │   └── index.ts           # Shared TypeScript types
│   └── app.ts                 # Fastify app factory
├── test/
│   ├── auth.test.ts
│   ├── projects.test.ts
│   └── tasks.test.ts
├── .env.example
├── .github/
│   └── workflows/
│       └── ci.yml
├── docker-compose.yml
├── package.json
├── tsconfig.json
└── vitest.config.ts
```

---

## Docker

Start the full stack (API + PostgreSQL):

```bash
docker-compose up --build
```

Start only the database for local development:

```bash
docker-compose up -d postgres
```

---

## License

[MIT](./LICENSE) — Shivansh Goyal

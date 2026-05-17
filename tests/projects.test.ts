import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { buildApp } from '../src/server.js';
import type { FastifyInstance } from 'fastify';

// ---------------------------------------------------------------------------
// Test fixtures
// ---------------------------------------------------------------------------

const TEST_USER_ID = 'user-uuid-1';
const OTHER_USER_ID = 'user-uuid-other';

const mockProject = {
  id: 'proj-uuid-1',
  name: 'My Project',
  description: 'A test project',
  ownerId: TEST_USER_ID,
  createdAt: new Date(),
  updatedAt: new Date(),
  _count: { tasks: 0 },
};

// ---------------------------------------------------------------------------
// Mocks
// ---------------------------------------------------------------------------

vi.mock('../src/plugins/prisma.js', () => ({
  default: async (fastify: any) => {
    fastify.decorate('prisma', {
      project: {
        findMany: vi.fn(),
        findFirst: vi.fn(),
        create: vi.fn(),
        update: vi.fn(),
        delete: vi.fn(),
      },
    });
  },
}));

// Helper: build a signed JWT for the test user so routes pass authentication.
async function getAuthHeader(app: FastifyInstance, userId = TEST_USER_ID): Promise<string> {
  const token = app.jwt.sign({ sub: userId }, { expiresIn: '15m' });
  return `Bearer ${token}`;
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe('Projects routes', () => {
  let app: FastifyInstance;
  let authHeader: string;

  beforeEach(async () => {
    app = await buildApp();
    await app.ready();
    authHeader = await getAuthHeader(app);
  });

  afterEach(async () => {
    await app.close();
    vi.clearAllMocks();
  });

  // -------------------------------------------------------------------------
  // POST /api/v1/projects
  // -------------------------------------------------------------------------

  describe('POST /api/v1/projects', () => {
    it('returns 201 with project data on successful creation', async () => {
      (app.prisma.project.create as ReturnType<typeof vi.fn>).mockResolvedValueOnce(mockProject);

      const response = await app.inject({
        method: 'POST',
        url: '/api/v1/projects',
        headers: { authorization: authHeader },
        payload: { name: 'My Project', description: 'A test project' },
      });

      expect(response.statusCode).toBe(201);
      const body = response.json();
      expect(body).toMatchObject({
        id: mockProject.id,
        name: mockProject.name,
        ownerId: TEST_USER_ID,
      });
    });
  });

  // -------------------------------------------------------------------------
  // GET /api/v1/projects
  // -------------------------------------------------------------------------

  describe('GET /api/v1/projects', () => {
    it('returns 200 with an array of projects belonging to the user', async () => {
      (app.prisma.project.findMany as ReturnType<typeof vi.fn>).mockResolvedValueOnce([
        mockProject,
      ]);

      const response = await app.inject({
        method: 'GET',
        url: '/api/v1/projects',
        headers: { authorization: authHeader },
      });

      expect(response.statusCode).toBe(200);
      const body = response.json();
      expect(Array.isArray(body)).toBe(true);
      expect(body).toHaveLength(1);
      expect(body[0]).toMatchObject({ id: mockProject.id, name: mockProject.name });
    });
  });

  // -------------------------------------------------------------------------
  // GET /api/v1/projects/:id  (ownership enforcement)
  // -------------------------------------------------------------------------

  describe('GET /api/v1/projects/:id', () => {
    it("returns 404 when accessing another user's project", async () => {
      // Project exists but belongs to a different owner
      const otherProject = { ...mockProject, ownerId: OTHER_USER_ID };
      // findFirst with ownerId filter returns null (enforced at query level)
      (app.prisma.project.findFirst as ReturnType<typeof vi.fn>).mockResolvedValueOnce(null);

      const response = await app.inject({
        method: 'GET',
        url: `/api/v1/projects/${otherProject.id}`,
        headers: { authorization: authHeader },
      });

      expect(response.statusCode).toBe(404);
    });
  });

  // -------------------------------------------------------------------------
  // PATCH /api/v1/projects/:id
  // -------------------------------------------------------------------------

  describe('PATCH /api/v1/projects/:id', () => {
    it('returns 200 with updated project data', async () => {
      const updatedProject = { ...mockProject, name: 'Renamed Project' };
      // findFirst returns the owned project (ownership check passes)
      (app.prisma.project.findFirst as ReturnType<typeof vi.fn>).mockResolvedValueOnce(
        mockProject,
      );
      (app.prisma.project.update as ReturnType<typeof vi.fn>).mockResolvedValueOnce(
        updatedProject,
      );

      const response = await app.inject({
        method: 'PATCH',
        url: `/api/v1/projects/${mockProject.id}`,
        headers: { authorization: authHeader },
        payload: { name: 'Renamed Project' },
      });

      expect(response.statusCode).toBe(200);
      const body = response.json();
      expect(body).toMatchObject({ name: 'Renamed Project' });
    });
  });

  // -------------------------------------------------------------------------
  // DELETE /api/v1/projects/:id
  // -------------------------------------------------------------------------

  describe('DELETE /api/v1/projects/:id', () => {
    it('returns 204 on successful deletion', async () => {
      // Ownership check passes
      (app.prisma.project.findFirst as ReturnType<typeof vi.fn>).mockResolvedValueOnce(
        mockProject,
      );
      (app.prisma.project.delete as ReturnType<typeof vi.fn>).mockResolvedValueOnce(mockProject);

      const response = await app.inject({
        method: 'DELETE',
        url: `/api/v1/projects/${mockProject.id}`,
        headers: { authorization: authHeader },
      });

      expect(response.statusCode).toBe(204);
    });
  });
});

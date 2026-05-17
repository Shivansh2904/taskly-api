import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { buildApp } from '../src/server.js';
import type { FastifyInstance } from 'fastify';
import bcrypt from 'bcrypt';

// ---------------------------------------------------------------------------
// Shared mocks
// ---------------------------------------------------------------------------

const mockUser = {
  id: 'user-uuid-1',
  email: 'alice@example.com',
  name: 'Alice',
  passwordHash: await bcrypt.hash('correct-password', 10),
  createdAt: new Date(),
  updatedAt: new Date(),
};

// We use vi.hoisted so the mock factory runs before imports resolve.
vi.mock('../src/plugins/prisma.js', () => ({
  default: async (fastify: any) => {
    fastify.decorate('prisma', {
      user: {
        findUnique: vi.fn(),
        create: vi.fn(),
      },
    });
  },
}));

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe('Auth routes', () => {
  let app: FastifyInstance;

  beforeEach(async () => {
    app = await buildApp();
    await app.ready();
  });

  afterEach(async () => {
    await app.close();
    vi.clearAllMocks();
  });

  // -------------------------------------------------------------------------
  // POST /api/v1/auth/register
  // -------------------------------------------------------------------------

  describe('POST /api/v1/auth/register', () => {
    it('returns 201 with accessToken and refreshToken on valid registration', async () => {
      // No existing user
      (app.prisma.user.findUnique as ReturnType<typeof vi.fn>).mockResolvedValueOnce(null);
      // Created user returned
      (app.prisma.user.create as ReturnType<typeof vi.fn>).mockResolvedValueOnce(mockUser);

      const response = await app.inject({
        method: 'POST',
        url: '/api/v1/auth/register',
        payload: {
          email: 'alice@example.com',
          name: 'Alice',
          password: 'correct-password',
        },
      });

      expect(response.statusCode).toBe(201);
      const body = response.json();
      expect(body).toHaveProperty('accessToken');
      expect(body).toHaveProperty('refreshToken');
      expect(typeof body.accessToken).toBe('string');
      expect(typeof body.refreshToken).toBe('string');
    });

    it('returns 409 when email is already taken', async () => {
      // Simulate existing user
      (app.prisma.user.findUnique as ReturnType<typeof vi.fn>).mockResolvedValueOnce(mockUser);

      const response = await app.inject({
        method: 'POST',
        url: '/api/v1/auth/register',
        payload: {
          email: 'alice@example.com',
          name: 'Alice',
          password: 'correct-password',
        },
      });

      expect(response.statusCode).toBe(409);
      const body = response.json();
      expect(body).toHaveProperty('message');
    });
  });

  // -------------------------------------------------------------------------
  // POST /api/v1/auth/login
  // -------------------------------------------------------------------------

  describe('POST /api/v1/auth/login', () => {
    it('returns 200 with tokens on correct credentials', async () => {
      (app.prisma.user.findUnique as ReturnType<typeof vi.fn>).mockResolvedValueOnce(mockUser);

      const response = await app.inject({
        method: 'POST',
        url: '/api/v1/auth/login',
        payload: {
          email: 'alice@example.com',
          password: 'correct-password',
        },
      });

      expect(response.statusCode).toBe(200);
      const body = response.json();
      expect(body).toHaveProperty('accessToken');
      expect(body).toHaveProperty('refreshToken');
    });

    it('returns 401 when password is wrong', async () => {
      (app.prisma.user.findUnique as ReturnType<typeof vi.fn>).mockResolvedValueOnce(mockUser);

      const response = await app.inject({
        method: 'POST',
        url: '/api/v1/auth/login',
        payload: {
          email: 'alice@example.com',
          password: 'wrong-password',
        },
      });

      expect(response.statusCode).toBe(401);
      const body = response.json();
      expect(body).toHaveProperty('message');
    });

    it('returns 401 when user does not exist', async () => {
      (app.prisma.user.findUnique as ReturnType<typeof vi.fn>).mockResolvedValueOnce(null);

      const response = await app.inject({
        method: 'POST',
        url: '/api/v1/auth/login',
        payload: {
          email: 'nobody@example.com',
          password: 'any-password',
        },
      });

      expect(response.statusCode).toBe(401);
    });
  });

  // -------------------------------------------------------------------------
  // GET /health
  // -------------------------------------------------------------------------

  describe('GET /health', () => {
    it('returns { status: "ok" }', async () => {
      const response = await app.inject({
        method: 'GET',
        url: '/health',
      });

      expect(response.statusCode).toBe(200);
      expect(response.json()).toEqual({ status: 'ok' });
    });
  });
});

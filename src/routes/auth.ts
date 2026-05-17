import { FastifyPluginAsync } from 'fastify';
import bcrypt from 'bcrypt';
import crypto from 'node:crypto';
import { config } from '../config.js';
import {
  registerBodySchema,
  loginBodySchema,
  refreshBodySchema,
  type RegisterBody,
  type LoginBody,
  type RefreshBody,
} from '../schemas/auth.js';

const BCRYPT_ROUNDS = 12;

function parseTTL(ttl: string): number {
  const units: Record<string, number> = {
    s: 1000,
    m: 60 * 1000,
    h: 60 * 60 * 1000,
    d: 24 * 60 * 60 * 1000,
  };
  const match = ttl.match(/^(\d+)([smhd])$/);
  if (!match) throw new Error(`Invalid TTL format: ${ttl}`);
  return parseInt(match[1], 10) * units[match[2]];
}

const authRoutes: FastifyPluginAsync = async (fastify) => {
  /**
   * POST /auth/register
   */
  fastify.post<{ Body: RegisterBody }>(
    '/register',
    {
      schema: {
        tags: ['Auth'],
        summary: 'Register a new user',
        body: registerBodySchema,
      },
    },
    async (request, reply) => {
      const { name, email, password } = request.body;

      const existing = await fastify.prisma.user.findUnique({
        where: { email },
        select: { id: true },
      });

      if (existing) {
        return reply.status(409).send({
          statusCode: 409,
          error: 'Conflict',
          message: 'A user with that email already exists',
        });
      }

      const passwordHash = await bcrypt.hash(password, BCRYPT_ROUNDS);

      const user = await fastify.prisma.user.create({
        data: { name, email, passwordHash },
        select: { id: true, email: true, name: true, createdAt: true },
      });

      const accessToken = fastify.jwt.sign({ id: user.id, email: user.email });

      const rawRefreshToken = crypto.randomBytes(64).toString('hex');
      const refreshExpiresAt = new Date(
        Date.now() + parseTTL(config.REFRESH_TOKEN_TTL),
      );

      await fastify.prisma.refreshToken.create({
        data: {
          token: rawRefreshToken,
          userId: user.id,
          expiresAt: refreshExpiresAt,
        },
      });

      return reply.status(201).send({
        accessToken,
        refreshToken: rawRefreshToken,
        user: {
          ...user,
          createdAt: user.createdAt.toISOString(),
        },
      });
    },
  );

  /**
   * POST /auth/login
   */
  fastify.post<{ Body: LoginBody }>(
    '/login',
    {
      schema: {
        tags: ['Auth'],
        summary: 'Authenticate and receive tokens',
        body: loginBodySchema,
      },
    },
    async (request, reply) => {
      const { email, password } = request.body;

      const user = await fastify.prisma.user.findUnique({
        where: { email },
        select: {
          id: true,
          email: true,
          name: true,
          createdAt: true,
          passwordHash: true,
        },
      });

      if (!user) {
        return reply.status(401).send({
          statusCode: 401,
          error: 'Unauthorized',
          message: 'Invalid credentials',
        });
      }

      const passwordValid = await bcrypt.compare(password, user.passwordHash);
      if (!passwordValid) {
        return reply.status(401).send({
          statusCode: 401,
          error: 'Unauthorized',
          message: 'Invalid credentials',
        });
      }

      const accessToken = fastify.jwt.sign({ id: user.id, email: user.email });

      const rawRefreshToken = crypto.randomBytes(64).toString('hex');
      const refreshExpiresAt = new Date(
        Date.now() + parseTTL(config.REFRESH_TOKEN_TTL),
      );

      await fastify.prisma.refreshToken.create({
        data: {
          token: rawRefreshToken,
          userId: user.id,
          expiresAt: refreshExpiresAt,
        },
      });

      const { passwordHash: _pw, ...safeUser } = user;

      return reply.send({
        accessToken,
        refreshToken: rawRefreshToken,
        user: {
          ...safeUser,
          createdAt: safeUser.createdAt.toISOString(),
        },
      });
    },
  );

  /**
   * POST /auth/refresh
   */
  fastify.post<{ Body: RefreshBody }>(
    '/refresh',
    {
      schema: {
        tags: ['Auth'],
        summary: 'Issue a new access token using a refresh token',
        body: refreshBodySchema,
      },
    },
    async (request, reply) => {
      const { refreshToken } = request.body;

      const stored = await fastify.prisma.refreshToken.findUnique({
        where: { token: refreshToken },
        include: { user: { select: { id: true, email: true } } },
      });

      if (!stored) {
        return reply.status(401).send({
          statusCode: 401,
          error: 'Unauthorized',
          message: 'Invalid refresh token',
        });
      }

      if (stored.expiresAt < new Date()) {
        await fastify.prisma.refreshToken.delete({ where: { id: stored.id } });
        return reply.status(401).send({
          statusCode: 401,
          error: 'Unauthorized',
          message: 'Refresh token has expired',
        });
      }

      const accessToken = fastify.jwt.sign({
        id: stored.user.id,
        email: stored.user.email,
      });

      return reply.send({ accessToken });
    },
  );

  /**
   * POST /auth/logout
   */
  fastify.post<{ Body: RefreshBody }>(
    '/logout',
    {
      schema: {
        tags: ['Auth'],
        summary: 'Revoke a refresh token',
        body: refreshBodySchema,
      },
    },
    async (request, reply) => {
      const { refreshToken } = request.body;

      await fastify.prisma.refreshToken
        .delete({ where: { token: refreshToken } })
        .catch(() => {
          /* token may already be gone — that's fine */
        });

      return reply.status(204).send();
    },
  );
};

export default authRoutes;

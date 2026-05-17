import Fastify from 'fastify';
import { ZodTypeProvider, serializerCompiler, validatorCompiler } from 'fastify-type-provider-zod';
import cors from '@fastify/cors';
import jwt from '@fastify/jwt';
import { config } from './config.js';
import prismaPlugin from './plugins/prisma.js';
import authPlugin from './plugins/auth.js';
import authRoutes from './routes/auth.js';
import projectRoutes from './routes/projects.js';
import taskRoutes from './routes/tasks.js';

export async function buildApp() {
  const app = Fastify({ logger: config.NODE_ENV !== 'test' })
    .withTypeProvider<ZodTypeProvider>();

  app.setValidatorCompiler(validatorCompiler);
  app.setSerializerCompiler(serializerCompiler);

  await app.register(cors, { origin: true });
  await app.register(jwt, { secret: config.JWT_SECRET });
  await app.register(prismaPlugin);
  await app.register(authPlugin);

  app.get('/health', async () => ({ status: 'ok', uptime: process.uptime() }));

  await app.register(authRoutes, { prefix: '/api/v1/auth' });
  await app.register(projectRoutes, { prefix: '/api/v1' });
  await app.register(taskRoutes, { prefix: '/api/v1' });

  // Map Prisma errors to HTTP codes
  app.setErrorHandler((error, _req, reply) => {
    if ((error as any).code === 'P2002') return reply.status(409).send({ error: 'Already exists' });
    if ((error as any).code === 'P2025') return reply.status(404).send({ error: 'Not found' });
    if (error.statusCode) return reply.status(error.statusCode).send({ error: error.message });
    app.log.error(error);
    return reply.status(500).send({ error: 'Internal server error' });
  });

  return app;
}

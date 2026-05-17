import { FastifyPluginAsync } from 'fastify';
import {
  createProjectBodySchema,
  updateProjectBodySchema,
  projectParamsSchema,
  projectListQuerySchema,
  projectListResponseSchema,
  projectSchema,
  type CreateProjectBody,
  type UpdateProjectBody,
  type ProjectParams,
  type ProjectListQuery,
} from '../schemas/project.js';

const projectRoutes: FastifyPluginAsync = async (fastify) => {
  /**
   * GET /projects
   * List authenticated user's projects with task count, supports pagination.
   */
  fastify.get<{ Querystring: ProjectListQuery }>(
    '/projects',
    {
      preHandler: [fastify.authenticate],
      schema: {
        tags: ['Projects'],
        summary: 'List projects for the authenticated user',
        querystring: projectListQuerySchema,
        response: {
          200: projectListResponseSchema,
        },
      },
    },
    async (request, reply) => {
      const { page, limit } = request.query;
      const userId = request.user.id;
      const skip = (page - 1) * limit;

      const [projects, total] = await Promise.all([
        fastify.prisma.project.findMany({
          where: { ownerId: userId },
          include: { _count: { select: { tasks: true } } },
          orderBy: { createdAt: 'desc' },
          skip,
          take: limit,
        }),
        fastify.prisma.project.count({ where: { ownerId: userId } }),
      ]);

      return reply.send({
        data: projects.map((p) => ({
          ...p,
          createdAt: p.createdAt.toISOString(),
          updatedAt: p.updatedAt.toISOString(),
        })),
        meta: {
          total,
          page,
          limit,
          totalPages: Math.ceil(total / limit),
        },
      });
    },
  );

  /**
   * POST /projects
   * Create a project for the authenticated user.
   */
  fastify.post<{ Body: CreateProjectBody }>(
    '/projects',
    {
      preHandler: [fastify.authenticate],
      schema: {
        tags: ['Projects'],
        summary: 'Create a new project',
        body: createProjectBodySchema,
        response: {
          201: projectSchema,
        },
      },
    },
    async (request, reply) => {
      const { name, description } = request.body;
      const userId = request.user.id;

      const project = await fastify.prisma.project.create({
        data: { name, description, ownerId: userId },
        include: { _count: { select: { tasks: true } } },
      });

      return reply.status(201).send({
        ...project,
        createdAt: project.createdAt.toISOString(),
        updatedAt: project.updatedAt.toISOString(),
      });
    },
  );

  /**
   * GET /projects/:id
   * Get a single project (must own it), includes task summary counts by status.
   */
  fastify.get<{ Params: ProjectParams }>(
    '/projects/:id',
    {
      preHandler: [fastify.authenticate],
      schema: {
        tags: ['Projects'],
        summary: 'Get a project by ID',
        params: projectParamsSchema,
      },
    },
    async (request, reply) => {
      const { id } = request.params;
      const userId = request.user.id;

      const project = await fastify.prisma.project.findFirst({
        where: { id, ownerId: userId },
        include: { _count: { select: { tasks: true } } },
      });

      if (!project) {
        return reply.status(404).send({
          statusCode: 404,
          error: 'Not Found',
          message: 'Project not found',
        });
      }

      // Build task status summary counts
      const statusCounts = await fastify.prisma.task.groupBy({
        by: ['status'],
        where: { projectId: id },
        _count: { status: true },
      });

      const taskSummary = statusCounts.reduce<Record<string, number>>(
        (acc, item) => {
          acc[item.status] = item._count.status;
          return acc;
        },
        {},
      );

      return reply.send({
        ...project,
        createdAt: project.createdAt.toISOString(),
        updatedAt: project.updatedAt.toISOString(),
        taskSummary,
      });
    },
  );

  /**
   * PATCH /projects/:id
   * Update a project's name/description (must own it).
   */
  fastify.patch<{ Params: ProjectParams; Body: UpdateProjectBody }>(
    '/projects/:id',
    {
      preHandler: [fastify.authenticate],
      schema: {
        tags: ['Projects'],
        summary: 'Update a project',
        params: projectParamsSchema,
        body: updateProjectBodySchema,
        response: {
          200: projectSchema,
        },
      },
    },
    async (request, reply) => {
      const { id } = request.params;
      const userId = request.user.id;

      const existing = await fastify.prisma.project.findFirst({
        where: { id, ownerId: userId },
        select: { id: true },
      });

      if (!existing) {
        return reply.status(404).send({
          statusCode: 404,
          error: 'Not Found',
          message: 'Project not found',
        });
      }

      const project = await fastify.prisma.project.update({
        where: { id },
        data: request.body,
        include: { _count: { select: { tasks: true } } },
      });

      return reply.send({
        ...project,
        createdAt: project.createdAt.toISOString(),
        updatedAt: project.updatedAt.toISOString(),
      });
    },
  );

  /**
   * DELETE /projects/:id
   * Delete a project (must own it).
   */
  fastify.delete<{ Params: ProjectParams }>(
    '/projects/:id',
    {
      preHandler: [fastify.authenticate],
      schema: {
        tags: ['Projects'],
        summary: 'Delete a project',
        params: projectParamsSchema,
      },
    },
    async (request, reply) => {
      const { id } = request.params;
      const userId = request.user.id;

      const existing = await fastify.prisma.project.findFirst({
        where: { id, ownerId: userId },
        select: { id: true },
      });

      if (!existing) {
        return reply.status(404).send({
          statusCode: 404,
          error: 'Not Found',
          message: 'Project not found',
        });
      }

      await fastify.prisma.project.delete({ where: { id } });

      return reply.status(204).send();
    },
  );
};

export default projectRoutes;

import { FastifyPluginAsync } from 'fastify';
import {
  createTaskBodySchema,
  updateTaskBodySchema,
  taskParamsSchema,
  taskProjectParamsSchema,
  taskListQuerySchema,
  taskListResponseSchema,
  taskSchema,
  type CreateTaskBody,
  type UpdateTaskBody,
  type TaskParams,
  type TaskListQuery,
} from '../schemas/task.js';
import { z } from 'zod';

/** Reusable helper — returns the project if the user owns it, otherwise sends 404 */
async function requireProjectOwnership(
  fastify: Parameters<FastifyPluginAsync>[0],
  projectId: string,
  userId: string,
  reply: Parameters<Parameters<FastifyPluginAsync>[0]['get']>[2],
) {
  const project = await fastify.prisma.project.findFirst({
    where: { id: projectId, ownerId: userId },
    select: { id: true },
  });

  if (!project) {
    reply.status(404).send({
      statusCode: 404,
      error: 'Not Found',
      message: 'Project not found',
    });
    return null;
  }

  return project;
}

const taskProjectParamsWithTaskSchema = taskParamsSchema; // { projectId, taskId }
const taskProjectOnlyParamsSchema = taskProjectParamsSchema; // { projectId }

const taskRoutes: FastifyPluginAsync = async (fastify) => {
  /**
   * GET /projects/:projectId/tasks
   * List tasks for a project, supports filtering by status/priority and pagination.
   */
  fastify.get<{
    Params: z.infer<typeof taskProjectOnlyParamsSchema>;
    Querystring: TaskListQuery;
  }>(
    '/projects/:projectId/tasks',
    {
      preHandler: [fastify.authenticate],
      schema: {
        tags: ['Tasks'],
        summary: 'List tasks for a project',
        params: taskProjectOnlyParamsSchema,
        querystring: taskListQuerySchema,
        response: {
          200: taskListResponseSchema,
        },
      },
    },
    async (request, reply) => {
      const { projectId } = request.params;
      const { page, limit, status, priority, assigneeId } = request.query;
      const userId = request.user.id;

      const project = await requireProjectOwnership(fastify, projectId, userId, reply);
      if (!project) return;

      const skip = (page - 1) * limit;

      const where = {
        projectId,
        ...(status ? { status } : {}),
        ...(priority ? { priority } : {}),
        ...(assigneeId ? { assigneeId } : {}),
      };

      const [tasks, total] = await Promise.all([
        fastify.prisma.task.findMany({
          where,
          include: {
            assignee: { select: { id: true, name: true, email: true } },
            tags: true,
          },
          orderBy: { createdAt: 'desc' },
          skip,
          take: limit,
        }),
        fastify.prisma.task.count({ where }),
      ]);

      return reply.send({
        data: tasks.map((t) => ({
          ...t,
          dueDate: t.dueDate ? t.dueDate.toISOString() : null,
          createdAt: t.createdAt.toISOString(),
          updatedAt: t.updatedAt.toISOString(),
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
   * POST /projects/:projectId/tasks
   * Create a task under a project.
   */
  fastify.post<{
    Params: z.infer<typeof taskProjectOnlyParamsSchema>;
    Body: CreateTaskBody;
  }>(
    '/projects/:projectId/tasks',
    {
      preHandler: [fastify.authenticate],
      schema: {
        tags: ['Tasks'],
        summary: 'Create a task in a project',
        params: taskProjectOnlyParamsSchema,
        body: createTaskBodySchema,
        response: {
          201: taskSchema,
        },
      },
    },
    async (request, reply) => {
      const { projectId } = request.params;
      const userId = request.user.id;
      const { tagIds, dueDate, ...rest } = request.body;

      const project = await requireProjectOwnership(fastify, projectId, userId, reply);
      if (!project) return;

      const task = await fastify.prisma.task.create({
        data: {
          ...rest,
          projectId,
          dueDate: dueDate ? new Date(dueDate) : undefined,
          tags: tagIds && tagIds.length > 0
            ? { connect: tagIds.map((id) => ({ id })) }
            : undefined,
        },
        include: {
          assignee: { select: { id: true, name: true, email: true } },
          tags: true,
        },
      });

      return reply.status(201).send({
        ...task,
        dueDate: task.dueDate ? task.dueDate.toISOString() : null,
        createdAt: task.createdAt.toISOString(),
        updatedAt: task.updatedAt.toISOString(),
      });
    },
  );

  /**
   * GET /projects/:projectId/tasks/:taskId
   * Get a single task with tags.
   */
  fastify.get<{ Params: TaskParams }>(
    '/projects/:projectId/tasks/:taskId',
    {
      preHandler: [fastify.authenticate],
      schema: {
        tags: ['Tasks'],
        summary: 'Get a single task',
        params: taskProjectParamsWithTaskSchema,
        response: {
          200: taskSchema,
        },
      },
    },
    async (request, reply) => {
      const { projectId, taskId } = request.params;
      const userId = request.user.id;

      const project = await requireProjectOwnership(fastify, projectId, userId, reply);
      if (!project) return;

      const task = await fastify.prisma.task.findFirst({
        where: { id: taskId, projectId },
        include: {
          assignee: { select: { id: true, name: true, email: true } },
          tags: true,
        },
      });

      if (!task) {
        return reply.status(404).send({
          statusCode: 404,
          error: 'Not Found',
          message: 'Task not found',
        });
      }

      return reply.send({
        ...task,
        dueDate: task.dueDate ? task.dueDate.toISOString() : null,
        createdAt: task.createdAt.toISOString(),
        updatedAt: task.updatedAt.toISOString(),
      });
    },
  );

  /**
   * PATCH /projects/:projectId/tasks/:taskId
   * Update task fields.
   */
  fastify.patch<{ Params: TaskParams; Body: UpdateTaskBody }>(
    '/projects/:projectId/tasks/:taskId',
    {
      preHandler: [fastify.authenticate],
      schema: {
        tags: ['Tasks'],
        summary: 'Update a task',
        params: taskProjectParamsWithTaskSchema,
        body: updateTaskBodySchema,
        response: {
          200: taskSchema,
        },
      },
    },
    async (request, reply) => {
      const { projectId, taskId } = request.params;
      const userId = request.user.id;
      const { tagIds, dueDate, ...rest } = request.body;

      const project = await requireProjectOwnership(fastify, projectId, userId, reply);
      if (!project) return;

      const existing = await fastify.prisma.task.findFirst({
        where: { id: taskId, projectId },
        select: { id: true },
      });

      if (!existing) {
        return reply.status(404).send({
          statusCode: 404,
          error: 'Not Found',
          message: 'Task not found',
        });
      }

      const task = await fastify.prisma.task.update({
        where: { id: taskId },
        data: {
          ...rest,
          ...(dueDate !== undefined
            ? { dueDate: dueDate ? new Date(dueDate) : null }
            : {}),
          ...(tagIds !== undefined
            ? { tags: { set: tagIds.map((id) => ({ id })) } }
            : {}),
        },
        include: {
          assignee: { select: { id: true, name: true, email: true } },
          tags: true,
        },
      });

      return reply.send({
        ...task,
        dueDate: task.dueDate ? task.dueDate.toISOString() : null,
        createdAt: task.createdAt.toISOString(),
        updatedAt: task.updatedAt.toISOString(),
      });
    },
  );

  /**
   * DELETE /projects/:projectId/tasks/:taskId
   * Delete a task.
   */
  fastify.delete<{ Params: TaskParams }>(
    '/projects/:projectId/tasks/:taskId',
    {
      preHandler: [fastify.authenticate],
      schema: {
        tags: ['Tasks'],
        summary: 'Delete a task',
        params: taskProjectParamsWithTaskSchema,
      },
    },
    async (request, reply) => {
      const { projectId, taskId } = request.params;
      const userId = request.user.id;

      const project = await requireProjectOwnership(fastify, projectId, userId, reply);
      if (!project) return;

      const existing = await fastify.prisma.task.findFirst({
        where: { id: taskId, projectId },
        select: { id: true },
      });

      if (!existing) {
        return reply.status(404).send({
          statusCode: 404,
          error: 'Not Found',
          message: 'Task not found',
        });
      }

      await fastify.prisma.task.delete({ where: { id: taskId } });

      return reply.status(204).send();
    },
  );
};

export default taskRoutes;

import { z } from 'zod';

export const TaskStatusEnum = z.enum([
  'TODO',
  'IN_PROGRESS',
  'IN_REVIEW',
  'DONE',
  'CANCELLED',
]);

export const TaskPriorityEnum = z.enum(['LOW', 'MEDIUM', 'HIGH', 'URGENT']);

export const createTaskBodySchema = z.object({
  title: z.string().min(1).max(500),
  description: z.string().max(5000).optional(),
  status: TaskStatusEnum.default('TODO'),
  priority: TaskPriorityEnum.default('MEDIUM'),
  dueDate: z.string().datetime().optional(),
  assigneeId: z.string().cuid().optional(),
  tagIds: z.array(z.string().cuid()).optional(),
});

export const updateTaskBodySchema = z.object({
  title: z.string().min(1).max(500).optional(),
  description: z.string().max(5000).nullable().optional(),
  status: TaskStatusEnum.optional(),
  priority: TaskPriorityEnum.optional(),
  dueDate: z.string().datetime().nullable().optional(),
  assigneeId: z.string().cuid().nullable().optional(),
  tagIds: z.array(z.string().cuid()).optional(),
});

export const taskParamsSchema = z.object({
  projectId: z.string().cuid(),
  taskId: z.string().cuid(),
});

export const taskProjectParamsSchema = z.object({
  projectId: z.string().cuid(),
});

export const taskListQuerySchema = z.object({
  page: z.coerce.number().int().positive().default(1),
  limit: z.coerce.number().int().positive().max(100).default(20),
  status: TaskStatusEnum.optional(),
  priority: TaskPriorityEnum.optional(),
  assigneeId: z.string().cuid().optional(),
});

export const tagSchema = z.object({
  id: z.string(),
  name: z.string(),
  colour: z.string(),
});

export const taskSchema = z.object({
  id: z.string(),
  title: z.string(),
  description: z.string().nullable(),
  status: TaskStatusEnum,
  priority: TaskPriorityEnum,
  dueDate: z.string().nullable(),
  projectId: z.string(),
  assigneeId: z.string().nullable(),
  assignee: z
    .object({
      id: z.string(),
      name: z.string(),
      email: z.string(),
    })
    .nullable()
    .optional(),
  tags: z.array(tagSchema).optional(),
  createdAt: z.string(),
  updatedAt: z.string(),
});

export const taskListResponseSchema = z.object({
  data: z.array(taskSchema),
  meta: z.object({
    total: z.number(),
    page: z.number(),
    limit: z.number(),
    totalPages: z.number(),
  }),
});

export type CreateTaskBody = z.infer<typeof createTaskBodySchema>;
export type UpdateTaskBody = z.infer<typeof updateTaskBodySchema>;
export type TaskParams = z.infer<typeof taskParamsSchema>;
export type TaskListQuery = z.infer<typeof taskListQuerySchema>;

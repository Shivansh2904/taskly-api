import { z } from 'zod';

export const createProjectBodySchema = z.object({
  name: z.string().min(1).max(200),
  description: z.string().max(1000).optional(),
});

export const updateProjectBodySchema = z.object({
  name: z.string().min(1).max(200).optional(),
  description: z.string().max(1000).nullable().optional(),
});

export const projectParamsSchema = z.object({
  id: z.string().cuid(),
});

export const projectListQuerySchema = z.object({
  page: z.coerce.number().int().positive().default(1),
  limit: z.coerce.number().int().positive().max(100).default(20),
});

export const projectSchema = z.object({
  id: z.string(),
  name: z.string(),
  description: z.string().nullable(),
  ownerId: z.string(),
  createdAt: z.string(),
  updatedAt: z.string(),
  _count: z
    .object({
      tasks: z.number(),
    })
    .optional(),
});

export const projectListResponseSchema = z.object({
  data: z.array(projectSchema),
  meta: z.object({
    total: z.number(),
    page: z.number(),
    limit: z.number(),
    totalPages: z.number(),
  }),
});

export type CreateProjectBody = z.infer<typeof createProjectBodySchema>;
export type UpdateProjectBody = z.infer<typeof updateProjectBodySchema>;
export type ProjectParams = z.infer<typeof projectParamsSchema>;
export type ProjectListQuery = z.infer<typeof projectListQuerySchema>;

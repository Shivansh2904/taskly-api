import { FastifyReply, FastifyRequest } from 'fastify';

/**
 * Standalone preHandler that verifies the Bearer JWT and attaches the
 * decoded payload to `request.user`.  Register it on individual routes or
 * as a scoped hook — whichever the route file prefers.
 */
export async function requireAuth(
  request: FastifyRequest,
  reply: FastifyReply,
): Promise<void> {
  return request.server.authenticate(request, reply);
}

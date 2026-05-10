declare const process: { env: Record<string, string | undefined> };
declare const Buffer: {
  from(input: string, encoding?: string): { length: number };
};

declare module "fastify" {
  export type FastifyInstance = any;
  export type FastifyPluginAsync = any;
  export type FastifyRequest = any;
  export type FastifyReply = any;
  const Fastify: any;
  export default Fastify;
}

declare module "zod" {
  export const z: any;
}

declare module "mongoose" {
  const mongoose: any;
  export default mongoose;
  export const Schema: any;
  export const model: any;
  export type InferSchemaType<T> = any;
}

declare module "jsonwebtoken" {
  const jwt: any;
  export default jwt;
}

declare module "node-cron" {
  const cron: any;
  export default cron;
}

declare module "@fastify/cors" { const x: any; export default x; }
declare module "@fastify/helmet" { const x: any; export default x; }
declare module "@fastify/rate-limit" { const x: any; export default x; }
declare module "@fastify/sensible" { const x: any; export default x; }
declare module "socket.io" { export const Server: any; }
declare module "nanoid" { export const nanoid: any; }
declare module "framer-motion" { export const motion: any; }
declare module "swr" { const useSWR: any; export default useSWR; }
declare module "lucide-react" { export const Home: any; export const Users: any; export const UserRound: any; export const Shield: any; export const Trophy: any; export const Swords: any; }
declare module "next" { export type Metadata = any; }
declare module "next/navigation" { export function notFound(): never; }
declare module "react" { export type ReactNode = any; }
declare module "*.css" { const content: any; export default content; }

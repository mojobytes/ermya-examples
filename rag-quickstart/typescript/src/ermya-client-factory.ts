/**
 * Construct the Ermya SDK client from config.
 *
 * The TS SDK takes a scheme-prefixed endpoint URL (unlike the Python SDK, which
 * takes a bare host:port). The pipeline depends on the minimal ErmyaClientLike
 * surface below so it can be mocked in tests without the real SDK. Endpoint
 * composition lives in ./endpoint so it is testable without loading the SDK.
 */

import { ErmyaClient } from "@ermya/client";

import type { ErmyaConfig } from "./config-loader.js";
import { composeEndpoint } from "./endpoint.js";

export interface ErmyaClientLike {
  createTenant(options: { tenantId: string; dimension: number }): Promise<unknown>;
  insert(options: {
    tenantId: string;
    vector: number[];
    metadata: Record<string, unknown>;
  }): Promise<{ id: bigint | number }>;
  search(options: {
    tenantId: string;
    vector: number[];
    k: number;
  }): Promise<{ results: Array<{ id: bigint | number; distance: number; metadata?: Record<string, unknown> }> }>;
}

export function createClient(config: ErmyaConfig): ErmyaClientLike {
  const client = new ErmyaClient({
    endpoint: composeEndpoint(config.host, config.port, config.secure),
    jwtToken: config.apiKey,
    useTls: config.secure,
  });
  return client as unknown as ErmyaClientLike;
}

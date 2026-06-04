/**
 * Construct the Tessera SDK client from config.
 *
 * The TS SDK takes a scheme-prefixed endpoint URL (unlike the Python SDK, which
 * takes a bare host:port). The pipeline depends on the minimal TesseraClientLike
 * surface below so it can be mocked in tests without the real SDK. Endpoint
 * composition lives in ./endpoint so it is testable without loading the SDK.
 */

import { TesseraClient } from "@tesseradb/client";

import type { TesseraConfig } from "./config-loader.js";
import { composeEndpoint } from "./endpoint.js";

export interface TesseraClientLike {
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

export function createClient(config: TesseraConfig): TesseraClientLike {
  const client = new TesseraClient({
    endpoint: composeEndpoint(config.host, config.port, config.secure),
    jwtToken: config.apiKey,
    useTls: config.secure,
  });
  return client as unknown as TesseraClientLike;
}

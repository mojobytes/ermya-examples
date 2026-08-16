/**
 * Compose the scheme-prefixed endpoint URL the TS SDK expects.
 *
 * Kept in its own dependency-free module so it is unit-testable without loading
 * the gRPC SDK stack that ermya-client-factory pulls in.
 */

export function composeEndpoint(host: string, port: number, secure: boolean): string {
  const scheme = secure ? "https" : "http";
  return `${scheme}://${host}:${port}`;
}

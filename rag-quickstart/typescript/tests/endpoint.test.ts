import { composeEndpoint } from "../src/endpoint.js";

describe("composeEndpoint", () => {
  it("uses http when not secure", () => {
    expect(composeEndpoint("localhost", 50051, false)).toBe("http://localhost:50051");
  });

  it("uses https when secure", () => {
    expect(composeEndpoint("api.example.com", 443, true)).toBe(
      "https://api.example.com:443",
    );
  });
});

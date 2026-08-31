import assert from "node:assert/strict";
import test from "node:test";

import { authorizeAndLogDownload, uploadProductAsset } from "../src/services/assetTransfers.js";

test("uploadProductAsset completes a signed upload", async () => {
  const calls = [];
  const api = {
    request: async (path, options) => {
      calls.push({ path, options });
      if (path.endsWith("upload-target/")) return {
        uuid: "asset::1",
        presigned_upload: { upload_url: "https://s3.example/upload", method: "PUT", headers: { "Content-Type": "text/plain" } },
      };
      return { uuid: "asset::1", asset_status: "verified" };
    },
  };
  const file = { name: "guide.txt", type: "text/plain", size: 5, arrayBuffer: async () => new Uint8Array([104, 101, 108, 108, 111]).buffer };
  const fetchCalls = [];

  const result = await uploadProductAsset({
    api,
    productUuid: "product::1",
    file,
    fetchImpl: async (...args) => { fetchCalls.push(args); return { ok: true, status: 200 }; },
  });

  assert.equal(result.asset_status, "verified");
  assert.equal(calls.length, 2);
  assert.equal(JSON.parse(calls[0].options.body).product_uuid, "product::1");
  assert.equal(fetchCalls[0][0], "https://s3.example/upload");
  assert.equal(fetchCalls[0][1].body, file);
  assert.equal(JSON.parse(calls[1].options.body).size_bytes, 5);
});

test("authorizeAndLogDownload consumes the delivery token before returning the URL", async () => {
  const calls = [];
  const api = { request: async (path, options) => {
    calls.push({ path, options });
    if (path.endsWith("deliver/")) return { download_url: "https://s3.example/file", delivery_token: "token-1" };
    return { uuid: "download::1" };
  } };

  const url = await authorizeAndLogDownload({ api, orderUuid: "order::1", assetUuid: "asset::1" });

  assert.equal(url, "https://s3.example/file");
  assert.equal(JSON.parse(calls[0].options.body).order_uuid, "order::1");
  assert.equal(calls[1].options.headers["X-Asset-Delivery-Token"], "token-1");
});

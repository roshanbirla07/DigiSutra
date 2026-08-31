import { API_PATHS } from "../constants/app.js";

export async function sha256Hex(file, cryptoImpl = globalThis.crypto) {
  if (!cryptoImpl?.subtle) return null;
  const digest = await cryptoImpl.subtle.digest("SHA-256", await file.arrayBuffer());
  return Array.from(new Uint8Array(digest), (byte) => byte.toString(16).padStart(2, "0")).join("");
}

export async function uploadProductAsset({ api, productUuid, file, fetchImpl = globalThis.fetch }) {
  if (!file?.name || typeof file.arrayBuffer !== "function") throw new Error("Choose a product file to upload.");
  const target = await api.request(API_PATHS.assetUploadTarget, {
    method: "POST",
    body: JSON.stringify({
      product_uuid: productUuid,
      original_filename: file.name,
      content_type: file.type || "application/octet-stream",
      size_bytes: file.size,
    }),
  });
  const signed = target.presigned_upload;
  if (!signed?.upload_url) throw new Error("The upload target did not include a signed URL.");

  const uploaded = await fetchImpl(signed.upload_url, {
    method: signed.method || "PUT",
    headers: signed.headers || { "Content-Type": file.type || "application/octet-stream" },
    body: file,
  });
  if (!uploaded.ok) throw new Error(`Product file upload failed (${uploaded.status}).`);

  const checksum = await sha256Hex(file);
  return api.request(API_PATHS.assetUploadComplete(target.uuid), {
    method: "POST",
    body: JSON.stringify({ size_bytes: file.size, ...(checksum ? { checksum_sha256: checksum } : {}) }),
  });
}

export async function authorizeAndLogDownload({ api, orderUuid, assetUuid }) {
  const delivery = await api.request(API_PATHS.assetDeliver(assetUuid), {
    method: "POST",
    body: JSON.stringify({ order_uuid: orderUuid }),
  });
  if (!delivery?.download_url || !delivery?.delivery_token) throw new Error("The download is not ready.");
  await api.request(API_PATHS.assetDownloadLog(assetUuid), {
    method: "POST",
    headers: { "X-Asset-Delivery-Token": delivery.delivery_token },
    body: JSON.stringify({}),
  });
  return delivery.download_url;
}

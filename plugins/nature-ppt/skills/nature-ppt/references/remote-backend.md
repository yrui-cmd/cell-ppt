# Optional remote vectorization backend

Nature PPT works locally without credentials. A hosted vectorizer is optional and is useful when a team maintains a better segmentation model or wants to centralize compute.

## Request contract

- Method: `POST`
- URL: configured by `--endpoint` or `NATURE_PPT_VECTOR_URL`
- Transport: HTTPS; plain HTTP is accepted only for an explicitly enabled localhost test
- Body: original image bytes
- Headers:
  - `Content-Type: application/octet-stream`
  - `Accept: image/svg+xml, application/json`
  - `X-Nature-PPT-Profile: editable` or `maximum-fidelity`
  - `X-Source-Filename: <original filename>`
  - optional `Authorization: Bearer <token>`
- Response: raw SVG, or JSON containing an `svg` string

The returned SVG must have a positive `viewBox`, stable IDs, no embedded raster image, and no external references. It is normalized and validated locally before PowerPoint sees it.

## Credential handling

Store the token in a user-owned file outside the repository and pass its path with `--token-file`, or set `NATURE_PPT_VECTOR_TOKEN_FILE`. Never put the token itself in a command, source file, manifest, screenshot, log, or deliverable.

## Privacy boundary

Do not select the remote backend automatically unless an endpoint is already configured. Upload only the image the user placed in scope. If the service has cost, retention, or consent requirements, satisfy them before upload.

import { AwsClient } from "aws4fetch";
import type { Config } from "./config.ts";

/** Presigned GET on the private bucket (django-storages querystring_auth equivalent). */
async function presignGet(cfg: Config["r2"], key: string): Promise<string> {
  const aws = new AwsClient({
    accessKeyId: cfg.accessKeyId,
    secretAccessKey: cfg.secretAccessKey,
    service: "s3",
    region: "auto",
  });
  const path = key.split("/").map(encodeURIComponent).join("/");
  const url = `${cfg.endpoint}/${cfg.privateBucket}/${path}?X-Amz-Expires=${cfg.signedExpire}`;
  const signed = await aws.sign(url, { method: "GET", aws: { signQuery: true } });
  return signed.url;
}

// Indirection so handler tests can stub presigning.
export const r2 = { presignGet };

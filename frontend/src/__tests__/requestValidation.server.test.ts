import { mkdtempSync, mkdirSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import path from 'node:path';
import { PassThrough } from 'node:stream';
import { finished } from 'node:stream/promises';

import {
  assertValidRequestTarget,
  rejectMalformedRequestTarget,
} from '../../server/requestValidation.js';
import { serveStatic } from '../../server/staticAssets.js';

type RecordedResponse = {
  body: string;
  headers: Record<string, string>;
  headersSent: boolean;
  statusCode: number | null;
  destroy: jest.Mock;
  end: (body?: string) => void;
  writeHead: (statusCode: number, headers: Record<string, string>) => void;
};

const createRecordedResponse = (): RecordedResponse => {
  const response: RecordedResponse = {
    body: '',
    headers: {},
    headersSent: false,
    statusCode: null,
    destroy: jest.fn(),
    end(body = '') {
      response.body = body;
      response.headersSent = true;
    },
    writeHead(statusCode, headers) {
      response.statusCode = statusCode;
      response.headers = headers;
      response.headersSent = true;
    },
  };
  return response;
};

describe('SSR request-target validation', () => {
  afterEach(() => {
    jest.restoreAllMocks();
  });

  it.each([
    '/php-cgi/php-cgi.exe?%ADd',
    '/xampp/php-cgi.exe?arg=%',
    '/assets/%E0%A4%A',
    '/path?value=%GG',
  ])('rejects malformed percent encoding in %s', requestTarget => {
    expect(() => assertValidRequestTarget(requestTarget)).toThrow(
      'Malformed request target.'
    );
  });

  it.each([
    '/',
    '/astrophotography/milky-way',
    '/assets/app.js?v=1',
    '/search?value=Milky%20Way',
    '/safe?redirect=%2Fastrophotography',
  ])('accepts a valid request target in %s', requestTarget => {
    expect(() => assertValidRequestTarget(requestTarget)).not.toThrow();
  });

  it('returns 400 and logs a security event without throwing', () => {
    const response = createRecordedResponse();
    const log = jest.spyOn(console, 'log').mockImplementation(() => undefined);

    const rejected = rejectMalformedRequestTarget(
      {
        method: 'GET',
        url: '/php-cgi/php-cgi.exe?%ADd',
      },
      response,
      100,
      'request-123',
      125
    );

    expect(rejected).toBe(true);
    expect(response.statusCode).toBe(400);
    expect(response.headers).toEqual({
      'Content-Type': 'text/plain; charset=utf-8',
    });
    expect(response.body).toBe('Bad Request');
    expect(JSON.parse(String(log.mock.calls[0]?.[0]))).toMatchObject({
      service: 'frontend-ssr',
      level: 'WARNING',
      request_id: 'request-123',
      event: 'request_rejected',
      kind: 'security_probe',
      method: 'GET',
      path: '/php-cgi/php-cgi.exe?%ADd',
      reason: 'malformed_request_target',
      status: 400,
      duration_ms: 25,
    });
  });

  it('continues handling valid requests after rejecting malformed input', () => {
    const malformedResponse = createRecordedResponse();
    const validResponse = createRecordedResponse();
    jest.spyOn(console, 'log').mockImplementation(() => undefined);

    expect(
      rejectMalformedRequestTarget(
        { method: 'GET', url: '/assets/%' },
        malformedResponse,
        100,
        'request-bad',
        101
      )
    ).toBe(true);
    expect(
      rejectMalformedRequestTarget(
        { method: 'GET', url: '/health' },
        validResponse,
        102,
        'request-good',
        103
      )
    ).toBe(false);
    expect(validResponse.statusCode).toBeNull();
  });
});

describe('SSR static path containment', () => {
  let rootDir: string;
  let clientDistDir: string;

  beforeEach(() => {
    rootDir = mkdtempSync(path.join(tmpdir(), 'portfolio-static-'));
    clientDistDir = path.join(rootDir, 'dist');
    mkdirSync(clientDistDir);
  });

  afterEach(() => {
    rmSync(rootDir, { recursive: true, force: true });
  });

  it('treats malformed encoded static paths as non-static', async () => {
    const response = new PassThrough() as PassThrough & {
      writeHead: jest.Mock;
    };
    response.writeHead = jest.fn();

    await expect(
      serveStatic({ url: '/assets/%' }, response, clientDistDir)
    ).resolves.toBe(false);
  });

  it('continues serving normal static assets', async () => {
    const assetsDir = path.join(clientDistDir, 'assets');
    mkdirSync(assetsDir);
    writeFileSync(path.join(assetsDir, 'app.js'), 'console.log("ok");');
    const response = new PassThrough() as PassThrough & {
      writeHead: jest.Mock;
    };
    response.writeHead = jest.fn();
    response.resume();

    await expect(
      serveStatic({ url: '/assets/app.js' }, response, clientDistDir)
    ).resolves.toBe(true);
    await finished(response);

    expect(response.writeHead).toHaveBeenCalledWith(
      200,
      expect.objectContaining({
        'Content-Type': 'application/javascript; charset=utf-8',
      })
    );
  });

  it('rejects encoded traversal into a sibling with the same path prefix', async () => {
    const siblingDir = `${clientDistDir}-escape`;
    mkdirSync(siblingDir);
    writeFileSync(path.join(siblingDir, 'probe.js'), 'not public');
    const response = new PassThrough() as PassThrough & {
      writeHead: jest.Mock;
    };
    response.writeHead = jest.fn();

    const served = await serveStatic(
      { url: '/%2e%2e/dist-escape/probe.js' },
      response,
      clientDistDir
    );
    if (served) {
      response.resume();
      await finished(response);
    }

    expect(served).toBe(false);
    expect(response.writeHead).not.toHaveBeenCalled();
  });
});

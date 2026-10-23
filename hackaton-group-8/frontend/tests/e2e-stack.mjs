import {createServer} from 'node:http';
import {spawn} from 'node:child_process';
import {existsSync} from 'node:fs';
import {resolve} from 'node:path';
import {fileURLToPath} from 'node:url';

const projectRoot = resolve(fileURLToPath(new URL('..', import.meta.url)), '..');
const jar = resolve(projectRoot, 'backend', 'target', 'quarkus-app', 'quarkus-run.jar');
if (!existsSync(jar)) throw new Error('Build backend/target/quarkus-app/quarkus-run.jar before running Playwright.');

let sequence = 0;
const verifications = new Map();
const wallets = new Map();
const supportCases = new Map();

function json(response, status, payload) {
  response.writeHead(status, {'content-type': 'application/json; charset=utf-8'});
  response.end(JSON.stringify(payload));
}

async function readJson(request) {
  const chunks = [];
  for await (const chunk of request) chunks.push(chunk);
  return JSON.parse(Buffer.concat(chunks).toString('utf8'));
}

const w1 = createServer(async (request, response) => {
  const url = new URL(request.url ?? '/', 'http://127.0.0.1');
  const path = url.pathname;
  try {
    if (request.method === 'POST' && path === '/kyc/verifications') {
      const body = await readJson(request);
      if (body.documentType !== 'TEST' || typeof body.document !== 'string' || !/^TEST-[A-Za-z0-9-]{1,80}$/.test(body.document)) {
        json(response, 400, {code: 'INVALID_DOCUMENT', message: 'Use a fictitious TEST document.'});
        return;
      }
      const scenario = body.scenario ?? 'APPROVED';
      if (!['APPROVED', 'MANUAL_REVIEW', 'REJECTED', 'UNAVAILABLE'].includes(scenario)) {
        json(response, 400, {code: 'INVALID_SCENARIO', message: 'Scenario is invalid.'});
        return;
      }
      if (scenario === 'UNAVAILABLE') {
        json(response, 503, {code: 'KYC_UNAVAILABLE', message: 'El servicio KYC no está disponible.'});
        return;
      }
      sequence++;
      const id = `kyc-${sequence}`;
      const walletId = `wallet-${sequence}`;
      const status = scenario === 'APPROVED' ? 'ACTIVE' : scenario === 'MANUAL_REVIEW' ? 'PENDING' : 'REJECTED';
      const verification = {id, wallet_id: walletId, scenario, status};
      verifications.set(id, verification);
      wallets.set(walletId, {id: walletId, status, balance: 0, reserved: 0, available: 0, currency: 'PEN'});
      if (scenario === 'MANUAL_REVIEW') {
        const caseId = `support-${sequence}`;
        supportCases.set(caseId, {id: caseId, resource: walletId, reason: 'KYC_MANUAL_REVIEW', status: 'OPEN'});
      }
      json(response, 201, verification);
      return;
    }
    if (request.method === 'GET' && path === '/support/cases') {
      json(response, 200, [...supportCases.values()]);
      return;
    }
    if (request.method === 'GET' && path.startsWith('/kyc/verifications/')) {
      const id = decodeURIComponent(path.slice('/kyc/verifications/'.length));
      const verification = verifications.get(id);
      json(response, verification ? 200 : 404, verification ?? {code: 'NOT_FOUND', message: 'Not found.'});
      return;
    }
    if (request.method === 'POST' && path.startsWith('/kyc/verifications/') && path.endsWith('/decision')) {
      const id = decodeURIComponent(path.slice('/kyc/verifications/'.length, -'/decision'.length));
      const verification = verifications.get(id);
      if (!verification) {
        json(response, 404, {code: 'NOT_FOUND', message: 'Not found.'});
        return;
      }
      const body = await readJson(request);
      if (!['ACTIVE', 'REJECTED'].includes(body.decision)) {
        json(response, 400, {code: 'INVALID_DECISION', message: 'Decision is invalid.'});
        return;
      }
      if (verification.status !== 'PENDING') {
        if (verification.status === body.decision) json(response, 200, verification);
        else json(response, 409, {code: 'DECISION_CONFLICT', message: 'DECISION_CONFLICT'});
        return;
      }
      const finalVerification = {...verification, status: body.decision};
      verifications.set(id, finalVerification);
      wallets.set(verification.wallet_id, {...wallets.get(verification.wallet_id), status: body.decision});
      for (const [caseId, support] of supportCases) {
        if (support.resource === verification.wallet_id) supportCases.set(caseId, {...support, status: 'RESOLVED'});
      }
      json(response, 200, finalVerification);
      return;
    }
    if (request.method === 'GET' && path.startsWith('/wallets/')) {
      const id = decodeURIComponent(path.slice('/wallets/'.length));
      const wallet = wallets.get(id);
      json(response, wallet ? 200 : 404, wallet ?? {code: 'NOT_FOUND', message: 'Not found.'});
      return;
    }
    json(response, 404, {code: 'NOT_FOUND', message: 'Not found.'});
  } catch (error) {
    console.error('W1 e2e fixture request failed:', error);
    if (!response.headersSent) json(response, 400, {code: 'INVALID_REQUEST', message: 'Invalid fixture request.'});
    else response.destroy(error);
  }
});

let app;
let closing = false;
function close() {
  if (closing) return Promise.resolve();
  closing = true;
  if (app && app.exitCode === null) app.kill();
  return new Promise(resolveClose => w1.close(resolveClose));
}

try {
  await new Promise((resolveListen, rejectListen) => {
    w1.once('error', rejectListen);
    w1.listen(0, '127.0.0.1', resolveListen);
  });
  const w1Address = w1.address();
  if (!w1Address || typeof w1Address === 'string') throw new Error('Could not resolve W1 fixture port.');

  app = spawn('java', ['-jar', jar], {
    cwd: projectRoot,
    env: {
      ...process.env,
      QUARKUS_HTTP_HOST: '127.0.0.1',
      QUARKUS_HTTP_PORT: '8090',
      WALLET_DB_URL: 'jdbc:h2:mem:e2e;DB_CLOSE_DELAY=-1',
      WALLET_LAB_ENABLED: 'true',
      W1_BASE_URL: `http://127.0.0.1:${w1Address.port}`,
    },
    stdio: 'inherit',
  });

  const deadline = Date.now() + 30000;
  while (Date.now() < deadline) {
    if (app.exitCode !== null) throw new Error(`Quarkus exited before readiness with code ${app.exitCode}.`);
    try {
      const response = await fetch('http://127.0.0.1:8090/api/health');
      if (response.ok) break;
    } catch {
      await new Promise(resolveDelay => setTimeout(resolveDelay, 200));
    }
  }
  const health = await fetch('http://127.0.0.1:8090/api/health').catch(() => null);
  if (!health?.ok) throw new Error('Quarkus did not become ready on port 8090.');
  process.stdin.resume();
} catch (error) {
  console.error(error);
  await close();
  process.exitCode = 1;
}

for (const signal of ['SIGINT', 'SIGTERM']) {
  process.on(signal, async () => {
    await close();
    process.exit(0);
  });
}

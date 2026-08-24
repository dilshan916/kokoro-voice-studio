const ngrok = require('@ngrok/ngrok');
const http = require('http');

const AUTHTOKEN = '3Cxa4FtuSzZjOdCZaIfAnuZ8dyz_4r9uV9RhHkchJyY1abHbK';
const DOMAIN = 'dry-eldercare-bok.ngrok-free.dev';
const PORT = 8000;

function checkLocalServer() {
  return new Promise((resolve) => {
    const req = http.get(`http://127.0.0.1:${PORT}/health`, (res) => {
      resolve(res.statusCode === 200);
    });
    req.on('error', () => resolve(false));
    req.setTimeout(2000, () => {
      req.destroy();
      resolve(false);
    });
  });
}

async function start() {
  console.log('\n============================================================');
  console.log('  Kokoro Voice Studio Pro - Permanent Ngrok Cloud Server');
  console.log(`  Fixed Domain: https://${DOMAIN}`);
  console.log('============================================================\n');

  const isServerRunning = await checkLocalServer();
  if (isServerRunning) {
    console.log(`[*] Kokoro FastAPI server is ACTIVE on port ${PORT}.`);
  } else {
    console.log(`[!] Note: Kokoro FastAPI server is starting on port ${PORT}...`);
  }

  console.log(`[*] Connecting Ngrok tunnel to port ${PORT}...`);

  try {
    const listener = await ngrok.forward({
      addr: PORT,
      authtoken: AUTHTOKEN,
      domain: DOMAIN,
    });

    console.log('\n' + '🟢 '.repeat(20));
    console.log(`  PERMANENT URL IS LIVE & SECURE:`);
    console.log(`  --> ${listener.url()}`);
    console.log('🟢 '.repeat(20) + '\n');
    console.log('Enter this URL into your mobile app Settings -> LAN Server URL:');
    console.log(`  ${listener.url()}`);
    console.log('\nPress Ctrl+C to stop the tunnel.\n');

    setInterval(() => {}, 1000 * 60 * 60);
  } catch (err) {
    if (err.message && err.message.includes('ERR_NGROK_334')) {
      console.log('\n' + '🟢 '.repeat(20));
      console.log(`  Your server is ALREADY ONLINE and active at:`);
      console.log(`  --> https://${DOMAIN}`);
      console.log('🟢 '.repeat(20) + '\n');
      console.log('You can connect right now from your mobile app!\n');
    } else {
      console.error('[!] Ngrok error:', err.message || err);
    }
  }
}

start();

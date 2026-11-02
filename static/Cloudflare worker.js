export default {
  async fetch(request, env) {
    const url = new URL(request.url);

    // Send everything to your real Cloud Run service.
    url.hostname = 'fitbot-402357265699.asia-south1.run.app';
    url.protocol = 'https:';

    // Cloud Run only sees Cloudflare's address, so pass the real visitor IP along.
    // That lets the app rate-limit each visitor separately instead of everyone as one person.
    const headers = new Headers(request.headers);
    headers.delete('X-Mentro-Client-IP');   // never trust copies sent by visitors
    headers.delete('X-Mentro-Proxy-Key');
    const visitorIp = request.headers.get('CF-Connecting-IP');
    if (visitorIp) headers.set('X-Mentro-Client-IP', visitorIp);
    // Optional hardening: set a secret named PROXY_KEY on this Worker (and PROXY_SHARED_SECRET on
    // Cloud Run, same value) so the app only trusts the IP header when it really came from here.
    if (env && env.PROXY_KEY) headers.set('X-Mentro-Proxy-Key', env.PROXY_KEY);

    return fetch(new Request(url.toString(), {
      method: request.method,
      headers: headers,
      body: request.body,
      // Hand Flask's redirects (login, logout, referral links) straight back to the browser.
      redirect: 'manual',
    }));
  }
};
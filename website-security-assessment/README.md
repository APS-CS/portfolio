# Project: "Security Assessment and Hardening of a Production Website"

A security assessment of [portalcs.se](https://portalcs.se), the public website of
Portal Cybersecurity, carried out before the site went live and repeated against
production afterwards. The site is static: no login, no forms, no database, no
cookies. That makes it a small target, and a good test of a different question:
**do the protections that are configured actually stop anything?**

Every finding below was demonstrated with a proof of concept, fixed, and then
re-tested with the same proof of concept against the fixed version. Each fix also
got an automated test that would have caught the fault.

> **Note on the details below.** The site's repository is private. The JavaScript
> excerpts are from code that has since been replaced, and the current scripts are
> downloaded by every visitor's browser anyway. Server configuration is described
> in words and not quoted. Hosting internals, the test suite itself, raw
> scan output and internal governance documents are not included. See
> [What is deliberately not published](#what-is-deliberately-not-published).

---

## Executive summary

**What was done.** The whole site was reviewed in five steps: code review, static
file checks, functional testing in a real browser, attack attempts in the same
browser, and a low-volume read-only scan of production.

**What was found.** This report covers five security findings: two of medium
severity and three of low. None could be used on its own to attack a visitor. The two medium findings were
protections that looked correct on paper but did not do their job:

- A browser protection against injected content (Trusted Types) was switched on,
  but the site's own code handed out a way around it.
- The server configuration did not itself enforce an encrypted connection. Visitors
  were still protected, but only by a default setting at the hosting provider.

**Where it stands.** All five are fixed and verified.

| | |
| :--- | :--- |
| Findings in this report | 5 (0 high, 2 medium, 3 low) |
| Fixed and re-tested | 5 |
| Found before go-live | 4 |
| Found in production | 1, fixed and verified the same evening |
| Visitors served the reviewed, pre-fix code | None. It was never deployed. |
| Attack attempts that the site stopped | 20 of 20 after the fixes |

**The main lesson.** A security control counts once an attack attempt has failed
against it, and not before. The site already had a strict security policy, and most
of it held. The faults were in the two places nobody had tried to break.

---

## Scope and rules of engagement

The site belongs to my own company, so authorisation was not in doubt. The test
still followed the same rules the site asks of outside researchers in its
vulnerability disclosure policy, because the site runs on a shared hosting platform
that I do not own.

| In scope | Out of scope |
| :--- | :--- |
| All HTML, CSS and JavaScript on the site | The hosting provider's platform |
| The server configuration file (`.htaccess`) | DNS and email |
| Response headers and TLS as seen by a visitor | Load testing and automated vulnerability scanners |
| The git history (leaked secrets) | Social engineering and physical security |

Attack attempts ran against a local copy of the site, never against production.
Production was only read: about sixty single requests, one at a time with a pause
between them.

---

## Attack surface

Before testing, the question was what there is to attack on a site with no backend.

| Surface | What can go wrong | Why it was tested |
| :--- | :--- | :--- |
| JavaScript that writes to the page | Injected content or script (DOM XSS) | The only dynamic part of the site. A fault here lends the company's name to an attacker. |
| Content Security Policy and Trusted Types | The protection exists on paper but stops nothing | An untested control is an assumption |
| URL validation | A link leads off-site or runs code | The function is a security boundary and must hold for any input |
| Server configuration | Unencrypted traffic, exposed files, open redirect | All server behaviour the site owner controls is in this one file |
| Response headers in production | The configuration never reaches the visitor | A hosting provider can ignore or overwrite settings |
| Git history | Passwords or keys in old commits | The repository is hosted with a third party, and a secret in history stays there after it is removed from the files |

The selection follows the parts of the
[OWASP Web Security Testing Guide](https://owasp.org/www-project-web-security-testing-guide/)
(v4.2) that apply to a static site: Configuration and Deployment Management Testing
(4.2), Client-side Testing (4.11), and Testing for Weak Transport Layer Security
(4.9.1). The categories for identity, authentication, authorisation and session
management have nothing to test here.

---

## Method

| Step | What | How | Volume |
| :---: | :--- | :--- | :--- |
| 1 | Code review | Follow each value from where it enters to where it is written to the page or a header | 13 pages, 3 script files, CSS, server config, 92 commits |
| 2 | Static checks | Python `unittest` reading the files without running them | 41 tests |
| 3 | Functional test | Headless Chrome driven over the DevTools protocol | 138 checks |
| 4 | Hardening test | Attack attempts executed inside the page | 20 attack attempts, 32 URL cases, hostile data, framing |
| 5 | Production scan | `curl` and `openssl`, read-only | About 60 requests |

Tools: Chrome (headless), Node.js without any packages, Python, git, curl and
OpenSSL. No vulnerability scanner, intercepting proxy or exploitation framework was
used. The site is small enough that reading all of it was the better method.

### The test environment

Three decisions in the test setup matter for whether the results can be trusted.

1. **The local server sends the real security headers.** It reads them out of the
   site's own server configuration, so the browser enforces the same policy as in
   production.
2. **The policy applies to the test code too.** DevTools can run code that bypasses
   the page's Content Security Policy. That option was turned off. Otherwise the
   test would have gone around the very protection it was meant to test.
3. **Before and after are tested the same way.** A script checks out both versions
   from git into temporary folders, serves each with its own headers, and runs
   identical proof-of-concept code in both. The output is printed side by side.

"Another domain" in the tests is `localhost` on the same port. The browser treats
`127.0.0.1` and `localhost` as different origins, so cross-origin rules are tested
without any traffic leaving the machine.

### The role of AI tooling

The code review, the test code and the fixes were produced with AI models
(Anthropic's Claude, through the coding agent Claude Code) working on my
instruction. I set the scope, approved each step that changed anything outside the
working folder, and approved the changes.

The division of labour is the important part:

- The model read the code and proposed hypotheses, for example "this policy accepts
  anything, so arbitrary HTML should be writable to the page".
- The model wrote test code for each hypothesis. The tests are ordinary scripts that
  can be read line by line.
- **The results come from the test runs, not from the model.** A language model can
  answer the same question differently twice. A script cannot. Everything under
  "Observed" below is output from a script or a command, and can be reproduced
  without any AI.
- A claim that could not be shown with a run is reported as "not exploitable" or
  "not verified", never as a finding.

The model had access to the site's source code, its git history and the responses
from the site itself. No customer material and no personal data were involved.

### How a finding is rated

| Question | Effect on severity |
| :--- | :--- |
| Can it be demonstrated? | Without a proof of concept it is an observation, not a finding |
| What does the attacker need first? | A fault that requires another fault weighs less |
| What can the attacker achieve? | The site has no accounts and holds no visitor data, which limits impact |
| How many visitors are affected? | All, or only some |

Severity is a judgement on the scale Info, Low, Medium, High. No CVSS score was
calculated. For a site this size the score adds little, and the reasoning is written
out under "Impact" for each finding.

---

## Findings overview

| ID | Severity | Finding | Found in | Status |
| :--- | :---: | :--- | :--- | :--- |
| [SEC-01](#sec-01--trusted-types-policy-accepted-everything-and-was-globally-reachable) | Medium | Trusted Types policy accepted everything and was globally reachable | Code review, confirmed by attack test | Fixed |
| [SEC-02](#sec-02--server-configuration-did-not-enforce-https) | Medium | Server configuration did not enforce HTTPS | Code review | Fixed |
| [SEC-03](#sec-03--url-validation-bypassed-with-a-tab-or-line-break) | Low | URL validation bypassed with a tab or line break | Attack test (URL case list) | Fixed |
| [SEC-04](#sec-04--article-list-built-as-html-strings) | Low | Article list built as HTML strings | Code review | Fixed |
| [SEC-05](#sec-05--web-manifest-served-without-a-content-type) | Low | Web manifest served without a Content-Type | Production scan | Fixed |

In the output below, BEFORE is the reviewed version and AFTER is the
fixed version. Labels are translated from Swedish. Browser error
messages are verbatim from Chrome 157.

---

## Findings in detail

### SEC-01 — Trusted Types policy accepted everything and was globally reachable

**Severity:** Medium · **Status:** Fixed

**Background.** The site's Content Security Policy requires Trusted Types. In
browsers that support it, the page refuses any HTML written to the DOM unless it has
passed through a named policy. The idea is that one small, reviewable function
decides what HTML is acceptable.

**The fault.** The policy function returned its input unchanged, and it was placed
on `window`. Any code running in the page could call it and get arbitrary HTML
approved.

```js
// Before
const policy = window.trustedTypes
  ? trustedTypes.createPolicy('portal-html', { createHTML: (s) => s })
  : null;
const tt = (s) => (policy ? policy.createHTML(s) : s);
window.PortalTT = tt;
```

**What was tested.** Five steps, run one at a time on the start page. Step 1 shows
that the protection is on, so that step 3 really is a bypass. Steps 4 and 5 try the
other routes to a policy, to show that the global function was the only gap.

```js
// 1. Write HTML without a policy
document.querySelector('.hero .lead').innerHTML =
  '<a href="https://evil.example/">x</a>';

// 2. Is the policy reachable as a global?
typeof PortalTT;

// 3. Attacker HTML through the global policy
document.querySelector('.hero .lead').innerHTML = PortalTT(
  '<a id="poc" href="https://evil.example/login">Your session has expired. Log in again</a>');

// 4. Create the same policy a second time
trustedTypes.createPolicy('portal-html', { createHTML: (s) => s });

// 5. Create a new policy
trustedTypes.createPolicy('attacker', { createHTML: (s) => s });
```

**Observed.**

```
1. HTML without a policy
  BEFORE  REJECTED: TypeError: Failed to set the 'innerHTML' property on 'Element': This document requires 'TrustedHTML' assignment.
  AFTER   REJECTED: (same)

2. Is the policy reachable as a global?
  BEFORE  function
  AFTER   undefined

3. Attacker HTML through the global policy
  BEFORE  ACCEPTED: <a id="poc" href="https://evil.example/login">Your session has expired. Log in again</a>
  AFTER   REJECTED: ReferenceError: PortalTT is not defined

4. Create the same policy a second time
  BEFORE  REJECTED: TypeError: ... Policy with name "portal-html" already exists.
  AFTER   REJECTED: (same)

5. Create a new policy
  BEFORE  REJECTED: TypeError: ... Policy "attacker" disallowed.
  AFTER   REJECTED: (same)
```

Steps 1, 4 and 5 are rejected in both versions, so the Content Security Policy was
written correctly from the start. The fault was entirely in steps 2 and 3. The
attacker's link was accepted and shown on the page in the site's own typography.

**Impact.** Not exploitable alone. An attacker first needs to run code in the page
or control a string that reaches the function. That is exactly the situation Trusted
Types exists for. With a pass-through policy, a future injection fault could be used
to place false content under the company's name, such as a login link. Script
execution was still blocked by `script-src 'self'`.

**Fix.** The policy now approves only the site's three fixed templates, by exact
comparison, and throws on everything else. It is no longer exported.

**Regression control.** The 20 attack attempts in the browser test include "policy
is not globally reachable", "policy cannot be created twice" and "no other policy
can be created". A static test checks that the policy is created once and never
assigned to `window`.

---

### SEC-02 — Server configuration did not enforce HTTPS

**Severity:** Medium · **Status:** Fixed. In production the redirect is performed by
the hosting provider's proxy, so the site's own rule is a fallback that has not been
exercised live.

**The fault.** The only redirect rule compared the host name. A request to the
correct host name over plain HTTP passed through unencrypted. HSTS only protects
visitors who have already been to the site over HTTPS.

**What was tested.** Three things, since no Apache was available locally.

1. *The file.* Is there any rule that tests the protocol?

   ```
   BEFORE  (no match)
   AFTER   two conditions: the connection itself, and whether a proxy in front
           has already handled TLS
   ```

2. *The logic of the rules.* A simplified rule interpreter in Python evaluates the
   rewrite rules against given requests.

   | Request | Expected |
   | :--- | :--- |
   | HTTP to the site | 301 to the same path over HTTPS |
   | HTTP to the `www` name | 301 to the canonical name over HTTPS |
   | HTTP from a proxy that has already handled TLS | Passes, no redirect loop |
   | Certificate renewal path over HTTP | Passes |
   | All redirect rules | The target is never built from the host name in the request |

3. *Production.* What does the live site answer over HTTP?

   ```
   $ curl -sS -o /dev/null -D - http://portalcs.se/
   HTTP/1.1 301 Moved Permanently
   Location: https://portalcs.se/
   ```

**Interpretation.** The HTTP response carried none of the headers that the site's
configuration sets on every response. The redirect is therefore done by the hosting
provider's reverse proxy, before the request reaches the web server. Visitors are
protected. But that protection rested on a provider setting the site owner does not
control, and the site's own rule has never run in production.

**Impact.** Before the fix, and without the provider's redirect, a first visit
through an `http://` link could be read or altered by someone on the network path,
for example on open Wi-Fi.

**Fix.** A rule that redirects with 301 when the connection is not HTTPS and the
proxy has not flagged it as HTTPS. The second condition prevents a redirect loop
when TLS ends at a proxy, which is how this hosting platform is built.

**Regression control.** Eight rule tests, and a header check against production
after every deployment.

---

### SEC-03 — URL validation bypassed with a tab or line break

**Severity:** Low · **Status:** Fixed

**The fault.** A helper function is meant to allow only relative links, `https:` and
`mailto:`, and it explicitly rejects protocol-relative addresses starting with `//`.
The check was made on the raw string. Browsers strip tabs and line breaks from a URL
before parsing it, so `/<tab>/evil.example` passed the check and then became
`//evil.example`.

```js
// Before
const safeUrl = (raw) => {
  const u = String(raw).trim();
  if (u.startsWith('//') || u.includes('\\')) return '#';
  if (/^(https:|mailto:)/i.test(u)) return u;
  if (u.includes(':')) return '#';
  return u;
};
```

**How it was found.** Code review found nothing wrong with this function. The fault
was found by a list of 32 values built from how browsers parse addresses, not from
how the code looks: letter case, leading whitespace, tabs and line breaks, backslash
treated as slash, control characters, and values that are not strings.

The test does not ask the function for its opinion. It sets the result as `href` on
a link and reads where *the browser* says the link leads.

```js
const out = safeUrl('/\t/evil.example');
const a = document.createElement('a');
a.setAttribute('href', out);
JSON.stringify({ returned: out, host: a.host, sameOrigin: a.origin === location.origin });
```

**Observed.** Three attack values and three control values. The controls show that
the fix did not break what is supposed to work.

```
1. Tab: '/\t/evil.example'
  BEFORE  {"returned":"/\t/evil.example","host":"evil.example","sameOrigin":false}
  AFTER   {"returned":"#","host":"127.0.0.1:56562","sameOrigin":true}

2. Line break: '/\n/evil.example'
  BEFORE  {"returned":"/\n/evil.example","host":"evil.example","sameOrigin":false}
  AFTER   {"returned":"#","host":"127.0.0.1:56562","sameOrigin":true}

3. https without slashes: 'https:evil.example'
  BEFORE  {"returned":"https:evil.example","host":"evil.example","sameOrigin":false}
  AFTER   {"returned":"#","host":"127.0.0.1:56562","sameOrigin":true}

4. Control, plain protocol-relative: '//evil.example'
  BEFORE  {"returned":"#", ... "sameOrigin":true}
  AFTER   {"returned":"#", ... "sameOrigin":true}

5. Control, allowed external link: 'https://www.ncsc.se/'
  BEFORE  {"returned":"https://www.ncsc.se/","host":"www.ncsc.se","sameOrigin":false}
  AFTER   {"returned":"https://www.ncsc.se/","host":"www.ncsc.se","sameOrigin":false}

6. Control, relative link: 'artiklar/x.html'
  BEFORE  {"returned":"artiklar/x.html", ... "sameOrigin":true}
  AFTER   {"returned":"artiklar/x.html", ... "sameOrigin":true}
```

Case 4 shows that the plain form was already rejected. That was the very check the
tab got past.

**Impact.** None today. The value comes from a data file the site owner writes, and
external `https://` links are allowed anyway. The fault matters the day the data
comes from a source the owner does not control, or the function is reused to keep
links on the site.

**Fix.** Non-strings, empty values and values containing whitespace or control
characters return `#`. `https` must have the form `https://` followed by a host name.

**Regression control.** All 32 cases run in the browser test. The test fails if a
single value leads to another origin without starting with `https://`.

---

### SEC-04 — Article list built as HTML strings

**Severity:** Low (hardening) · **Status:** Fixed

**The pattern.** Article rows and filter buttons were assembled as strings and
written with `innerHTML`. Every field went through an escaping function. The
protection therefore depended on no future change forgetting one escape call, and
this pattern was the reason the global policy in SEC-01 existed at all.

**What was tested.** Two questions. Can the pattern be exploited today? Is the
pattern gone after the fix?

For the first, an article row was built with hostile content in every field, added
to the page and clicked.

```js
window.__x = 0;
const bad = '<img src=x onerror="window.__x=1"><script>window.__x=1<\/script>"\'><svg onload=window.__x=1>';
const data = { titel: bad, utdrag: bad, kategori: bad, datum: '2026-01-01',
               lasetid: bad, url: 'javascript:window.__x=1' };
// build the row from `data`, append it to the article list, click it, then:
({ elementsCreated: row.querySelectorAll('img,script,svg').length,
   href: row.getAttribute('href'),
   titleIsText: row.querySelector('h3').textContent === bad,
   codeRan: window.__x === 1 });
```

**Observed.**

```
Hostile article data in every field
  BEFORE  {"elementsCreated":0,"href":"#","titleIsText":true,"codeRan":false}
  AFTER   {"elementsCreated":0,"href":"#","titleIsText":true,"codeRan":false}

innerHTML in the rendering script
  BEFORE  3 occurrences
  AFTER   (no match)
```

**Interpretation.** Same result before and after. The escaping held and nothing
could be exploited. This finding is included because "the test found nothing" is a
result, and because the fix addresses the pattern, not a demonstrated fault. The
difference is *why* it holds: before, because five escape calls were all in place;
after, because no HTML is parsed at all.

**Fix.** Rows are built with `createElement` and `textContent`. The rendering script
writes no HTML to the DOM.

**Regression control.** A static test blocks `innerHTML`, `insertAdjacentHTML`,
`document.write`, `eval` and similar sinks in every script file on future changes.

---

### SEC-05 — Web manifest served without a Content-Type

**Severity:** Low · **Status:** Fixed, verified in production

**The fault.** The hosting provider's web server did not recognise the
`.webmanifest` file extension and sent the file with no `Content-Type`. The site
also sends `X-Content-Type-Options: nosniff`, which tells the browser not to guess.

**How it was found.** Only in production. The local test server had its own list of
file types, and that list included the extension. The production scan fetched every
public file and read the status code and content type of each.

**Observed.**

```
$ curl -sS -o /dev/null -D - https://portalcs.se/site.webmanifest

Before the fix:
HTTP/1.1 200 OK
X-Content-Type-Options: nosniff

After the fix:
HTTP/1.1 200 OK
Content-Type: application/manifest+json
X-Content-Type-Options: nosniff
```

**Impact.** Small. The manifest holds only a name, colours and icons. A browser that
follows `nosniff` strictly may decline to read it. No route to an attack was found.

**Fix.** One line declaring the type in the server configuration, and a static test
for file types the server does not know by default.

**Lesson.** The first check after uploading the fix still showed the fault. The new
configuration file had not replaced the old one on the server. A fix is not done
until it has been checked where it is supposed to work.

---

## Verified without remark

A report that lists only faults says nothing about what held. These were tested and
passed.

| Control | Result |
| :--- | :--- |
| 20 attack attempts in the page | All stopped: writing HTML three ways, `eval`, `new Function`, string timers, inline script, inline handlers, inline style, script and image from another origin, `fetch`, `sendBeacon`, `<base>` hijack, iframe, form submission |
| Framing | A page on another origin cannot display the site in a frame |
| Security headers in production | Present on 200, 301 and 404 responses alike |
| Files that must not be served | Repository metadata, editor settings, documentation, tests, templates and backup files all return 404 |
| Directory listing | Off |
| TLS | 1.3 and 1.2 accepted, 1.1 refused |
| HTTP methods | `TRACE` refused |
| `security.txt` | Valid per RFC 9116 |
| Server banner | No version disclosed |
| Git history | 92 commits searched for passwords, keys and tokens. Eight matches, all article text or header names. No secrets. |
| Third-party resources | None. Everything loads from the site's own domain. |
| Inline code | None in any HTML file |

For the exfiltration attempts (`sendBeacon`, form submission) the test does not
trust the browser's return value. It checks the local server's log to confirm the
request never arrived.

---

## From findings to rules

Each finding became a rule for how the site is built, and each rule is enforced by
a test, not by memory.

| Rule | Comes from | Enforced by |
| :--- | :--- | :--- |
| Never write HTML to the DOM from data. Build elements. | SEC-04 | Static test for forbidden sinks |
| A Trusted Types policy rejects what it does not recognise and is never exported. | SEC-01 | Static test and browser attack tests |
| Validate a URL after rejecting whitespace and control characters, never on the raw string. | SEC-03 | 32 URL cases in the browser |
| All traffic over HTTPS. Redirect targets are never built from the request's host name. | SEC-02 | Rule tests |
| Every security fix gets a test that would have caught the fault. | All | Review |
| Every deployment is checked in production: headers, content types, hidden files. | SEC-02, SEC-05 | Scripted read-only check |
| A control does not count until an attack attempt has failed against it. | SEC-01, SEC-04 | The hardening tests |

---

## Limitations, stated honestly

- **One browser.** Everything ran in Chrome. Trusted Types behaves differently, or
  is missing, in other browsers. There the site relies on the rest of the Content
  Security Policy and on not writing HTML from data.
- **The rule interpreter is simplified.** It tests the expressions in the server
  configuration, not the web server itself. Production was checked with about sixty
  requests, which is a sample.
- **The HTTPS rule is untested live.** The provider redirects first, so the site's
  own rule has never been the one to act.
- **A snapshot.** The results hold for one commit and one evening. A change in the
  code or at the provider can change them, which is why the tests run before every
  deployment.
- **Absence of findings is not proof of absence.** A test shows that one specific
  attempt fails. It does not show that the site is secure.

---

## What is deliberately not published

**Published:** the scope, the method, the reasoning behind each test, the findings
with proof of concept and observed output, the fixes, and the limitations. The JavaScript
excerpts show code that has been replaced.

**Not published:** the repository and its commit history, the server configuration
file, details of the hosting provider's infrastructure seen in response
headers, raw scan logs, the full list of probed paths, the test suite and
proof-of-concept runner, the internal findings register, and the internal policies
and guidelines that the findings feed into.

---

## Scope and disclaimer

The site tested is my own company's. No client systems, client data or third-party
systems were tested. Attack attempts ran only against a local copy on my own
machine. Requests to production were read-only, low in volume, and within the limits
the site's own disclosure policy sets for anyone.

---

## Key Learning Outcomes

* **Testing controls, not listing them.** A strict policy and a pass-through
  function can sit in the same codebase. Only an attack attempt tells them apart.
* **Building test cases from the platform's behaviour.** The URL bypass was found by
  inputs chosen from how browsers parse addresses, after code review had passed the
  function.
* **Before-and-after evidence.** Running identical proof-of-concept code against
  both versions separates "fixed" from "changed".
* **Knowing where a control actually lives.** The HTTPS redirect and one response
  header turned out to be the provider's, not the site's. That changes what the
  owner can promise.
* **Reporting negative results and open items.** What held, what was not tested and
  what is still open are part of the result.
* **Using AI tooling under control.** Hypotheses from a model, evidence from
  reproducible scripts, decisions and approval from a person.

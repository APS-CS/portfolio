# Project: "Hardened Self-Hosted Media Server (Jellyfin on Docker)"

A home lab project running [Jellyfin](https://jellyfin.org) — an open source media
server — in Docker on a small refurbished office PC. The media streaming is the
excuse; the real subject is defending a service that parses untrusted input, needs
hardware access, has real users who notice downtime, and fails in ambiguous ways.

> **Note on addresses:** all IP addresses in this document are fictional examples
> chosen for readability. They do not correspond to any real network. The LAN is
> written as `10.20.30.0/24` throughout.

---

## Threat model

Hardening without a threat model is just cargo culting. Before any configuration, the
question was: *what can realistically go wrong here, and what would it cost me?*

| # | Threat | Realistic? | Impact | Primary control |
| :--- | :--- | :--- | :--- | :--- |
| T1 | Malicious media file exploits a parser bug (ffmpeg/libav) and executes code as the service | Yes — ffmpeg is a large C codebase with a long CVE history, and it parses every file in the library | Code execution inside the container | Least-privilege container: non-root, no capabilities, no privilege escalation, read-only media |
| T2 | Compromised service escapes the container to the host | Low but non-zero | Full host compromise | Capability dropping, no privileged mode, no Docker socket mount, minimal device exposure, patched kernel |
| T3 | Service exposed to the internet and brute-forced or hit by an unauthenticated RCE | Very high **if** the port is forwarded | Full compromise, plus lateral movement into the home network | No port forwarding at all. Access via VPN only |
| T4 | Another compromised device on the LAN attacks the server laterally | Plausible — IoT devices are the usual weak link | Compromise from a trusted-looking source | Host firewall with per-subnet rules, planned VLAN segmentation |
| T5 | Ransomware or accidental deletion destroys the media library | Plausible | Irreversible data loss | Read-only mount; backups |
| T6 | Physical theft of the machine | Plausible — it's small and sits in a home | Disclosure of all data at rest | Full-disk encryption (LUKS) |
| T7 | Silent supply-chain change via an auto-updating container image | Happens routinely | Unreviewed code running as your service; non-reproducible bugs | Pinned image tags, deliberate updates |

Everything below maps back to a row in this table. If a control doesn't, it doesn't
belong here.

---

## Defence in depth

The design assumes each layer will eventually fail, so no single control is load
bearing.

```
                Internet
                    |
                [ router ]  <-- no port forwarding to the server (T3)
                    |
        LAN 10.20.30.0/24
                    |
        [ UFW: default deny in ]  <-- host firewall, per-source rules (T3, T4)
                    |
        [ Ubuntu LTS, LUKS, auditd, unattended-upgrades ]  <-- host (T2, T6)
                    |
        [ Docker: non-root, cap_drop ALL, no-new-privileges ]  <-- container (T1, T2)
                    |
        [ Jellyfin: media mounted :ro, render node only ]  <-- service (T1, T5)
```

---

## Network exposure — the single most important decision

The most common self-hosting mistake is forwarding a port. Jellyfin's login page
facing the internet means every unauthenticated vulnerability in the web stack, and
every credential-stuffing bot on the planet, is now your problem. Search engines for
internet-connected devices index these within hours.

**Decision: nothing is forwarded.** The server is reachable only from the LAN
(`10.20.30.0/24`). Remote access, when needed, goes through a VPN — you authenticate
to the tunnel first, and only then can you reach the service. Jellyfin never sees an
unauthenticated packet from the internet.

Host firewall policy:

```bash
sudo ufw default deny incoming
sudo ufw default allow outgoing

# Media service: LAN only
sudo ufw allow from 10.20.30.0/24 to any port 8096 proto tcp

# Administration: LAN only, and only on the internal interface
sudo ufw allow in on eth0 from 10.20.30.0/24 to any port 22 proto tcp

sudo ufw enable
sudo ufw status verbose
```

Two things worth internalising here:

1. **A firewall rule without a source is not a restriction.** `ufw allow 8096` opens
   the port to everything that can route to the host. `ufw allow from 10.20.30.0/24`
   is a control; the other is a formality.
2. **A missing subnet mask silently narrows a rule to a single address.**
   `192.168.0.0` and `192.168.0.0/24` are not the same rule, and the first one will
   fail in a way that looks like a broken network rather than a broken rule.

A related trap: a machine with more than one network interface will listen on *all*
of them by default. If a second NIC sits on a different segment, SSH is reachable
from that segment too — invisible in `ufw status`, which shows the rule but not which
interfaces are actually live. Binding administrative services to a specific interface
(`ufw allow in on eth0 ...`) makes the intent explicit and closes the gap.

---

## Container hardening

The compose file is the security boundary, so every line is a decision.

```yaml
services:
  jellyfin:
    image: jellyfin/jellyfin:10.11.8      # pinned — T7
    user: "1000:1000"                     # non-root — T1
    cap_drop:
      - ALL                               # no capabilities — T1, T2
    security_opt:
      - no-new-privileges:true            # blocks setuid escalation — T2
    group_add:
      - "993"                             # render group only, GID from `getent group render`
    devices:
      - /dev/dri/renderD128:/dev/dri/renderD128   # render node only, not all of /dev/dri
    volumes:
      - /opt/jellyfin/config:/config              # writable state
      - /srv/media:/media:ro                      # library is read-only — T1, T5
    ports:
      - "10.20.30.10:8096:8096"           # bound to the LAN interface, not 0.0.0.0
    restart: unless-stopped
```

**`cap_drop: ALL`** removes every Linux capability. Jellyfin needs none of them, and
a compromised process without capabilities can't manipulate the network stack, load
modules, or change file ownership.

**`no-new-privileges: true`** prevents a process from gaining privileges through
setuid binaries. Without it, a compromised service that finds a setuid binary inside
the image has an escalation path.

**Non-root user.** Container root is host root in most default configurations. If a
process escapes, whatever it was inside is what it is outside.

**Read-only media (`:ro`).** Jellyfin only reads the library. Granting write access
means a compromised process could encrypt or delete everything — the ransomware
scenario. Making the mount read-only removes that capability entirely rather than
relying on the process behaving.

**Port binding.** `8096:8096` binds to every interface. `10.20.30.10:8096:8096` binds
to one. Docker also writes its own iptables rules that can bypass UFW, so relying on
the firewall alone is not enough — bind narrowly *and* filter.

**No Docker socket mount.** Mounting `/var/run/docker.sock` into a container is
equivalent to giving it root on the host. There is no configuration in which a media
server needs it.

**Pinned image tag.** `:latest` means the code running your service can change on any
restart, unreviewed. It also makes bugs non-reproducible, which is the worst property
a bug can have (see Case 2).

---

## GPU access: a worked example of least privilege

Hardware transcoding requires exposing the GPU, which is the one place this design
deliberately widens the attack surface. It's worth walking through, because it is a
textbook least-privilege decision with a real trade-off.

The GPU appears as device nodes in `/dev/dri`:

- **`renderD128`** — the *render node*. Purpose-built to be handed to unprivileged
  processes for compute and encode/decode work. It exposes no display control.
- **`card0`** — the *primary node*, which also covers display modesetting. More
  privileged, and entirely unnecessary for transcoding.

Most guides tell you to map the whole directory:

```yaml
    devices:
      - /dev/dri:/dev/dri        # includes card0 — more than is needed
```

Mapping only the render node gives identical functionality with less exposure:

```yaml
    devices:
      - /dev/dri/renderD128:/dev/dri/renderD128
```

The render node is owned by the `render` group with mode `660` — only root and group
members can open it. A container process is not a member of the host's groups, so it
fails to open the device even when the node is mapped in. The fix is a supplementary
group, not root:

```bash
getent group render          # find the host GID (e.g. 993)
```

```yaml
    group_add:
      - "993"
```

**What `group_add` grants, and what it doesn't.** It grants exactly one thing: the
right to open the render node. It is not a capability and does not weaken `cap_drop:
ALL` or `no-new-privileges`. It gives no root, no network access, no other devices,
and no write access to the media.

**The residual risk, stated honestly.** A compromised Jellyfin process — say, via a
malicious media file exploiting ffmpeg (T1) — can now reach the i915 GPU driver in
the kernel. Kernel drivers are a recurring source of local privilege escalation, so
this is a genuine, if narrow, widening of the container escape path (T2). It is
accepted because the alternative (software transcoding on a low-TDP CPU) makes the
service unusable, and it is mitigated by automatic kernel patching.

That is what a security decision looks like when it's written down: the gain, the
cost, and why the cost is acceptable *here*.

---

## Host hardening

- **Full-disk encryption (LUKS)** — T6. A stolen machine is a lost machine, not a
  data breach.
- **`unattended-upgrades`** for security patches. This carries more weight than usual
  because the GPU exposure above is mitigated primarily by a current kernel.
- **`auditd`** for system-level audit logging — who ran what, and when.
- **SSH key authentication only**, password authentication and direct root login
  disabled. Administrative access restricted to the LAN and to the internal
  interface.
- **No unnecessary services.** Every listening port is an attack surface; `ss -tlnp`
  should hold no surprises.

---

## Application-level security

Hardening the container doesn't help if the application is left open.

- **No anonymous access.** Jellyfin can be configured to allow unauthenticated local
  network access. It isn't here — every user authenticates.
- **Separate accounts per user**, so playback history and library permissions are
  per-person and revocable individually.
- **Administrative rights on exactly one account.** Day-to-day viewing uses a
  non-admin account, so a stolen session isn't a stolen server.
- **Strong, unique credentials** for the admin account.
- **No plugins from untrusted repositories.** Plugins run with the server's
  privileges; a third-party plugin repository is a supply-chain risk (T7) with the
  same blast radius as the server itself.

---

## Monitoring and evidence

A control you can't observe is a control you're guessing about.

- A monitoring script samples load average, CPU, RAM and swap every few seconds to a
  log file, with an explicit `sync` after each write so the data is on disk if the
  machine dies mid-write.
- Started with `nohup` and `disown` so it survives the SSH session that launched it —
  otherwise it dies exactly when it's needed most.
- A larger diagnostic script collects kernel logs, service logs, thermal data,
  container state and network configuration into one timestamped file.

Verification is part of the configuration, not an afterthought:

```bash
docker exec jellyfin id                    # confirms non-root and expected groups
docker exec jellyfin ls -l /dev/dri        # confirms only the render node is present
docker inspect jellyfin | grep -iE "privileged|CapAdd|SecurityOpt"
sudo ufw status verbose                    # confirms per-source rules, not blanket allows
ss -tlnp                                   # confirms what is actually listening, on which address
```

---

## Troubleshooting case studies

Three incidents, each with a security lesson attached.

### Case 1 — The "freeze" that was resource starvation

**Symptom:** the whole machine became unresponsive, SSH included, a few minutes into
video playback.

**Hypotheses ruled out:** out of memory (no OOM-killer entries in the kernel log);
GPU driver crash (no hang or reset messages).

**Actual cause:** the container could not open the GPU render node, so ffmpeg fell
back to software encoding and saturated every core on a low-power CPU. The kernel was
alive the whole time — it just had nothing left to schedule SSH with.

**Security lesson:** this is an availability failure, and availability is a security
property. It's also the shape a resource-exhaustion denial of service takes: a single
crafted file that forces expensive transcoding could reproduce it deliberately.
Separately — a setting enabled in a UI is not proof that it does anything. Verify at
the layer where the work happens, not the layer where you configured it.

### Case 2 — The "freeze" that was a browser cache

**Symptom:** playback froze again — but monitoring captured during the event showed
the server ~98% idle, load 0.03, RAM free, swap untouched.

**Actual cause:** a stale service worker in the browser, left from an earlier version
of the web client, throwing `ChunkLoadError`. Entirely client-side. The trigger was an
unpinned image tag: the container had silently updated while the browser served
cached assets from the previous version.

**Security lesson:** T7 made visible. An image that updates itself is code changing
under you without review, and it turns a reproducible bug into an intermittent one.
More broadly: two identical-looking symptoms had unrelated causes, and only telemetry
separated them. Without it, the obvious move was to keep "fixing" a healthy server.

### Case 3 — Evidence that deleted itself

Jellyfin runs a scheduled task at startup that clears the transcode directory,
including the ffmpeg logs from the session that just failed. Every freeze was followed
by a reboot, so the recovery destroyed the evidence.

**Security lesson:** log retention has to be designed before the incident, not after.
Anything you intend to read post-crash must be written where the recovery process
won't touch it, and read before anything else runs. In an incident response context
this is the whole argument for shipping logs off-host: local logs are under the
control of whatever, or whoever, caused the incident.

---

## Trade-offs, stated explicitly

| Decision | Gain | Cost |
| :--- | :--- | :--- |
| GPU render node mapped in | Hardware transcoding; a usable service | A compromised process reaches the kernel GPU driver. Narrow, understood, mitigated by patching |
| `group_add` for the render group | Device access without root | One supplementary group. No capabilities, no weakening of other controls |
| Read-only media mount | Library can't be encrypted or wiped by the service | Metadata and artwork must be written elsewhere |
| LAN only, no port forwarding | No internet-facing attack surface | Remote access requires a VPN; less convenient for guests |
| Pinned image version | Reproducible builds, reviewed updates | Security updates must be applied deliberately — an accepted maintenance burden |
| Non-admin daily accounts | Smaller blast radius from a stolen session | Slightly more account management |

---

## Open items

- Finish validating hardware acceleration end to end under real load.
- VLAN segmentation — isolate the server from IoT devices on the LAN.
- Ship logs off-host so post-incident evidence survives a reboot.
- Documented backup and restore routine for the configuration volume, tested by
  actually restoring it.
- Fail2ban or equivalent on SSH, even though it is LAN-restricted.

---

## Key Learning Outcomes

* **Threat modelling before configuration** — deriving controls from realistic
  scenarios instead of copying a hardening checklist.
* **Least privilege as a concrete practice** — device nodes, supplementary groups,
  capabilities, and the difference between "it works" and "it has only what it needs".
* **Network exposure decisions** — why source-restricted firewall rules, interface
  binding and VPN-first remote access matter more than any single hardening flag.
* **Evidence-based troubleshooting** — forming a hypothesis, deciding in advance what
  would disprove it, and collecting data that survives the failure.
* **Documenting trade-offs** — being able to explain what a control costs, not just
  that it's enabled, is what makes a security decision defensible to someone else.

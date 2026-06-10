# Deploying LedgerIQ — free Oracle VM + Cloudflare Tunnel

This runs the whole app (FastAPI + React + PostgreSQL + nginx) on one free,
always-on server, published at `https://app.yourdomain.com` over HTTPS with **no
open inbound ports** — Cloudflare Tunnel connects outbound to Cloudflare, so
nothing on the VM is exposed to the internet directly.

You'll do three things: (1) get a free VM, (2) create a Cloudflare Tunnel,
(3) run `docker compose`. ~30 minutes end to end.

---

## 1. Create a free Oracle Cloud VM

1. Sign up at <https://cloud.oracle.com> (the **Always Free** tier needs a card
   for identity verification but is not charged for Always Free resources).
2. **Compute → Instances → Create instance**:
   - **Image:** Ubuntu 24.04 (or 22.04).
   - **Shape:** `VM.Standard.A1.Flex` (Ampere/ARM, Always Free). Give it
     **2 OCPU / 8 GB RAM** — plenty, and the on-VM Docker build needs the RAM.
     *(If A1 capacity is unavailable in your region, retry later or pick another
     availability domain.)*
   - **SSH keys:** upload your public key (`~/.ssh/id_ed25519.pub`).
3. Create it and note the **public IP**.

> You do **not** need to open any ports in the VCN security list — the tunnel is
> outbound-only. (That's the security win of this approach.)

---

## 2. Install Docker on the VM

```bash
ssh ubuntu@<VM_PUBLIC_IP>

# Docker Engine + Compose plugin
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
newgrp docker      # or log out/in so the group applies
docker --version && docker compose version
```

All images used (postgres, nginx, cloudflared, node, python) have ARM64 builds,
so they run fine on the A1 (ARM) shape.

---

## 3. Get the app onto the VM

Easiest is via GitHub (push your repo, then clone). Or copy directly:

```bash
# Option A — from GitHub
git clone https://github.com/<you>/LedgerIQ.git && cd LedgerIQ

# Option B — from your laptop (run on the laptop)
# rsync -av --exclude .deps --exclude node_modules --exclude '*.db' \
#   ~/Desktop/projects/LedgerIQ/ ubuntu@<VM_PUBLIC_IP>:~/LedgerIQ/
```

---

## 4. Configure secrets

```bash
cp .env.example .env
nano .env
```

Set, at minimum:

```ini
POSTGRES_PASSWORD=<a long random password>
JWT_SECRET=<run: openssl rand -base64 48>
PUBLIC_ORIGIN=https://app.yourdomain.com
# Optional: LLM_API_KEY=sk-ant-...   (enables the LLM-backed AI features)
# TUNNEL_TOKEN is filled in the next step.
```

---

## 5. Create the Cloudflare Tunnel

1. In the Cloudflare dashboard → **Zero Trust → Networks → Tunnels → Create a
   tunnel** → connector **Cloudflared** → name it `ledgeriq`.
2. On the install screen, **copy the tunnel token** (the long string after
   `--token`). Put it in `.env`:
   ```ini
   TUNNEL_TOKEN=<paste the token>
   ```
3. Add a **Public Hostname** for the tunnel:
   - **Subdomain:** `app`  **Domain:** `yourdomain.com`
   - **Service:** `HTTP`  →  `nginx:80`

   (Cloudflare auto-creates the `app` DNS record on your domain and handles
   HTTPS at its edge.)

---

## 6. Launch

```bash
docker compose -f docker-compose.yml -f docker-compose.tunnel.yml up -d --build
```

- The backend runs database migrations automatically on start.
- Give it a minute, then open **https://app.yourdomain.com** and register your
  account (first registration = your user).

Check status / logs:

```bash
docker compose -f docker-compose.yml -f docker-compose.tunnel.yml ps
docker compose -f docker-compose.yml -f docker-compose.tunnel.yml logs -f
```

---

## Everyday operations

```bash
# pull latest code, rebuild, restart
git pull
docker compose -f docker-compose.yml -f docker-compose.tunnel.yml up -d --build

# stop / start
docker compose -f docker-compose.yml -f docker-compose.tunnel.yml down
docker compose -f docker-compose.yml -f docker-compose.tunnel.yml up -d

# back up the database
docker compose exec postgres pg_dump -U "$POSTGRES_USER" "$POSTGRES_DB" > backup_$(date +%F).sql
```

Your data lives in the `pgdata` Docker volume and survives restarts/rebuilds.
`down -v` (note the `-v`) would delete it — don't use that unless you mean to.

---

## Notes

- **HTTPS** is handled entirely by Cloudflare; the origin stays plain HTTP on the
  internal Docker network, which is fine because the tunnel link is encrypted.
- **No CORS config needed** — the browser hits `app.yourdomain.com` and the API
  is same-origin (`/api/...`), proxied by nginx. `PUBLIC_ORIGIN` is set anyway as
  a safety net.
- **Scheduler** (subscription auto-posting, reminders, optional weekly LLM
  insights) runs inside the backend container — it's always on with the VM.
- To use a different subdomain, just change the Public Hostname in step 5 and
  `PUBLIC_ORIGIN` in `.env`.

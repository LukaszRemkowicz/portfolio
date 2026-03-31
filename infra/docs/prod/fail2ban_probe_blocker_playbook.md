What you still need to do on the server:

```bash
sudo apt-get update && sudo apt-get install -y fail2ban
sudo mkdir -p /var/log/portfolio/traefik
sudo chown -R <user>:<user> /var/log/portfolio/traefik
chmod +x /home/<user>/portfolio/infra/scripts/security/install_fail2ban_probe_blocker.sh
sudo /home/<user>/portfolio/infra/scripts/security/install_fail2ban_probe_blocker.sh
TAG=v2.2.0 doppler run -- docker compose -f docker-compose.traefik.yml up -d traefik
```

Then verify:

```bash
sudo fail2ban-client status portfolio-nginx-sensitive-probes
sudo fail2ban-client status portfolio-traefik-sensitive-probes
```

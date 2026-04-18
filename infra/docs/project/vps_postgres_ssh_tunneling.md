# VPS Postgres SSH Tunneling

## Purpose

This document explains how to connect to the VPS PostgreSQL database from a local machine through an SSH tunnel.

It is intended for local tools such as pgAdmin that need a local TCP endpoint while the database itself stays private inside the VPS Docker network.

## Tunnel Command

Use this command on your local machine:

```bash
ssh -N -L 25432:172.18.0.2:5432 portfolio
```

This creates a local SSH tunnel from your machine to the PostgreSQL container running on the VPS.

## What The Command Means

```text
ssh -N -L 25432:172.18.0.2:5432 portfolio
```

- `ssh`
  Starts an SSH connection.
- `-N`
  Do not run a remote shell or command. Keep the session open only for port forwarding.
- `-L`
  Create local port forwarding.
- `25432`
  Local port on your machine. This is the port pgAdmin should use.
- `172.18.0.2`
  Target IP used on the remote side of the tunnel.
  After SSH connects to `portfolio`, the VPS tries to open a connection to `172.18.0.2:5432`.
  That address is the PostgreSQL container IP inside the VPS Docker bridge network.
  It is not your local machine, not `localhost` on your machine, and not the public VPS IP.
  It works because the SSH process is already running on the VPS, and from there Docker container IPs on that network are reachable.
  To get this IP on the VPS, first find the DB container with `docker ps`, then inspect it, for example:
  `docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' portfolio-dev-db-1`
- `5432`
  PostgreSQL port inside the container.
- `portfolio`
  SSH alias for the VPS server from your local SSH config.

## Port Mapping Summary

- Local machine: `127.0.0.1:25432`
- VPS-side target: `172.18.0.2:5432`
- SSH hop: `portfolio`

So when pgAdmin connects to `127.0.0.1:25432`, traffic is forwarded through SSH to `172.18.0.2:5432` on the VPS.

## Important Note About The Docker IP

The IP `172.18.0.2` in the SSH command is the PostgreSQL container IP inside the VPS Docker network.

This means:

- it is not a localhost address on the VPS
- it is not the public VPS address
- it points directly to the running database container inside Docker networking

If Docker networking changes or the database container is recreated on a different bridge/network, this IP may change. If the tunnel suddenly stops working, verify that the PostgreSQL container still uses `172.18.0.2`.

## How To Get The Docker DB IP On The VPS

You usually obtain the Docker-side database IP on the VPS with `docker inspect`.

In this repository, the Compose service is `db`, and the running container is typically named:

```text
portfolio-dev-db-1
```

### 1. Find the PostgreSQL container on the VPS

SSH into the VPS and list containers:

```bash
ssh portfolio
docker ps --format 'table {{.Names}}\t{{.Image}}\t{{.Status}}'
```

Look for the Postgres container, for example:

```text
portfolio-dev-db-1   postgres:18   Up ...
```

### 2. Read its Docker network IP

```bash
docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' portfolio-dev-db-1
```

Example output:

```text
172.18.0.2
```

That is the IP you place into the SSH tunnel command:

```bash
ssh -N -L 25432:172.18.0.2:5432 portfolio
```

### 3. See the Docker network details if needed

```bash
docker inspect portfolio-dev-db-1
```

In the output, check:

- `.NetworkSettings.Networks`
- the network name
- the `IPAddress` value

## Why The Docker IP Is Used Here

The tunnel target is:

```text
172.18.0.2:5432
```

because SSH runs on the VPS, and from the VPS it can reach the Postgres container on the internal Docker bridge network.

So the flow is:

- pgAdmin connects to `127.0.0.1:25432` on your local machine
- SSH forwards that traffic to the VPS alias `portfolio`
- the VPS forwards it to the Docker container IP `172.18.0.2`
- PostgreSQL receives it on port `5432`

## pgAdmin Configuration Example

Use this configuration in pgAdmin:

- Name: `Portfolio VPS DB (SSH tunnel)`
- Host name/address: `127.0.0.1`
- Port: `25432`
- Maintenance database: `postgres`
- Username: `<postgres user>`
- Password: `<postgres password>`

Use the same database credentials that the VPS PostgreSQL container is configured with.

## Why pgAdmin Uses 127.0.0.1

pgAdmin should connect to `127.0.0.1`, not to `172.18.0.2` and not to the VPS hostname.

Reason:

- `172.18.0.2` exists only inside the VPS Docker network
- your local machine cannot reach that private container IP directly
- the SSH tunnel exposes the remote database locally on port `25432`

## Cheatsheet

### Start tunnel

```bash
ssh -N -L 25432:172.18.0.2:5432 portfolio
```

### Start tunnel in background

```bash
ssh -f -N -L 25432:172.18.0.2:5432 portfolio
```

### Test the local forwarded port with psql

```bash
psql -h 127.0.0.1 -p 25432 -U <postgres user> -d postgres
```

### Check whether the local tunnel port is listening

```bash
lsof -iTCP:25432 -sTCP:LISTEN
```

### Stop a background tunnel

```bash
pkill -f "ssh -f -N -L 25432:172.18.0.2:5432 portfolio"
```

## Troubleshooting

### pgAdmin cannot connect

Check:

- the SSH alias `portfolio` works
- the tunnel command is still running
- pgAdmin uses `127.0.0.1` as host
- pgAdmin uses port `25432`
- PostgreSQL is still listening on `5432` inside the container
- the container IP is still `172.18.0.2`

### Port `25432` already in use locally

Pick another free local port, for example:

```bash
ssh -N -L 35432:172.18.0.2:5432 portfolio
```

Then update pgAdmin to use:

- Host name/address: `127.0.0.1`
- Port: `35432`

## Security Notes

- The database stays private on the VPS side; only SSH exposes it to your local machine.
- Prefer binding pgAdmin to the local forwarded port only.
- Close the tunnel when you no longer need DB access.

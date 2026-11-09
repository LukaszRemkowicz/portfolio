import http.client
import json
import os
import re
import shutil
import subprocess
import tempfile
import time
import unittest
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
RENDERER = "/docker-entrypoint.d/18-render-text-resources.sh"
ADMIN_DOMAIN = "admin.portfolio.example.test"
API_DOMAIN = "api.portfolio.example.test"
PUBLIC_DOMAIN = "portfolio.example.test"
CONTACT_EMAIL = "security@example.test"


def docker(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["docker", *args],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


class NginxTextResourcesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        if shutil.which("docker") is None:
            raise unittest.SkipTest("Docker is required for Nginx integration tests")

        cls.suffix = uuid.uuid4().hex[:10]
        cls.image = os.environ.get("NGINX_TEST_IMAGE")
        cls.owns_image = cls.image is None
        if cls.owns_image:
            cls.image = f"landingpage-nginx-text-resources-test:{cls.suffix}"
            result = docker(
                "build",
                "--file",
                "docker/nginx/Dockerfile",
                "--tag",
                cls.image,
                ".",
            )
            if result.returncode:
                raise RuntimeError(f"Nginx image build failed:\n{result.stderr}")

    @classmethod
    def tearDownClass(cls) -> None:
        if hasattr(cls, "container"):
            docker("rm", "--force", cls.container)
        if getattr(cls, "owns_image", False):
            docker("image", "rm", cls.image)

    def test_required_and_unsafe_renderer_values_fail_closed(self) -> None:
        cases = [
            ({"API_DOMAIN": API_DOMAIN, "SECURITY_CONTACT_EMAIL": CONTACT_EMAIL}, "ADMIN_DOMAIN"),
            ({"ADMIN_DOMAIN": ADMIN_DOMAIN, "SECURITY_CONTACT_EMAIL": CONTACT_EMAIL}, "API_DOMAIN"),
            ({"ADMIN_DOMAIN": ADMIN_DOMAIN, "API_DOMAIN": API_DOMAIN}, "SECURITY_CONTACT_EMAIL"),
            (
                {
                    "ADMIN_DOMAIN": f"{ADMIN_DOMAIN}\nreturn 200;",
                    "API_DOMAIN": API_DOMAIN,
                    "SECURITY_CONTACT_EMAIL": CONTACT_EMAIL,
                },
                "ADMIN_DOMAIN",
            ),
            (
                {
                    "ADMIN_DOMAIN": ADMIN_DOMAIN,
                    "API_DOMAIN": f"{API_DOMAIN}$(touch /tmp/nginx-injected)",
                    "SECURITY_CONTACT_EMAIL": CONTACT_EMAIL,
                },
                "API_DOMAIN",
            ),
            (
                {
                    "ADMIN_DOMAIN": ADMIN_DOMAIN,
                    "API_DOMAIN": API_DOMAIN,
                    "SECURITY_CONTACT_EMAIL": f"{CONTACT_EMAIL}\r\nX-Evil: yes",
                },
                "SECURITY_CONTACT_EMAIL",
            ),
        ]

        for values, expected_name in cases:
            with self.subTest(expected_name=expected_name, values=values):
                command = [
                    "run",
                    "--rm",
                    "--read-only",
                    "--tmpfs",
                    "/var/cache/nginx",
                    "--entrypoint",
                    RENDERER,
                ]
                for name, value in values.items():
                    command.extend(["--env", f"{name}={value}"])
                command.append(self.image)
                result = docker(*command)
                self.assertNotEqual(result.returncode, 0, result.stdout)
                self.assertIn(expected_name, result.stderr + result.stdout)

    def test_nginx_serves_domain_resources_without_frontend_or_backend(self) -> None:
        self.container = f"landingpage-nginx-text-resources-{self.suffix}"
        command = [
            "run",
            "--detach",
            "--name",
            self.container,
            "--read-only",
            "--tmpfs",
            "/var/cache/nginx",
            "--tmpfs",
            "/var/run",
            "--tmpfs",
            "/tmp",
            "--add-host",
            "be:127.0.0.1",
            "--publish",
            "127.0.0.1::80",
            "--env",
            f"ADMIN_DOMAIN={ADMIN_DOMAIN}",
            "--env",
            f"API_DOMAIN={API_DOMAIN}",
            "--env",
            f"SECURITY_CONTACT_EMAIL={CONTACT_EMAIL}",
            self.image,
        ]
        result = docker(*command)
        self.assertEqual(result.returncode, 0, result.stderr)

        port_result = docker("port", self.container, "80/tcp")
        self.assertEqual(port_result.returncode, 0, port_result.stderr)
        self.port = int(port_result.stdout.rsplit(":", 1)[1].strip())

        for _ in range(40):
            try:
                ready = self._request("/robots.txt", ADMIN_DOMAIN)[0] == 200
            except (OSError, http.client.HTTPException):
                ready = False
            if ready:
                break
            time.sleep(0.25)
        else:
            logs = docker("logs", self.container)
            self.fail(f"Nginx did not become ready:\n{logs.stderr or logs.stdout}")

        config_check = docker("exec", self.container, "nginx", "-t")
        self.assertEqual(config_check.returncode, 0, config_check.stderr + config_check.stdout)

        for domain in (ADMIN_DOMAIN, API_DOMAIN):
            with self.subTest(domain=domain, resource="robots"):
                status, headers, body = self._request("/robots.txt", domain)
                self.assertEqual(status, 200)
                self.assertIn("User-agent: *\nDisallow: /", body)
                self.assertEqual(headers.get("content-type"), "text/plain; charset=utf-8")
                self.assertEqual(headers.get("cache-control"), "public, max-age=3600")

            with self.subTest(domain=domain, resource="security.txt"):
                status, headers, body = self._request("/.well-known/security.txt", domain)
                self.assertEqual(status, 200)
                self.assertEqual(headers.get("content-type"), "text/plain; charset=utf-8")
                self.assertIn(f"Contact: mailto:{CONTACT_EMAIL}", body)
                self.assertIn(f"Canonical: https://{domain}/.well-known/security.txt", body)
                self.assertIn("Preferred-Languages: en, pl", body)
                expires_value = re.search(r"^Expires: (.+)$", body, re.MULTILINE)
                self.assertIsNotNone(expires_value)
                expires = datetime.fromisoformat(expires_value.group(1).replace("Z", "+00:00"))
                expected = datetime.now(timezone.utc) + timedelta(days=180)
                self.assertLess(abs((expires - expected).total_seconds()), 120)

        for path in ("/robots.txt", "/.well-known/security.txt"):
            with self.subTest(host="unknown.example.test", path=path):
                status, _, _ = self._request(path, "unknown.example.test")
                self.assertEqual(status, 404)

        for path in ("/robots.txt", "/.well-known/security.txt"):
            with self.subTest(host=PUBLIC_DOMAIN, path=path):
                status, _, _ = self._request(path, PUBLIC_DOMAIN)
                self.assertEqual(status, 404)

        for path in ("/", "/assets/app.js", "/service-worker.js"):
            with self.subTest(host=PUBLIC_DOMAIN, path=path):
                status, _, _ = self._request(path, PUBLIC_DOMAIN)
                self.assertEqual(status, 404)

        # These explicit Django routes still reach the configured backend upstream.
        for path in ("/sitemap.xml", "/v1/settings/"):
            with self.subTest(path=path):
                status, _, _ = self._request(path, PUBLIC_DOMAIN)
                self.assertEqual(status, 502)

    def test_compose_supplies_runtime_domains_and_contact(self) -> None:
        compose_admin_domain = "control.example.test"
        compose_variables: set[str] = set()
        for compose_file in (
            "docker-compose.yml",
            "docker-compose.common.yml",
            "docker-compose.prod.yml",
            "docker-compose.stage.yml",
        ):
            content = (REPO_ROOT / compose_file).read_text()
            compose_variables.update(re.findall(r"(?<!\$)\$\{([A-Z][A-Z0-9_]*)", content))

        fixture = {name: "fixture" for name in compose_variables}
        fixture.update(
            {
                "DB_BACKUP_DIR": "/tmp/landingpage-backups",
                "SITE_DOMAIN": PUBLIC_DOMAIN,
                "ADMIN_DOMAIN": compose_admin_domain,
                "API_DOMAIN": API_DOMAIN,
                "SECURITY_CONTACT_EMAIL": CONTACT_EMAIL,
                "ENVIRONMENT": "production",
                "TAG": "test",
            }
        )

        with tempfile.TemporaryDirectory(prefix="landingpage-compose-test-") as temp_dir:
            env_path = Path(temp_dir) / "compose.env"
            configurations = {
                "local": ["-f", "docker-compose.yml"],
                "prod": ["-f", "docker-compose.common.yml", "-f", "docker-compose.prod.yml"],
                "stage": ["-f", "docker-compose.common.yml", "-f", "docker-compose.stage.yml"],
            }
            for environment, compose_args in configurations.items():
                with self.subTest(environment=environment):
                    env_values = dict(fixture)
                    if environment == "local":
                        env_values.pop("SECURITY_CONTACT_EMAIL")
                    env_path.write_text("".join(f"{name}={value}\n" for name, value in env_values.items()))
                    configured = docker(
                        "compose",
                        "--env-file",
                        str(env_path),
                        *compose_args,
                        "config",
                        "--format",
                        "json",
                    )
                    self.assertEqual(configured.returncode, 0, configured.stderr)
                    config = json.loads(configured.stdout)
                    nginx = config["services"]["nginx"]
                    self.assertEqual(nginx["environment"]["ADMIN_DOMAIN"], compose_admin_domain)
                    self.assertEqual(nginx["environment"]["API_DOMAIN"], API_DOMAIN)
                    expected_contact = "security@example.invalid" if environment == "local" else CONTACT_EMAIL
                    self.assertEqual(nginx["environment"]["SECURITY_CONTACT_EMAIL"], expected_contact)
                    if environment == "prod":
                        self.assertEqual(
                            nginx["labels"]["traefik.http.routers.portfolio-prod-admin.rule"],
                            "Host(`control.example.test`)",
                        )
                    if environment == "local":
                        targets = {volume["target"] for volume in nginx["volumes"]}
                        self.assertIn("/docker-entrypoint.d/18-render-text-resources.sh", targets)
                        self.assertIn("/etc/nginx/text-resources/templates", targets)

            for environment in ("prod", "stage"):
                with self.subTest(environment=environment, missing_contact=True):
                    env_values = dict(fixture)
                    env_values.pop("SECURITY_CONTACT_EMAIL")
                    env_path.write_text("".join(f"{name}={value}\n" for name, value in env_values.items()))
                    configured = docker(
                        "compose",
                        "--env-file",
                        str(env_path),
                        *configurations[environment],
                        "config",
                        "--format",
                        "json",
                    )
                    self.assertNotEqual(configured.returncode, 0)
                    self.assertIn("SECURITY_CONTACT_EMAIL", configured.stderr)

    def _request(self, path: str, host: str) -> tuple[int, dict[str, str], str]:
        connection = http.client.HTTPConnection("127.0.0.1", self.port, timeout=2)
        try:
            connection.request("GET", path, headers={"Host": host})
            response = connection.getresponse()
            body = response.read().decode("utf-8")
            return response.status, {name.lower(): value for name, value in response.getheaders()}, body
        finally:
            connection.close()


if __name__ == "__main__":
    unittest.main()

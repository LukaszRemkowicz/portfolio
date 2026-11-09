import http.client
import os
import shutil
import subprocess
import tempfile
import time
import unittest
from pathlib import Path
from uuid import uuid4


class NginxMediaPrivacyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if (
            not shutil.which("docker")
            or subprocess.run(["docker", "info"], capture_output=True).returncode
        ):
            raise unittest.SkipTest("Docker daemon is unavailable")

        cls.root = Path(__file__).resolve().parents[3]
        temp_dir = "/private/tmp" if Path("/private/tmp").is_dir() else None
        cls.temp = tempfile.TemporaryDirectory(prefix="nginx-media-privacy-", dir=temp_dir)
        cls.work = Path(cls.temp.name)
        cls.name = f"nginx-media-privacy-{uuid4().hex[:12]}"
        cls.image = os.getenv("NGINX_TEST_IMAGE") or cls.name
        cls.owns_image = not bool(os.getenv("NGINX_TEST_IMAGE"))
        cls.addClassCleanup(cls.cleanup)

        media = cls.work / "media"
        for path in (
            "images/original/source.jpg",
            "images/legacy-source.jpg",
            "images/high_resolution/full.webp",
            "images/original_format/old-full.webp",
            "images/thumbnail/thumb.webp",
            "images/detail/detail.webp",
        ):
            file = media / path
            file.parent.mkdir(parents=True, exist_ok=True)
            file.write_text("fixture")

        if cls.owns_image:
            subprocess.run(
                [
                    "docker",
                    "build",
                    "-q",
                    "-f",
                    str(cls.root / "docker/nginx/Dockerfile"),
                    "-t",
                    cls.image,
                    str(cls.root),
                ],
                check=True,
            )

        run = subprocess.run(
            [
                "docker",
                "run",
                "-d",
                "--name",
                cls.name,
                "--add-host",
                "be:127.0.0.1",
                "--add-host",
                "fe:127.0.0.1",
                "-e",
                "ADMIN_DOMAIN=admin.privacy.example",
                "-e",
                "API_DOMAIN=api.privacy.example",
                "-e",
                "SECURITY_CONTACT_EMAIL=privacy@example.invalid",
                "-p",
                "127.0.0.1::80",
                "--mount",
                f"type=bind,source={media},target=/app/media,readonly",
                cls.image,
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        cls.port = (
            subprocess.check_output(["docker", "port", cls.name, "80/tcp"], text=True)
            .strip()
            .rsplit(":", 1)[-1]
        )
        deadline = time.monotonic() + 15
        while time.monotonic() < deadline:
            try:
                if cls.request("/health")[0] == 200:
                    break
            except OSError:
                time.sleep(0.2)
        else:
            raise RuntimeError(f"Nginx did not start: {run.stdout.strip()}")

    @classmethod
    def request(cls, path):
        connection = http.client.HTTPConnection("127.0.0.1", cls.port, timeout=3)
        connection.request("GET", path, headers={"Host": "privacy.example"})
        response = connection.getresponse()
        body = response.read()
        connection.close()
        return response.status, body

    @classmethod
    def cleanup(cls):
        subprocess.run(["docker", "rm", "-f", cls.name], capture_output=True)
        if cls.owns_image:
            subprocess.run(["docker", "image", "rm", cls.image], capture_output=True)
        cls.temp.cleanup()

    def test_only_thumbnail_and_detail_images_are_public(self):
        statuses = {
            "/media/images/original/source.jpg": (403, 404),
            "/media/images/legacy-source.jpg": (403, 404),
            "/media/images/high_resolution/full.webp": (403, 404),
            "/media/images/original_format/old-full.webp": (403, 404),
            "/media/about_me_images/../images/original/source.jpg": (403, 404),
            "/media/images/thumbnail/thumb.webp": (200,),
            "/media/images/detail/detail.webp": (200,),
        }
        for path, expected in statuses.items():
            with self.subTest(path=path):
                self.assertIn(self.request(path)[0], expected)


if __name__ == "__main__":
    unittest.main()

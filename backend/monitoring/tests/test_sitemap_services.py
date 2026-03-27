from collections import Counter
from dataclasses import dataclass, field

import requests

from monitoring.sitemap_services import SitemapAuditService, SitemapHTTPClient
from monitoring.types import SitemapIssue, SitemapIssueCategory


@dataclass(frozen=True)
class FakeResponse:
    status_code: int
    text: str
    url: str
    headers: dict[str, str] = field(default_factory=dict)


class FakeSession:
    def __init__(
        self,
        responses: dict[tuple[str, bool], FakeResponse],
        errors: dict[tuple[str, bool], Exception] | None = None,
    ) -> None:
        self.responses: dict[tuple[str, bool], FakeResponse] = responses
        self.errors: dict[tuple[str, bool], Exception] = errors or {}

    def get(
        self,
        url: str,
        *,
        timeout: float,
        allow_redirects: bool = True,
    ) -> FakeResponse:
        del timeout
        key: tuple[str, bool] = (url, allow_redirects)
        if key in self.errors:
            raise self.errors[key]
        return self.responses[key]


URLSET_XML = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url><loc>https://portfolio.example/</loc></url>
  <url><loc>https://portfolio.example/travel</loc></url>
</urlset>
"""


SITEMAP_INDEX_XML = """<?xml version="1.0" encoding="UTF-8"?>
<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <sitemap><loc>https://portfolio.example/sitemap-pages.xml</loc></sitemap>
  <sitemap><loc>https://portfolio.example/sitemap-travel.xml</loc></sitemap>
</sitemapindex>
"""


PAGES_XML = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url><loc>https://portfolio.example/</loc></url>
  <url><loc>https://portfolio.example/programming</loc></url>
</urlset>
"""


TRAVEL_XML = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url><loc>https://portfolio.example/travel</loc></url>
  <url><loc>https://portfolio.example/programming</loc></url>
</urlset>
"""


class TestSitemapAuditService:
    def test_collect_urls_expands_sitemap_index(self):
        responses: dict[tuple[str, bool], FakeResponse] = {
            ("https://portfolio.example/sitemap.xml", True): FakeResponse(
                status_code=200,
                text=SITEMAP_INDEX_XML,
                url="https://portfolio.example/sitemap.xml",
            ),
            ("https://portfolio.example/sitemap-pages.xml", True): FakeResponse(
                status_code=200,
                text=PAGES_XML,
                url="https://portfolio.example/sitemap-pages.xml",
            ),
            ("https://portfolio.example/sitemap-travel.xml", True): FakeResponse(
                status_code=200,
                text=TRAVEL_XML,
                url="https://portfolio.example/sitemap-travel.xml",
            ),
        }
        session: FakeSession = FakeSession(responses)
        service = SitemapAuditService(
            client=SitemapHTTPClient(session=session),
            production_domain="portfolio.example",
        )

        urls, total_sitemaps = service.collect_urls("https://portfolio.example/sitemap.xml")

        assert total_sitemaps == 3
        assert urls == [
            "https://portfolio.example/",
            "https://portfolio.example/programming",
            "https://portfolio.example/travel",
            "https://portfolio.example/programming",
        ]

    def test_audit_flags_duplicate_non_prod_and_broken_urls(self):
        responses: dict[tuple[str, bool], FakeResponse] = {
            ("https://portfolio.example/sitemap.xml", True): FakeResponse(
                status_code=200,
                text="""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url><loc>https://portfolio.example/</loc></url>
  <url><loc>https://staging.example/programming</loc></url>
  <url><loc>https://portfolio.example/broken</loc></url>
  <url><loc>https://portfolio.example/</loc></url>
</urlset>
""",
                url="https://portfolio.example/sitemap.xml",
            ),
            ("https://portfolio.example/", False): FakeResponse(
                status_code=200,
                text="<html></html>",
                url="https://portfolio.example/",
            ),
            ("https://staging.example/programming", False): FakeResponse(
                status_code=200,
                text="<html></html>",
                url="https://staging.example/programming",
            ),
            ("https://portfolio.example/broken", False): FakeResponse(
                status_code=404,
                text="<html></html>",
                url="https://portfolio.example/broken",
            ),
        }
        session: FakeSession = FakeSession(responses)
        service = SitemapAuditService(
            client=SitemapHTTPClient(session=session),
            production_domain="portfolio.example",
        )

        report = service.audit("https://portfolio.example/sitemap.xml")
        issue_categories: Counter[str] = Counter(issue.category.value for issue in report.issues)

        assert report.total_sitemaps == 1
        assert report.total_urls == 4
        assert issue_categories[SitemapIssueCategory.DUPLICATE_URL.value] == 1
        assert issue_categories[SitemapIssueCategory.NON_PROD_DOMAIN.value] == 1
        assert issue_categories[SitemapIssueCategory.BROKEN_URL.value] == 1

    def test_audit_flags_final_url_mismatch(self):
        responses: dict[tuple[str, bool], FakeResponse] = {
            ("https://portfolio.example/sitemap.xml", True): FakeResponse(
                status_code=200,
                text=URLSET_XML,
                url="https://portfolio.example/sitemap.xml",
            ),
            ("https://portfolio.example/", False): FakeResponse(
                status_code=301,
                text="",
                url="https://portfolio.example/",
                headers={"Location": "https://portfolio.example/home"},
            ),
            ("https://portfolio.example/", True): FakeResponse(
                status_code=200,
                text="<html></html>",
                url="https://portfolio.example/home",
            ),
            ("https://portfolio.example/travel", False): FakeResponse(
                status_code=200,
                text="<html></html>",
                url="https://portfolio.example/travel",
            ),
        }
        session: FakeSession = FakeSession(responses)
        service = SitemapAuditService(
            client=SitemapHTTPClient(session=session),
            production_domain="portfolio.example",
        )

        report = service.audit("https://portfolio.example/sitemap.xml")
        categories: list[SitemapIssueCategory] = [issue.category for issue in report.issues]

        assert SitemapIssueCategory.FINAL_URL_MISMATCH in categories

    def test_audit_records_fetch_errors(self):
        responses: dict[tuple[str, bool], FakeResponse] = {
            ("https://portfolio.example/sitemap.xml", True): FakeResponse(
                status_code=200,
                text=URLSET_XML,
                url="https://portfolio.example/sitemap.xml",
            ),
            ("https://portfolio.example/travel", False): FakeResponse(
                status_code=200,
                text="<html></html>",
                url="https://portfolio.example/travel",
            ),
        }
        errors: dict[tuple[str, bool], Exception] = {
            ("https://portfolio.example/", False): requests.RequestException("timeout"),
        }
        session: FakeSession = FakeSession(responses=responses, errors=errors)
        service = SitemapAuditService(
            client=SitemapHTTPClient(session=session),
            production_domain="portfolio.example",
        )

        report = service.audit("https://portfolio.example/sitemap.xml")
        categories: list[SitemapIssueCategory] = [issue.category for issue in report.issues]

        assert SitemapIssueCategory.FETCH_ERROR in categories

    def test_audit_flags_canonical_mismatch_on_html_page(self):
        responses: dict[tuple[str, bool], FakeResponse] = {
            ("https://portfolio.example/sitemap.xml", True): FakeResponse(
                status_code=200,
                text=URLSET_XML,
                url="https://portfolio.example/sitemap.xml",
            ),
            ("https://portfolio.example/", False): FakeResponse(
                status_code=200,
                text=(
                    '<html><head><link rel="canonical" '
                    'href="https://portfolio.example/home"></head></html>'
                ),
                url="https://portfolio.example/",
            ),
            ("https://portfolio.example/travel", False): FakeResponse(
                status_code=200,
                text="<html></html>",
                url="https://portfolio.example/travel",
            ),
        }
        session: FakeSession = FakeSession(responses)
        service = SitemapAuditService(
            client=SitemapHTTPClient(session=session),
            production_domain="portfolio.example",
        )

        report = service.audit("https://portfolio.example/sitemap.xml")
        categories: list[SitemapIssueCategory] = [issue.category for issue in report.issues]

        assert SitemapIssueCategory.CANONICAL_MISMATCH in categories

    def test_audit_flags_noindex_from_meta_robots_and_headers(self):
        responses: dict[tuple[str, bool], FakeResponse] = {
            ("https://portfolio.example/sitemap.xml", True): FakeResponse(
                status_code=200,
                text=URLSET_XML,
                url="https://portfolio.example/sitemap.xml",
            ),
            ("https://portfolio.example/", False): FakeResponse(
                status_code=200,
                text='<html><head><meta name="robots" content="index, noindex"></head></html>',
                url="https://portfolio.example/",
            ),
            ("https://portfolio.example/travel", False): FakeResponse(
                status_code=200,
                text="<html></html>",
                url="https://portfolio.example/travel",
                headers={"X-Robots-Tag": "noindex"},
            ),
        }
        session: FakeSession = FakeSession(responses)
        service = SitemapAuditService(
            client=SitemapHTTPClient(session=session),
            production_domain="portfolio.example",
        )

        report = service.audit("https://portfolio.example/sitemap.xml")
        issue_categories: Counter[str] = Counter(issue.category.value for issue in report.issues)

        assert issue_categories[SitemapIssueCategory.NOINDEX_PAGE.value] == 2

    def test_summarize_issues_returns_category_counts(self):
        service = SitemapAuditService(
            client=SitemapHTTPClient(session=FakeSession({})),
            production_domain="portfolio.example",
        )
        issues: list[SitemapIssue] = [
            SitemapIssue(
                url="https://portfolio.example/a",
                category=SitemapIssueCategory.BROKEN_URL,
                message="broken",
                status_code=404,
            ),
            SitemapIssue(
                url="https://portfolio.example/b",
                category=SitemapIssueCategory.BROKEN_URL,
                message="broken",
                status_code=500,
            ),
            SitemapIssue(
                url="https://portfolio.example/c",
                category=SitemapIssueCategory.NON_PROD_DOMAIN,
                message="wrong domain",
            ),
            SitemapIssue(
                url="https://portfolio.example/d",
                category=SitemapIssueCategory.NOINDEX_PAGE,
                message="noindex",
            ),
        ]

        summary: dict[str, int] = service.summarize_issues(issues)

        assert summary == {
            SitemapIssueCategory.BROKEN_URL.value: 2,
            SitemapIssueCategory.NON_PROD_DOMAIN.value: 1,
            SitemapIssueCategory.NOINDEX_PAGE.value: 1,
        }

from collections import Counter
from collections.abc import Iterable
from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse
from xml.etree import ElementTree

import requests

from django.conf import settings

from .protocols import HTTPSession
from .types import HTTPResponseData, SitemapIssue, SitemapIssueCategory, SitemapReportResult


class SitemapHTTPClient:
    def __init__(
        self,
        session: HTTPSession | None = None,
        timeout_seconds: float = 10.0,
        verify_ssl: bool = True,
        internal_base_url: str | None = None,
        public_host: str | None = None,
    ) -> None:
        resolved_session: HTTPSession = session or requests.Session()
        self.session: HTTPSession = resolved_session
        self.timeout_seconds: float = timeout_seconds
        self.verify_ssl: bool = verify_ssl
        self.internal_base_url: str | None = (
            internal_base_url.rstrip("/") if internal_base_url else None
        )
        self.public_host: str | None = public_host

    def get(self, url: str, allow_redirects: bool = True) -> HTTPResponseData:
        request_url: str = url
        request_headers: dict[str, str] | None = None
        if self.internal_base_url and self.public_host:
            parsed_url = urlparse(url)
            if parsed_url.netloc == self.public_host:
                request_url = f"{self.internal_base_url}{parsed_url.path or '/'}"
                if parsed_url.query:
                    request_url = f"{request_url}?{parsed_url.query}"
                request_headers = {"Host": self.public_host}

        response: requests.Response = self.session.get(
            request_url,
            timeout=self.timeout_seconds,
            allow_redirects=allow_redirects,
            verify=self.verify_ssl,
            headers=request_headers,
        )
        response_headers: dict[str, str] = dict(response.headers)
        return HTTPResponseData(
            status_code=response.status_code,
            text=response.text,
            url=response.url,
            headers=response_headers,
        )


class SitemapXMLParser:
    @staticmethod
    def parse_locations(xml_text: str) -> tuple[str, list[str]]:
        root: ElementTree.Element = ElementTree.fromstring(xml_text)
        root_tag: str = SitemapXMLParser._strip_namespace(root.tag)
        locations: list[str] = []

        for element in root.iter():
            if SitemapXMLParser._strip_namespace(element.tag) != "loc":
                continue
            value: str = (element.text or "").strip()
            if value:
                locations.append(value)

        return root_tag, locations

    @staticmethod
    def _strip_namespace(tag_name: str) -> str:
        if "}" in tag_name:
            return tag_name.split("}", 1)[1]
        return tag_name


class HTMLMetadataParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.canonical_href: str | None = None
        self.robots_directives: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes: dict[str, str] = {
            key.lower(): value for key, value in attrs if value is not None
        }

        if tag.lower() == "link" and self._is_canonical_link(attributes):
            href: str | None = attributes.get("href")
            if href and not self.canonical_href:
                self.canonical_href = href.strip()

        if tag.lower() != "meta":
            return

        metadata_name: str = attributes.get("name", "").strip().lower()
        if metadata_name != "robots":
            return

        content: str = attributes.get("content", "")
        directives: list[str] = [
            directive.strip().lower() for directive in content.split(",") if directive.strip()
        ]
        self.robots_directives.extend(directives)

    @staticmethod
    def _is_canonical_link(attributes: dict[str, str]) -> bool:
        rel_value: str = attributes.get("rel", "")
        rel_tokens: set[str] = {
            token.strip().lower() for token in rel_value.split() if token.strip()
        }
        return "canonical" in rel_tokens


class SitemapAuditService:
    def __init__(
        self,
        client: SitemapHTTPClient,
        production_domain: str | None = None,
    ) -> None:
        resolved_domain: str = production_domain or settings.SITE_DOMAIN
        self.client: SitemapHTTPClient = client
        self.production_domain: str = resolved_domain

    def get_default_sitemap_url(self) -> str:
        return f"https://{self.production_domain}/sitemap.xml"

    def collect_urls(self, root_sitemap_url: str | None = None) -> tuple[list[str], int]:
        sitemap_url: str = root_sitemap_url or self.get_default_sitemap_url()
        pending_sitemaps: list[str] = [sitemap_url]
        seen_sitemaps: set[str] = set()
        discovered_urls: list[str] = []

        while pending_sitemaps:
            current_sitemap_url: str = pending_sitemaps.pop(0)
            if current_sitemap_url in seen_sitemaps:
                continue
            seen_sitemaps.add(current_sitemap_url)

            response: HTTPResponseData = self.client.get(current_sitemap_url)
            root_tag, locations = SitemapXMLParser.parse_locations(response.text)
            if root_tag == "sitemapindex":
                pending_sitemaps.extend(locations)
                continue
            if root_tag == "urlset":
                discovered_urls.extend(locations)

        return discovered_urls, len(seen_sitemaps)

    def audit(self, root_sitemap_url: str | None = None) -> SitemapReportResult:
        sitemap_url: str = root_sitemap_url or self.get_default_sitemap_url()
        urls, total_sitemaps = self.collect_urls(sitemap_url)
        issues: list[SitemapIssue] = self._audit_urls(urls)
        return SitemapReportResult(
            root_sitemap_url=sitemap_url,
            total_sitemaps=total_sitemaps,
            total_urls=len(urls),
            issues=issues,
        )

    def summarize_issues(self, issues: Iterable[SitemapIssue]) -> dict[str, int]:
        counter: Counter[str] = Counter(issue.category.value for issue in issues)
        return dict(counter)

    def _audit_urls(self, urls: list[str]) -> list[SitemapIssue]:
        issues: list[SitemapIssue] = []
        duplicates: set[str] = self._find_duplicates(urls)

        for duplicate_url in sorted(duplicates):
            issues.append(
                SitemapIssue(
                    url=duplicate_url,
                    category=SitemapIssueCategory.DUPLICATE_URL,
                    message="URL appears more than once in sitemap output.",
                )
            )

        unique_urls: list[str] = list(dict.fromkeys(urls))
        for url in unique_urls:
            issues.extend(self._audit_single_url(url))

        return issues

    def _audit_single_url(self, url: str) -> list[SitemapIssue]:
        issues: list[SitemapIssue] = []
        hostname: str = urlparse(url).netloc
        if hostname != self.production_domain:
            issues.append(
                SitemapIssue(
                    url=url,
                    category=SitemapIssueCategory.NON_PROD_DOMAIN,
                    message="URL host does not match the production domain.",
                )
            )

        try:
            response: HTTPResponseData = self.client.get(url, allow_redirects=False)
        except requests.RequestException as error:
            issues.append(
                SitemapIssue(
                    url=url,
                    category=SitemapIssueCategory.FETCH_ERROR,
                    message=f"Request failed: {error}",
                )
            )
            return issues

        status_code: int = response.status_code
        final_url: str = response.url

        if status_code >= 400:
            issues.append(
                SitemapIssue(
                    url=url,
                    category=SitemapIssueCategory.BROKEN_URL,
                    message="URL returned an error status.",
                    status_code=status_code,
                    final_url=final_url,
                )
            )
            return issues

        if status_code >= 300:
            followed_response: HTTPResponseData = self.client.get(url, allow_redirects=True)
            final_url = followed_response.url
            issues.append(
                SitemapIssue(
                    url=url,
                    category=SitemapIssueCategory.REDIRECT_IN_SITEMAP,
                    message="Sitemap URL redirects instead of resolving directly.",
                    status_code=status_code,
                    final_url=final_url,
                )
            )
            issues.append(
                SitemapIssue(
                    url=url,
                    category=SitemapIssueCategory.FINAL_URL_MISMATCH,
                    message="Final URL differs from the sitemap URL.",
                    status_code=status_code,
                    final_url=final_url,
                )
            )

        if status_code == 200:
            issues.extend(self._audit_page_metadata(url, response))

        return issues

    def _audit_page_metadata(self, url: str, response: HTTPResponseData) -> list[SitemapIssue]:
        issues: list[SitemapIssue] = []
        parser: HTMLMetadataParser = HTMLMetadataParser()
        parser.feed(response.text)

        canonical_href: str | None = parser.canonical_href
        if canonical_href:
            canonical_url: str = urljoin(url, canonical_href)
            if canonical_url != url:
                issues.append(
                    SitemapIssue(
                        url=url,
                        category=SitemapIssueCategory.CANONICAL_MISMATCH,
                        message="Canonical URL differs from the sitemap URL.",
                        status_code=response.status_code,
                        final_url=canonical_url,
                    )
                )

        robot_directives: list[str] = parser.robots_directives + self._parse_x_robots_tag(response)
        if "noindex" in robot_directives:
            issues.append(
                SitemapIssue(
                    url=url,
                    category=SitemapIssueCategory.NOINDEX_PAGE,
                    message="Page is marked as noindex.",
                    status_code=response.status_code,
                )
            )

        return issues

    @staticmethod
    def _parse_x_robots_tag(response: HTTPResponseData) -> list[str]:
        header_value: str = response.headers.get("X-Robots-Tag", "")
        directives: list[str] = [
            directive.strip().lower() for directive in header_value.split(",") if directive.strip()
        ]
        return directives

    @staticmethod
    def _find_duplicates(urls: list[str]) -> set[str]:
        counts: Counter[str] = Counter(urls)
        duplicates: set[str] = {url for url, count in counts.items() if count > 1}
        return duplicates

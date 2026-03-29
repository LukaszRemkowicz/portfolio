from datetime import date

import factory

from monitoring.models import LogAnalysis, SitemapAnalysis


class LogAnalysisFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = LogAnalysis

    analysis_date = factory.LazyFunction(date.today)
    summary = factory.Faker("text")
    severity = "INFO"
    log_size_bytes = 1024
    execution_time_seconds = 5.5
    gpt_tokens_used = 150
    key_findings = ["Database latency normal", "Cache hit rate high"]
    recommendations = "No action needed."
    email_sent = False


class SitemapAnalysisFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = SitemapAnalysis

    analysis_date = factory.LazyFunction(date.today)
    root_sitemap_url = "https://portfolio.example/sitemap.xml"
    total_sitemaps = 2
    total_urls = 20
    issue_summary = {"broken_url": 1}
    issues = [
        {
            "url": "https://portfolio.example/missing",
            "category": "broken_url",
            "message": "URL returned an error status.",
            "status_code": 404,
        }
    ]
    summary = "One sitemap URL needs attention."
    severity = "WARNING"
    key_findings = ["broken_url: 1"]
    recommendations = "Fix the broken sitemap URL."
    trend_summary = "A new sitemap issue appeared in this run."
    execution_time_seconds = 4.2
    gpt_tokens_used = 120
    gpt_cost_usd = 0.0034
    email_sent = False

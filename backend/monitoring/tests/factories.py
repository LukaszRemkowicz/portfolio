from datetime import date

import factory

from monitoring.models import LogAnalysis


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

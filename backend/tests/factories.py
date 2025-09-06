from datetime import date
import factory
from faker import Faker


fake = Faker()


class ProjectFactory(factory.Factory):
    class Meta:
        model = dict

    project_code = factory.LazyAttribute(lambda _: fake.unique.bothify(text="P####"))
    project_name = factory.LazyAttribute(lambda _: fake.sentence(nb_words=3))
    status = 1
    created_by = "test"
    updated_by = "test"


class ProjectHistoryFactory(factory.Factory):
    class Meta:
        model = dict

    project_code = factory.LazyAttribute(lambda _: fake.unique.bothify(text="P####"))
    entry_type = "Report"
    log_date = factory.LazyAttribute(lambda _: date(2025, 1, 6))
    summary = factory.LazyAttribute(lambda _: fake.paragraph())
    created_by = "test"
    updated_by = "test"


class WeeklyReportAnalysisFactory(factory.Factory):
    class Meta:
        model = dict

    project_code = factory.LazyAttribute(lambda _: fake.unique.bothify(text="P####"))
    cw_label = "CW02"
    language = "EN"
    category = "Development"
    created_by = "test"


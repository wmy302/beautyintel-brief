from enum import StrEnum


class SourceType(StrEnum):
    rss = "rss"
    webpage = "webpage"
    api = "api"
    xhs_api = "xhs_api"
    manual_csv = "manual_csv"
    manual_json = "manual_json"
    placeholder = "placeholder"

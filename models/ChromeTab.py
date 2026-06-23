from dataclasses import dataclass, asdict

from models.ChromeSource import ChromeSource


@dataclass
class ChromeTab:

    handle: str | None
    title: str
    url: str
    source: ChromeSource

    def to_dict(self):
        data = asdict(self)
        data["source"] = self.source.value
        return data

    @classmethod
    def from_dict(cls, data):

        return cls(
            handle=data.get("handle"),
            title=data.get("title", ""),
            url=data.get("url", ""),
            source=ChromeSource(data.get("source", "chrome_api"))
        )
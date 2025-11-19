from dataclasses import dataclass


@dataclass
class Episode:
    """Represents a single episode."""

    season: int
    episode: int
    link: str
    filename: str
    source: str

from __future__ import annotations
import logging
import json
from typing import Union
from attr import define, field
from griptape.artifacts import BaseArtifact, TextArtifact, ErrorArtifact
from schema import Schema, Literal
from griptape.core import BaseTool
from griptape.core.decorators import activity


@define
class WebScraper(BaseTool):
    include_links: bool = field(default=True, kw_only=True, metadata={"env": "INCLUDE_LINKS"})

    @activity(config={
        "name": "get_title",
        "description": "Can be used to get the title of a web page",
        "schema": Schema({
            Literal(
                "url",
                description="Valid HTTP URL"
            ): str
        })
    })
    def get_title(self, params: dict) -> BaseArtifact:
        url = params["values"]["url"]
        page = self._load_page(url)

        if isinstance(page, ErrorArtifact):
            return page
        else:
            return TextArtifact(page.get("title"))

    @activity(config={
        "name": "get_content",
        "description": "Can be used to get all text content of a web page",
        "schema": Schema({
            Literal(
                "url",
                description="Valid HTTP URL"
            ): str
        })
    })
    def get_content(self, params: dict) -> BaseArtifact:
        url = params["values"]["url"]
        page = self._load_page(url)

        if isinstance(page, ErrorArtifact):
            return page
        else:
            return TextArtifact(page.get("text"))

    @activity(config={
        "name": "get_author",
        "description": "Can be used to get web page author",
        "schema": Schema({
            Literal(
                "url",
                description="Valid HTTP URL"
            ): str
        })
    })
    def get_author(self, params: dict) -> BaseArtifact:
        url = params["values"]["url"]
        page = self._load_page(url)

        if isinstance(page, ErrorArtifact):
            return page
        else:
            return TextArtifact(page.get("author"))

    def _load_page(self, url: str) -> Union[dict, ErrorArtifact]:
        import trafilatura
        from trafilatura.settings import use_config

        config = use_config()
        page = trafilatura.fetch_url(url)

        # This disables signal, so that trafilatura can work on any thread:
        # More info: https://trafilatura.readthedocs.io/en/latest/usage-python.html#disabling-signal
        config.set("DEFAULT", "EXTRACTION_TIMEOUT", "0")

        # Disable error logging in trafilatura as it sometimes logs errors from lxml, even though
        # the end result of page parsing is successful.
        logging.getLogger("trafilatura").setLevel(logging.FATAL)

        if page is None:
            return ErrorArtifact("error: can't access URL")
        else:
            return json.loads(
                trafilatura.extract(
                    page,
                    include_links=self.env_value("INCLUDE_LINKS"),
                    output_format="json",
                    config=config
                )
            )

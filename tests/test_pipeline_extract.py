"""Tests for scripts/pipeline_extract.py (Issue #12 — Extract stage, spec §8)."""
import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from scripts.pipeline_extract import (  # noqa: E402
    build_prompt, dedupe_against_existing, extract_article, extract_json_object,
    html_to_text, make_anthropic_client, make_firecrawl_scraper,
    make_llm_client_from_env, make_openai_compatible_client, validate_extraction)


class TestHtmlToText(unittest.TestCase):
    def test_strips_tags_scripts_and_collapses_whitespace(self):
        html = "<html><head><style>body{}</style></head><body><h1>Big news</h1>" \
               "<script>evil()</script><p>  YTL   plans\n 50MW  </p></body></html>"
        text = html_to_text(html)
        self.assertNotIn("body{}", text)
        self.assertNotIn("evil()", text)
        self.assertIn("Big news", text)
        self.assertIn("YTL plans 50MW", text)


class TestBuildPrompt(unittest.TestCase):
    def test_prompt_embeds_instructions_article_and_schema(self):
        prompt = build_prompt("Some article text about MW.")
        self.assertIn("Some article text about MW.", prompt)
        for field in ["name", "operator", "capacity_mw", "location"]:
            self.assertIn(field, prompt)
        self.assertIn("return nothing", prompt.lower())


class TestValidateExtraction(unittest.TestCase):
    def test_valid_full_extraction_passes(self):
        ok, errs = validate_extraction({
            "name": "Foo DC", "capacity_mw": 50, "capacity_type": "estimated",
            "status": "planned"})
        self.assertTrue(ok, errs)

    def test_missing_name_fails(self):
        ok, errs = validate_extraction({"capacity_mw": 50})
        self.assertFalse(ok)
        self.assertTrue(any("name" in e for e in errs))

    def test_non_numeric_mw_fails(self):
        ok, errs = validate_extraction({"name": "X", "capacity_mw": "fifty"})
        self.assertFalse(ok)

    def test_bad_capacity_type_fails(self):
        ok, errs = validate_extraction({"name": "X", "capacity_type": "sure"})
        self.assertFalse(ok)

    def test_unknown_to_public_status_fails(self):
        ok, errs = validate_extraction({"name": "X", "status": "exploding"})
        self.assertFalse(ok)


class TestExtractArticle(unittest.TestCase):
    def test_model_says_nothing_found_produces_no_row(self):
        client = lambda text: {"found": False}
        row, reason = extract_article("<p>cats are cute</p>", "http://x/a", client,
                                      today="2026-08-26")
        self.assertIsNone(row)
        self.assertEqual(reason, "no facts found")

    def test_relevant_article_yields_normalized_row_with_provenance(self):
        client = lambda text: {
            "found": True, "name": "Foo DC", "operator": "Foo Co",
            "address": "Kulai, Johor", "capacity_mw": 50, "capacity_type": "estimated"}
        row, reason = extract_article("<p>...</p>", "http://x/a", client, today="2026-08-26")
        self.assertEqual(row["name"], "Foo DC")
        self.assertEqual(row["capacity_source"], "article: http://x/a")
        self.assertEqual(row["last_updated"], "2026-08-26")
        self.assertEqual(row["report_url"], "http://x/a")

    def test_invalid_model_output_is_skipped_with_reason(self):
        client = lambda text: {"found": True, "capacity_mw": 50}  # no name
        row, reason = extract_article("<p>x</p>", "http://x/a", client, today="2026-08-26")
        self.assertIsNone(row)
        self.assertIn("name", reason)


class TestDedupeAgainstExisting(unittest.TestCase):
    def test_existing_name_plus_address_is_skipped_case_insensitively(self):
        existing = [{"name": "Foo DC", "address": "Kulai, Johor"}]
        new, skipped = dedupe_against_existing(
            [{"name": " foo dc ", "address": "kulai, johor"}], existing)
        self.assertEqual(new, [])
        self.assertEqual(skipped, 1)


class TestExtractJsonObject(unittest.TestCase):
    def test_parses_bare_json(self):
        self.assertEqual(extract_json_object('{"a": 1}'), {"a": 1})

    def test_parses_fenced_json_block_deepseek_style(self):
        self.assertEqual(extract_json_object('sure!\n```json\n{"a": 2}\n```\ndone'), {"a": 2})

    def test_returns_none_when_no_json_object(self):
        self.assertIsNone(extract_json_object("no json here"))


class TestAnthropicClient(unittest.TestCase):
    def test_posts_to_messages_api_and_parses_json_content(self):
        captured = {}

        def poster(url, headers, body):
            captured.update(url=url, headers=headers, body=body)
            return {"content": [{"type": "text",
                                 "text": '{"found": true, "name": "Foo DC"}'}]}

        client = make_anthropic_client(api_key="sk-test", model="m-test", poster=poster)
        out = client("article text")
        self.assertEqual(out["name"], "Foo DC")
        self.assertEqual(captured["url"], "https://api.anthropic.com/v1/messages")
        self.assertEqual(captured["headers"]["x-api-key"], "sk-test")
        self.assertEqual(captured["body"]["model"], "m-test")

    def test_non_json_model_text_returns_none(self):
        def poster(url, headers, body):
            return {"content": [{"type": "text", "text": "I cannot help"}]}
        client = make_anthropic_client(api_key="k", model="m", poster=poster)
        self.assertIsNone(client("x"))


class TestOpenAICompatibleClient(unittest.TestCase):
    def test_deepseek_style_endpoint_roundtrip(self):
        captured = {}

        def poster(url, headers, body):
            captured.update(url=url, headers=headers, body=body)
            return {"choices": [{"message": {"content": '```json\n{"found": true, "name": "DS DC"}\n```'}}]}

        client = make_openai_compatible_client(
            base_url="https://api.deepseek.com", api_key="sk-ds", model="deepseek-chat",
            poster=poster)
        self.assertEqual(client("text")["name"], "DS DC")
        self.assertEqual(captured["url"], "https://api.deepseek.com/chat/completions")
        self.assertEqual(captured["headers"]["Authorization"], "Bearer sk-ds")
        self.assertEqual(captured["body"]["model"], "deepseek-chat")


class TestEnvFactory(unittest.TestCase):
    def test_dispatches_anthropic(self):
        c = make_llm_client_from_env({"LLM_PROVIDER": "anthropic", "ANTHROPIC_API_KEY": "k"},
                                     poster=lambda *a: {"content": [{"text": '{"a":1}'}]})
        self.assertTrue(callable(c))

    def test_dispatches_deepseek_with_defaults(self):
        captured = {}

        def poster(url, headers, body):
            captured["url"] = url
            return {"choices": [{"message": {"content": "{}"}}]}

        c = make_llm_client_from_env(
            {"LLM_PROVIDER": "deepseek", "LLM_API_KEY": "k", "LLM_MODEL": "deepseek-chat"},
            poster=poster)
        c("x")
        self.assertEqual(captured["url"], "https://api.deepseek.com/chat/completions")

    def test_modal_style_custom_base_url(self):
        captured = {}

        def poster(url, headers, body):
            captured["url"] = url
            return {"choices": [{"message": {"content": "{}"}}]}

        c = make_llm_client_from_env(
            {"LLM_PROVIDER": "openai", "LLM_API_KEY": "k",
             "LLM_BASE_URL": "https://me--extract.modal.run/v1", "LLM_MODEL": "m"},
            poster=poster)
        c("x")
        self.assertEqual(captured["url"], "https://me--extract.modal.run/v1/chat/completions")

    def test_missing_key_raises_clear_error(self):
        with self.assertRaisesRegex(RuntimeError, "ANTHROPIC_API_KEY"):
            make_llm_client_from_env({"LLM_PROVIDER": "anthropic"}, poster=lambda *a: {})


class TestFirecrawlScraper(unittest.TestCase):
    def test_posts_url_and_returns_markdown(self):
        captured = {}

        def poster(url, headers, body):
            captured.update(url=url, headers=headers, body=body)
            return {"success": True, "data": {"markdown": "# clean article\n50 MW site"}}

        scrape = make_firecrawl_scraper(api_key="fc-test", poster=poster)
        text = scrape("https://x/article")
        self.assertIn("50 MW site", text)
        self.assertEqual(captured["url"], "https://api.firecrawl.dev/v1/scrape")
        self.assertEqual(captured["body"]["url"], "https://x/article")
        self.assertEqual(captured["body"]["formats"], ["markdown"])


if __name__ == "__main__":
    unittest.main()

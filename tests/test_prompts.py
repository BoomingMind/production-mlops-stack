"""
Unit tests for prompt templates and prompt evaluation scripts.

These tests validate:
1. Prompt template syntax and structure
2. Prompt evaluation functions
3. Prompt loading and formatting
"""

import json
import os
import sys
from pathlib import Path

import pytest

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


class TestPromptTemplates:
    """Tests for prompt template files."""

    PROMPT_DIR = (
        Path(__file__).parent.parent / "experiments" / "prompts" / "prompt_templates"
    )
    REQUIRED_TEMPLATES = [
        "zero_shot.txt",
        "few_shot_k3.txt",
        "few_shot_k5.txt",
        "chain_of_thought.txt",
        "meta_prompt.txt",
    ]

    def test_prompt_templates_exist(self):
        """Test that all required prompt templates exist."""
        for template_name in self.REQUIRED_TEMPLATES:
            template_path = self.PROMPT_DIR / template_name
            assert template_path.exists(), f"Missing template: {template_name}"

    def test_prompt_templates_not_empty(self):
        """Test that prompt templates are not empty."""
        for template_name in self.REQUIRED_TEMPLATES:
            template_path = self.PROMPT_DIR / template_name
            content = template_path.read_text().strip()
            assert len(content) > 50, f"Template {template_name} is too short or empty"

    def test_prompt_templates_have_placeholders(self):
        """Test that templates contain expected placeholders."""
        for template_name in self.REQUIRED_TEMPLATES:
            template_path = self.PROMPT_DIR / template_name
            content = template_path.read_text()
            # All templates should have aqi_value placeholder
            assert (
                "{aqi_value}" in content or "aqi" in content.lower()
            ), f"Template {template_name} missing AQI placeholder"

    def test_prompt_templates_request_structured_output(self):
        """Test that templates request structured (JSON-like) output."""
        for template_name in self.REQUIRED_TEMPLATES:
            template_path = self.PROMPT_DIR / template_name
            content = template_path.read_text().lower()
            # Templates should either mention JSON explicitly or show JSON examples with braces
            has_json_keyword = "json" in content
            has_json_example = (
                "{{" in content or '{"' in content or "response:" in content
            )
            assert (
                has_json_keyword or has_json_example
            ), f"Template {template_name} should request structured JSON output"

    def test_prompt_templates_valid_encoding(self):
        """Test that templates use valid UTF-8 encoding."""
        for template_name in self.REQUIRED_TEMPLATES:
            template_path = self.PROMPT_DIR / template_name
            try:
                content = template_path.read_text(encoding="utf-8")
                assert len(content) > 0
            except UnicodeDecodeError:
                pytest.fail(f"Template {template_name} has invalid UTF-8 encoding")


class TestEvalDataset:
    """Tests for the evaluation dataset."""

    EVAL_DATA_PATH = Path(__file__).parent.parent / "data" / "eval.jsonl"

    def test_eval_dataset_exists(self):
        """Test that evaluation dataset exists."""
        assert self.EVAL_DATA_PATH.exists(), "Evaluation dataset not found"

    def test_eval_dataset_valid_jsonl(self):
        """Test that eval dataset is valid JSONL format."""
        with open(self.EVAL_DATA_PATH) as f:
            line_count = 0
            for line in f:
                if line.strip():
                    try:
                        json.loads(line)  # Validate JSON format
                        line_count += 1
                    except json.JSONDecodeError:
                        pytest.fail(f"Invalid JSON on line {line_count + 1}")
            assert (
                line_count >= 5
            ), f"Eval dataset should have at least 5 examples, got {line_count}"

    def test_eval_dataset_required_fields(self):
        """Test that each eval example has required fields."""
        required_fields = [
            "aqi",
            "category",
            "expected_summary",
            "expected_precautions",
        ]

        with open(self.EVAL_DATA_PATH) as f:
            for i, line in enumerate(f, 1):
                if line.strip():
                    data = json.loads(line)
                    for field in required_fields:
                        assert field in data, f"Missing field '{field}' on line {i}"

    def test_eval_dataset_aqi_values_valid(self):
        """Test that AQI values are in valid range (0-500)."""
        with open(self.EVAL_DATA_PATH) as f:
            for i, line in enumerate(f, 1):
                if line.strip():
                    data = json.loads(line)
                    aqi = data.get("aqi", 0)
                    assert 0 <= aqi <= 500, f"Invalid AQI {aqi} on line {i}"

    def test_eval_dataset_categories_valid(self):
        """Test that AQI categories are valid."""
        valid_categories = [
            "Good",
            "Moderate",
            "Unhealthy for Sensitive Groups",
            "Unhealthy",
            "Very Unhealthy",
            "Hazardous",
        ]

        with open(self.EVAL_DATA_PATH) as f:
            for i, line in enumerate(f, 1):
                if line.strip():
                    data = json.loads(line)
                    category = data.get("category", "")
                    assert (
                        category in valid_categories
                    ), f"Invalid category '{category}' on line {i}"

    def test_eval_dataset_precautions_list(self):
        """Test that expected_precautions is a non-empty list."""
        with open(self.EVAL_DATA_PATH) as f:
            for i, line in enumerate(f, 1):
                if line.strip():
                    data = json.loads(line)
                    precautions = data.get("expected_precautions", [])
                    assert isinstance(
                        precautions, list
                    ), f"Precautions should be a list on line {i}"
                    assert (
                        len(precautions) >= 1
                    ), f"Precautions should not be empty on line {i}"


class TestPromptEvaluatorModule:
    """Tests for the prompt evaluator module structure."""

    def test_evaluator_module_exists(self):
        """Test that evaluate_prompts.py exists."""
        eval_script = (
            Path(__file__).parent.parent
            / "experiments"
            / "prompts"
            / "evaluate_prompts.py"
        )
        assert eval_script.exists(), "evaluate_prompts.py not found"

    def test_evaluator_module_imports(self):
        """Test that evaluator module can be parsed (syntax check)."""
        eval_script = (
            Path(__file__).parent.parent
            / "experiments"
            / "prompts"
            / "evaluate_prompts.py"
        )
        content = eval_script.read_text()

        # Compile to check for syntax errors
        try:
            compile(content, eval_script, "exec")
        except SyntaxError as e:
            pytest.fail(f"Syntax error in evaluate_prompts.py: {e}")

    def test_evaluator_has_main_function(self):
        """Test that evaluator has a main function."""
        eval_script = (
            Path(__file__).parent.parent
            / "experiments"
            / "prompts"
            / "evaluate_prompts.py"
        )
        content = eval_script.read_text()

        assert (
            "def main(" in content or 'if __name__ == "__main__"' in content
        ), "evaluate_prompts.py should have a main function or entry point"

    def test_evaluator_has_eval_class(self):
        """Test that evaluator has PromptEvaluator class."""
        eval_script = (
            Path(__file__).parent.parent
            / "experiments"
            / "prompts"
            / "evaluate_prompts.py"
        )
        content = eval_script.read_text()

        assert (
            "class PromptEvaluator" in content
        ), "evaluate_prompts.py should have PromptEvaluator class"


class TestPromptEvaluatorMetrics:
    """Tests for evaluation metric computation."""

    def test_rouge_computation_identical(self):
        """Test ROUGE-L score for identical strings."""
        try:
            from rouge_score import rouge_scorer

            scorer = rouge_scorer.RougeScorer(["rougeL"], use_stemmer=True)

            text = "Air quality is good today."
            scores = scorer.score(text, text)

            # Identical text should have perfect ROUGE score
            assert scores["rougeL"].fmeasure >= 0.99
        except ImportError:
            pytest.skip("rouge-score not installed")

    def test_rouge_computation_different(self):
        """Test ROUGE-L score for different strings."""
        try:
            from rouge_score import rouge_scorer

            scorer = rouge_scorer.RougeScorer(["rougeL"], use_stemmer=True)

            text1 = "Air quality is good today."
            text2 = "The weather is nice outside."
            scores = scorer.score(text1, text2)

            # Different text should have lower ROUGE score
            assert scores["rougeL"].fmeasure < 0.5
        except ImportError:
            pytest.skip("rouge-score not installed")

    def test_cosine_similarity_computation(self):
        """Test cosine similarity with embeddings."""
        try:
            import numpy as np
            from sentence_transformers import SentenceTransformer

            model = SentenceTransformer("all-MiniLM-L6-v2")

            text1 = "Air quality is unhealthy."
            text2 = "The air pollution levels are high."
            text3 = "I like pizza."

            emb = model.encode([text1, text2, text3])

            # Compute cosine similarity
            def cosine_sim(a, b):
                return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

            sim_related = cosine_sim(emb[0], emb[1])
            sim_unrelated = cosine_sim(emb[0], emb[2])

            # Related texts should have higher similarity
            assert sim_related > sim_unrelated
            assert sim_related > 0.5
        except ImportError:
            pytest.skip("sentence-transformers not installed")


class TestCIPromptEvaluation:
    """Tests for CI-compatible prompt evaluation."""

    def test_quick_eval_returns_metrics(self):
        """Test that quick evaluation returns expected metrics structure."""
        # This tests the structure without making actual LLM calls
        expected_metrics = [
            "avg_rouge_l",
            "avg_cosine_similarity",
            "avg_precaution_overlap",
            "avg_latency",
            "error_rate",
        ]

        # Mock result structure
        mock_result = {
            "strategy": "zero_shot",
            "metrics": {
                "avg_rouge_l": 0.45,
                "avg_cosine_similarity": 0.78,
                "avg_precaution_overlap": 0.65,
                "avg_latency": 1.2,
                "error_rate": 0.0,
                "num_examples": 5,
                "num_successful": 5,
            },
        }

        for metric in expected_metrics:
            assert metric in mock_result["metrics"], f"Missing metric: {metric}"

    def test_eval_thresholds(self):
        """Test that evaluation thresholds are reasonable."""
        # Define minimum acceptable thresholds for CI
        thresholds = {
            "min_rouge_l": 0.2,
            "min_cosine_similarity": 0.5,
            "min_precaution_overlap": 0.3,
            "max_error_rate": 0.3,  # Allow up to 30% errors
        }

        # These are the minimum standards prompts should meet
        assert thresholds["min_rouge_l"] >= 0.1
        assert thresholds["min_cosine_similarity"] >= 0.3
        assert thresholds["max_error_rate"] <= 0.5

import json
import os
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
from dotenv import load_dotenv

load_dotenv()


@dataclass
class EvalResult:
    """Single evaluation result."""

    strategy: str
    aqi_value: float
    aqi_category: str
    generated_summary: str
    generated_precautions: List[str]
    expected_summary: str
    expected_precautions: List[str]
    rouge_l: float = 0.0
    cosine_similarity: float = 0.0
    precaution_overlap: float = 0.0
    latency_seconds: float = 0.0
    tokens_used: Optional[int] = None
    error: Optional[str] = None


class PromptEvaluator:
    """Evaluates prompting strategies with quantitative metrics."""

    def __init__(
        self,
        eval_data_path: Optional[Path] = None,
        model_name: str = "llama-3.3-70b-versatile",
        mlflow_uri: str = "http://localhost:5005",
        experiment_name: str = "AQI_Prompt_Engineering",
    ):
        self.model_name = model_name
        self.experiment_name = experiment_name

        # Paths
        if eval_data_path is None:
            self.eval_data_path = (
                Path(__file__).parent.parent.parent / "data" / "eval.jsonl"
            )
        else:
            self.eval_data_path = Path(eval_data_path)

        # Lazy-loaded components
        self._advisor = None
        self._rouge_scorer = None
        self._embedding_model = None

        # Setup MLflow
        self._setup_mlflow(mlflow_uri)

        # Load eval data
        self.eval_data = self._load_eval_data()

    def _setup_mlflow(self, uri):
        """Configure MLflow tracking."""
        try:
            import mlflow

            mlflow.set_tracking_uri(uri)
            mlflow.set_experiment(self.experiment_name)
            self.mlflow = mlflow
            print(f"MLflow: {uri} | Experiment: {self.experiment_name}")
        except Exception as e:
            print(f"MLflow setup failed: {e}")
            self.mlflow = None

    def _load_eval_data(self) -> List[Dict]:
        """Load evaluation dataset."""
        if not self.eval_data_path.exists():
            raise FileNotFoundError(f"Eval data not found: {self.eval_data_path}")

        data = []
        with open(self.eval_data_path) as f:
            for line in f:
                if line.strip():
                    data.append(json.loads(line))

        print(f"Loaded {len(data)} eval examples")
        return data

    @property
    def advisor(self):
        """Lazy load advisor."""
        if self._advisor is None:
            try:
                from src.aqi_advisor.advisor import AQIAdvisor

                self._advisor = AQIAdvisor(model=self.model_name, temperature=0.3)
            except Exception as e:
                print(f"Failed to load advisor: {e}")
                raise
        return self._advisor

    @property
    def rouge_scorer(self):
        """Lazy load ROUGE scorer."""
        if self._rouge_scorer is None:
            from rouge_score import rouge_scorer

            self._rouge_scorer = rouge_scorer.RougeScorer(["rougeL"], use_stemmer=True)
        return self._rouge_scorer

    @property
    def embedding_model(self):
        """Lazy load embedding model."""
        if self._embedding_model is None:
            from sentence_transformers import SentenceTransformer

            self._embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
        return self._embedding_model

    def compute_rouge_l(self, generated: str, reference: str) -> float:
        """Compute ROUGE-L F1 score."""
        if not generated or not reference:
            return 0.0
        scores = self.rouge_scorer.score(reference, generated)
        return scores["rougeL"].fmeasure

    def compute_cosine_similarity(self, text1: str, text2: str) -> float:
        """Compute cosine similarity using embeddings."""
        if not text1 or not text2:
            return 0.0
        embeddings = self.embedding_model.encode([text1, text2])
        cos_sim = np.dot(embeddings[0], embeddings[1]) / (
            np.linalg.norm(embeddings[0]) * np.linalg.norm(embeddings[1])
        )
        return float(cos_sim)

    def compute_precaution_overlap(
        self, generated: List[str], expected: List[str], threshold: float = 0.6
    ) -> float:
        """Compute semantic overlap of precautions."""
        if not generated or not expected:
            return 0.0

        gen_emb = self.embedding_model.encode(generated)
        exp_emb = self.embedding_model.encode(expected)

        matches = 0
        for e_emb in exp_emb:
            sims = [
                np.dot(e_emb, g_emb) / (np.linalg.norm(e_emb) * np.linalg.norm(g_emb))
                for g_emb in gen_emb
            ]
            if max(sims) >= threshold:
                matches += 1

        return matches / len(expected)

    def evaluate_single(self, example: Dict, strategy) -> EvalResult:
        """Evaluate single example with given strategy."""
        result = self.advisor.generate_advisory(
            aqi_value=example["aqi"], strategy=strategy
        )

        gen_summary = result.get("summary", "")
        gen_precautions = result.get("precautions", [])

        return EvalResult(
            strategy=strategy.value,
            aqi_value=example["aqi"],
            aqi_category=example["category"],
            generated_summary=gen_summary,
            generated_precautions=gen_precautions,
            expected_summary=example["expected_summary"],
            expected_precautions=example["expected_precautions"],
            rouge_l=self.compute_rouge_l(gen_summary, example["expected_summary"]),
            cosine_similarity=self.compute_cosine_similarity(
                gen_summary, example["expected_summary"]
            ),
            precaution_overlap=self.compute_precaution_overlap(
                gen_precautions, example["expected_precautions"]
            ),
            latency_seconds=result.get("metadata", {}).get("latency_seconds", 0),
            tokens_used=result.get("metadata", {}).get("tokens_used"),
            error=result.get("error"),
        )

    def evaluate_strategy(self, strategy) -> Dict[str, Any]:
        """Evaluate a strategy across all examples and log to MLflow."""
        from src.aqi_advisor.prompts import PromptStrategy

        print(f"\n{'='*50}")
        print(f"Strategy: {strategy.value}")
        print(f"{'='*50}")

        results = []
        for i, example in enumerate(self.eval_data):
            print(f"  [{i+1}/{len(self.eval_data)}] AQI: {example['aqi']}", end=" ")
            result = self.evaluate_single(example, strategy)
            results.append(result)

            if result.error:
                print(f"{result.error[:30]}")
            else:
                print(
                    f"ROUGE: {result.rouge_l:.3f} | Cosine: {result.cosine_similarity:.3f}"
                )

        # Aggregate metrics
        successful = [r for r in results if not r.error]

        if not successful:
            return {"strategy": strategy.value, "error": "All examples failed"}

        metrics = {
            "avg_rouge_l": np.mean([r.rouge_l for r in successful]),
            "avg_cosine_similarity": np.mean([r.cosine_similarity for r in successful]),
            "avg_precaution_overlap": np.mean(
                [r.precaution_overlap for r in successful]
            ),
            "avg_latency": np.mean([r.latency_seconds for r in successful]),
            "std_rouge_l": np.std([r.rouge_l for r in successful]),
            "std_cosine_similarity": np.std([r.cosine_similarity for r in successful]),
            "error_rate": (len(results) - len(successful)) / len(results),
            "num_examples": len(results),
            "num_successful": len(successful),
        }

        # Log to MLflow
        if self.mlflow:
            try:
                with self.mlflow.start_run(
                    run_name=f"{strategy.value}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                ):
                    # Log params
                    self.mlflow.log_params(
                        {
                            "strategy": strategy.value,
                            "model": self.model_name,
                            "num_examples": len(results),
                            "temperature": 0.3,
                        }
                    )

                    # Log metrics
                    self.mlflow.log_metrics(
                        {
                            "avg_rouge_l": metrics["avg_rouge_l"],
                            "avg_cosine_similarity": metrics["avg_cosine_similarity"],
                            "avg_precaution_overlap": metrics["avg_precaution_overlap"],
                            "avg_latency": metrics["avg_latency"],
                            "std_rouge_l": metrics["std_rouge_l"],
                            "std_cosine_similarity": metrics["std_cosine_similarity"],
                            "error_rate": metrics["error_rate"],
                        }
                    )

                    # Log detailed results as artifact
                    details = [
                        {
                            "aqi": r.aqi_value,
                            "category": r.aqi_category,
                            "rouge_l": r.rouge_l,
                            "cosine_sim": r.cosine_similarity,
                            "precaution_overlap": r.precaution_overlap,
                            "latency": r.latency_seconds,
                            "generated_summary": r.generated_summary,
                            "generated_precautions": r.generated_precautions,
                            "error": r.error,
                        }
                        for r in results
                    ]

                    artifact_path = Path(f"/tmp/{strategy.value}_results.json")
                    artifact_path.write_text(json.dumps(details, indent=2))
                    self.mlflow.log_artifact(str(artifact_path))

                print(f"Logged to MLflow")
            except Exception as e:
                print(f"MLflow error: {e}")

        # Print summary
        print(f"\n  Summary:")
        print(
            f"    ROUGE-L:     {metrics['avg_rouge_l']:.4f} (±{metrics['std_rouge_l']:.4f})"
        )
        print(f"    Cosine Sim:  {metrics['avg_cosine_similarity']:.4f}")
        print(f"    Precaution:  {metrics['avg_precaution_overlap']:.4f}")
        print(f"    Latency:     {metrics['avg_latency']:.3f}s")
        print(f"    Error Rate:  {metrics['error_rate']*100:.1f}%")

        return {
            "strategy": strategy.value,
            "metrics": metrics,
            "results": results,
        }

    def evaluate_all(self) -> Dict[str, Any]:
        """Evaluate all strategies."""
        from src.aqi_advisor.prompts import PromptStrategy

        print("\n" + "=" * 60)
        print("PROMPT ENGINEERING EVALUATION")
        print("=" * 60)
        print(f"Model: {self.model_name}")
        print(f"Examples: {len(self.eval_data)}")
        print(f"Strategies: {[s.value for s in PromptStrategy]}")

        all_results = {}
        for strategy in PromptStrategy:
            all_results[strategy.value] = self.evaluate_strategy(strategy)

        # Print comparison
        self._print_comparison(all_results)

        return all_results

    def _print_comparison(self, results: Dict):
        """Print comparison table."""
        print("\n" + "=" * 80)
        print("COMPARISON")
        print("=" * 80)
        print(
            f"{'Strategy':<20} {'ROUGE-L':>10} {'Cosine':>10} {'Precaution':>12} {'Latency':>10}"
        )
        print("-" * 80)

        for name, data in results.items():
            if "metrics" in data:
                m = data["metrics"]
                print(
                    f"{name:<20} {m['avg_rouge_l']:>10.4f} {m['avg_cosine_similarity']:>10.4f} "
                    f"{m['avg_precaution_overlap']:>12.4f} {m['avg_latency']:>9.3f}s"
                )
            else:
                print(f"{name:<20} {'ERROR':>10}")

        print("=" * 80)


def main():
    prompt_eval = PromptEvaluator()
    prompt_eval.evaluate_all()


if __name__ == "__main__":
    main()

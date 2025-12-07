import json
import os
from typing import Dict, Any, Optional
import time

from dotenv import load_dotenv

from groq import Groq

from src.aqi_advisor.prompts import PromptStrategy, get_aqi_category, PromptLoader

load_dotenv()


class AQIAdvisor:
    """
    AQI Health Advisory Generator using LLM.

    This class handles:
    1. Loading and formatting prompts
    2. Calling the OpenAI API
    3. Parsing and returning structured responses

    Example usage:
        advisor = AQIAdvisor()
        result = advisor.generate_advisory(aqi_value=150)
        print(result["summary"])
        print(result["precautions"])
    """

    def __init__(self, model, temperature: float = 0.3, api_key: Optional[str] = None):
        self.model = model
        self.prompt_loader = PromptLoader()
        self.temperature = temperature

        api_key = os.getenv("OPENAI_API_KEY")

        if not api_key:
            raise ValueError(
                "OpenAI API key required!\n"
                "Set it in your .env file:\n"
                "OPENAI_API_KEY=sk-your-key-here"
            )

        try:
            self.client = Groq(api_key=api_key)
            print(f"Groq client initialized with model: {model}")

        except ImportError:
            raise ImportError(
                "openai package not installed!\n" "Run: pip install openai"
            )

    def _parse_json_response(self, response_text: str) -> Dict[str, Any]:
        """
        Parse JSON from the model's response.

        Handles cases where the model wraps JSON in markdown code blocks.

        Args:
            response_text: Raw response from the model

        Returns:
            Parsed JSON as dictionary
        """
        text = response_text.strip()

        # Handle markdown code blocks
        if "```json" in text:
            # Extract content between ```json and ```
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            # Extract content between ``` and ```
            text = text.split("```")[1].split("```")[0].strip()

        return json.loads(text)

    def generate_advisory(
        self, aqi_value, strategy: PromptStrategy, aqi_category: Optional[str] = None
    ) -> Dict:
        """
        Generate a health advisory for the given AQI value.

        This is the main method you'll use!

        Args:
            aqi_value: The AQI value (0-500+)
            strategy: Prompting strategy (ZERO_SHOT for now)
            aqi_category: Optional category override

        Returns:
            Dictionary containing:
            {
                "summary": "Health impact summary...",
                "precautions": ["precaution 1", "precaution 2", ...],
                "metadata": {
                    "model": "gpt-3.5-turbo",
                    "strategy": "zero_shot",
                    "aqi_value": 150,
                    "aqi_category": "Unhealthy for Sensitive Groups",
                    "latency_seconds": 1.23,
                    "tokens_used": 150
                }
            }
        """

        if aqi_category is None:
            aqi_category = get_aqi_category(aqi_value)

        # Load and format the prompt
        prompt = self.prompt_loader.format_prompt(
            strategy=strategy, aqi_value=aqi_value, aqi_category=aqi_category
        )

        print(prompt)
        # Call the OpenAI API
        start_time = time.time()

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a helpful air quality health advisor. Always respond with valid JSON only, no additional text.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=self.temperature,
                max_tokens=500,
            )

            latency = time.time() - start_time
            raw_response = response.choices[0].message.content.strip()

            print(f"Latency: {latency:.2f}s")
            print(f"Raw response:\n{raw_response[:200]}...")

            # Parse the JSON response
            parsed_response = self._parse_json_response(raw_response)

            return {
                "summary": parsed_response.get("summary", ""),
                "precautions": parsed_response.get("precautions", []),
                "metadata": {
                    "model": self.model,
                    "strategy": strategy.value,
                    "aqi_value": aqi_value,
                    "aqi_category": aqi_category,
                    "latency_seconds": round(latency, 3),
                    "tokens_used": response.usage.total_tokens
                    if response.usage
                    else None,
                },
            }
        except json.JSONDecodeError as e:
            print(f"JSON parsing error: {e}")
            return {
                "summary": "",
                "precautions": [],
                "error": f"Failed to parse JSON: {str(e)}",
                "raw_response": raw_response if "raw_response" in locals() else None,
                "metadata": {
                    "model": self.model,
                    "strategy": strategy.value,
                    "aqi_value": aqi_value,
                    "aqi_category": aqi_category,
                    "latency_seconds": round(time.time() - start_time, 3),
                },
            }
        except Exception as e:
            print(f"API error: {e}")
            return {
                "summary": "",
                "precautions": [],
                "error": str(e),
                "metadata": {
                    "model": self.model,
                    "strategy": strategy.value,
                    "aqi_value": aqi_value,
                    "aqi_category": aqi_category,
                    "latency_seconds": round(time.time() - start_time, 3),
                },
            }

    def generate_advisory_all_strategies(
        self, aqi_value: float, aqi_category: Optional[str] = None
    ) -> Dict:
        """
        Generate advisories using all available strategies.

        Useful for comparison and evaluation.
        """
        results = {}
        for strategy in PromptStrategy:
            results[strategy.value] = self.generate_advisory(aqi_value, strategy)
        return results


if __name__ == "__main__":
    # testing zero shot
    # strategy = PromptStrategy.ZERO_SHOT
    aqi_advisor = AQIAdvisor("llama-3.3-70b-versatile", 0.3)
    # print(aqi_advisor.generate_advisory(95,strategy))

    # all strategies output:
    results = aqi_advisor.generate_advisory_all_strategies(95)

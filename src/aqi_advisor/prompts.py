"""
Prompt Loading and Management Module

This module handles:
1. Loading prompt templates from files
2. Formatting prompts with AQI data
3. Managing different prompting strategies
"""

from enum import Enum
from pathlib import Path
from typing import Optional


class PromptStrategy(Enum):
    """
    Enumeration of available prompting strategies.
    
    For now, we only have ZERO_SHOT. We'll add more later:
    - FEW_SHOT_K3
    - FEW_SHOT_K5
    - CHAIN_OF_THOUGHT
    - META_PROMPT
    """
    ZERO_SHOT = "zero_shot"
    FEW_SHOT_K3 = "few_shot_k3"
    FEW_SHOT_K5 = "few_shot_k5"
    CHAIN_OF_THOUGHT = "chain_of_thought"
    META_PROMPT = "meta_prompt"


def get_aqi_category(aqi: float) -> str:
    """
    Get AQI category based on standard EPA AQI ranges.
    
    Args:
        aqi: Air Quality Index value (0-500+)
        
    Returns:
        Category string (Good, Moderate, Unhealthy for Sensitive Groups, etc.)
    
    Reference: https://www.airnow.gov/aqi/aqi-basics/
    """
    if aqi <= 50:
        return "Good"
    elif aqi <= 100:
        return "Moderate"
    elif aqi <= 150:
        return "Unhealthy for Sensitive Groups"
    elif aqi <= 200:
        return "Unhealthy"
    elif aqi <= 300:
        return "Very Unhealthy"
    else:
        return "Hazardous"


class PromptLoader:
    """
    Loads and formats prompt templates from files.
    
    Templates are stored as .txt files with {placeholder} variables
    that get replaced with actual values at runtime.
    """
    
    def __init__(self, templates_dir: Optional[Path] = None):
        """
        Initialize the prompt loader.
        
        Args:
            templates_dir: Path to directory containing prompt templates.
                          Defaults to experiments/prompts/prompt_templates/
        """
        if templates_dir is None:
            # Navigate from src/aqi_advisor/ to experiments/prompts/prompt_templates/
            self.templates_dir = (
                Path(__file__).parent.parent.parent 
                / "experiments" / "prompts" / "prompt_templates"
            )
        else:
            self.templates_dir = Path(templates_dir)
        
        print(f"Prompt templates directory: {self.templates_dir}")
    
    def load_template(self, strategy: PromptStrategy) -> str:
        """
        Load a prompt template file.
        
        Args:
            strategy: The prompting strategy to load
            
        Returns:
            Raw template string with {placeholders}
            
        Raises:
            FileNotFoundError: If template file doesn't exist
        """
        template_file = self.templates_dir / f"{strategy.value}.txt"
        
        if not template_file.exists():
            raise FileNotFoundError(
                f"Template not found: {template_file}\n"
                f"Please create the file first."
            )
        
        template = template_file.read_text(encoding="utf-8")
        print(f"Loaded template: {strategy.value}")
        return template
    
    def format_prompt(
        self, 
        strategy: PromptStrategy, 
        aqi_value: float, 
        aqi_category: Optional[str] = None
    ) -> str:
        """
        Load and format a prompt with AQI data.
        
        Args:
            strategy: The prompting strategy to use
            aqi_value: The AQI value (0-500+)
            aqi_category: Optional category (auto-calculated if not provided)
            
        Returns:
            Formatted prompt string ready to send to LLM
        """
        # Auto-calculate category if not provided
        if aqi_category is None:
            aqi_category = get_aqi_category(aqi_value)
        
        # Load the template
        template = self.load_template(strategy)
        
        # Replace placeholders with actual values
        formatted = template.format(
            aqi_value=aqi_value,
            aqi_category=aqi_category
        )
        
        return formatted


# Quick test function
def test_prompt_loading():
    """Test that prompt loading works correctly."""
    loader = PromptLoader()
    
    try:
        # Test with AQI = 150
        prompt = loader.format_prompt(
            strategy=PromptStrategy.ZERO_SHOT,
            aqi_value=150,
            aqi_category="Unhealthy for Sensitive Groups"
        )
        print("\n" + "=" * 50)
        print("FORMATTED PROMPT:")
        print("=" * 50)
        print(prompt)
        print("=" * 50)
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False


if __name__ == "__main__":
    test_prompt_loading()
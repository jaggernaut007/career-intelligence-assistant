"""
LLM Judge for evaluating AI agents.
"""

import logging
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from app.services.llm_service import LLMService

logger = logging.getLogger(__name__)

class EvaluationResult(BaseModel):
    """Result of an LLM evaluation."""
    score: float = Field(..., description="Score from 0.0 to 10.0")
    is_passing: bool = Field(..., description="Whether the output met the passing criteria")
    reasoning: str = Field(..., description="Explanation for the score and pass/fail decision")
    suggestions: Optional[List[str]] = Field(default=None, description="Suggestions for improvement if any")

class LLMJudge:
    """
    Evaluates agent outputs against defined criteria using an LLM.
    """

    def __init__(self, llm_service: Optional[LLMService] = None):
        self.llm_service = llm_service or LLMService()

    async def evaluate(
        self,
        agent_name: str,
        input_data: Any,
        actual_output: Any,
        criteria: Any,  # Allow List or Str
        context: Optional[str] = None
    ) -> EvaluationResult:
        """
        Evaluate an agent's output against criteria.

        Args:
            agent_name: Name of the agent being tested
            input_data: The input provided to the agent
            actual_output: The output produced by the agent
            criteria: The acceptance criteria (string or list of strings)
            context: Additional context for the evaluator (optional)

        Returns:
            EvaluationResult containing score, pass/fail status, and reasoning
        """
        
        # Format criteria
        if isinstance(criteria, list):
            formatted_criteria = "\n".join(criteria)
        else:
            formatted_criteria = str(criteria)

        system_prompt = (
            "You are an expert AI Quality Assurance Judge. "
            "Your job is to evaluate the outputs of other AI agents based on specific criteria.\n"
            "You must be objective and fair in your evaluation. Focus on substance over exact string matching unless specified."
        )

        user_prompt = f"""
### Evaluation Task
Evaluate the performance of the '{agent_name}' agent.

### Context
{context if context else "No additional context provided."}

### Input Data
```json
{str(input_data)}
```

### Agent Output
```json
{str(actual_output)}
```

### Evaluation Criteria
{formatted_criteria}

### Instructions
1. Analyze if the Agent Output satisfies the Evaluation Criteria given the Input Data.
2. Provide a score from 0.0 to 10.0 (10 being perfect).
3. determine if it passes (true/false).
4. Explain your reasoning.

Respond with the following JSON structure:
{{
    "score": <float>,
    "is_passing": <bool>,
    "reasoning": "<string>",
    "suggestions": ["<string>", ...]
}}
"""
        try:
            result_dict = await self.llm_service.complete_json(
                prompt=user_prompt,
                system_prompt=system_prompt,
                temperature=0.0  # Deterministic for evaluation
            )
            return EvaluationResult(**result_dict)
        except Exception as e:
            logger.error(f"Error during LLM evaluation: {e}")
            # Fallback for error case
            return EvaluationResult(
                score=0.0,
                is_passing=False,
                reasoning=f"Evaluation failed due to internal error: {str(e)}"
            )

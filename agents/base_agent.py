"""
Base agent class for all fiction generation agents.
Provides common functionality for LLM invocation, lore querying, and structured output.
"""

from abc import ABC, abstractmethod
from typing import Optional
import hashlib
import json
from models.schema import FictionProject


class BaseAgent(ABC):
    """Abstract base class for all agents in the pipeline"""

    def __init__(self, llm, lore_store=None, temperature: float = 0.3, seed: Optional[int] = None):
        """
        Initialize base agent

        Args:
            llm: LangChain LLM instance
            lore_store: Optional LoreVectorStore for lore queries
            temperature: LLM temperature (0.0-1.0)
            seed: Optional seed for reproducibility
        """
        self.llm = llm
        self.lore_store = lore_store
        self.temperature = temperature
        self.seed = seed
        self.agent_name = self.__class__.__name__
        self.prompt_version = "1.0"

    @abstractmethod
    def get_prompt(self) -> str:
        """Return the versioned prompt for this agent"""
        pass

    @abstractmethod
    def process(self, input_data: FictionProject) -> FictionProject:
        """Process input and return updated project"""
        pass

    def get_prompt_hash(self) -> str:
        """Generate hash of current prompt for versioning"""
        prompt = self.get_prompt()
        return hashlib.sha256(prompt.encode()).hexdigest()[:8]

    def invoke_llm(self, prompt: str, context: str, max_tokens: int = None) -> str:
        """
        Wrapper for LLM calls with standardized parameters

        Args:
            prompt: System prompt/instructions
            context: Context data for the agent
            max_tokens: Maximum tokens to generate (default: use model config)

        Returns:
            LLM response content
        """
        full_prompt = f"{prompt}\n\nContext:\n{context}\n\nOutput (JSON only):"

        # Build kwargs for LLM
        llm_kwargs = {"temperature": self.temperature}
        if self.seed is not None:
            llm_kwargs["seed"] = self.seed

        # Use max_tokens from parameter or model's configured value
        if max_tokens:
            llm_kwargs["max_tokens"] = max_tokens
        elif hasattr(self.llm, 'max_tokens') and self.llm.max_tokens:
            llm_kwargs["max_tokens"] = self.llm.max_tokens

        # Invoke LLM with retry logic for API errors
        max_api_retries = 3
        last_error = None

        for attempt in range(max_api_retries):
            try:
                response = self.llm.invoke(full_prompt, **llm_kwargs)

                # Handle different response types
                if hasattr(response, 'content'):
                    return response.content
                else:
                    return str(response)

            except Exception as e:
                last_error = e
                error_msg = str(e).lower()

                # Check if it's a JSON parsing error from the API response
                if 'jsondecodeerror' in error_msg or 'expecting value' in error_msg:
                    if attempt < max_api_retries - 1:
                        print(f"    [API returned malformed JSON, retrying... ({attempt + 1}/{max_api_retries})]")
                        import time
                        time.sleep(2 ** attempt)  # Exponential backoff: 1s, 2s, 4s
                        continue
                    else:
                        raise ValueError(f"OpenRouter API returned malformed JSON after {max_api_retries} attempts. This is an API issue, not a prompt issue. Try again in a moment.")
                else:
                    # Different error, don't retry
                    raise

    def get_relevant_lore(self, context: str, project_id: str, top_k: int = 10) -> str:
        """
        Query Pinecone for relevant lore given context

        Args:
            context: Context string to match against lore
            project_id: Project identifier
            top_k: Number of lore entries to retrieve

        Returns:
            Formatted lore string for prompt injection
        """
        if not self.lore_store:
            return ""

        try:
            lore_entries = self.lore_store.query_lore(
                query=context,
                project_id=project_id,
                top_k=top_k
            )

            # Format lore for prompt
            lore_text = "### ESTABLISHED LORE:\n\n"
            for entry in lore_entries:
                lore_text += f"**{entry['lore_type'].title()}: {entry['name']}**\n"
                lore_text += f"{json.dumps(entry['content'], indent=2)}\n\n"

            return lore_text
        except Exception as e:
            print(f"Warning: Lore query failed: {e}")
            return ""

    def invoke_llm_with_lore(self, prompt: str, context: str, project_id: str) -> str:
        """
        Wrapper for LLM calls with lore context injection

        Args:
            prompt: System prompt/instructions
            context: Context data for the agent
            project_id: Project identifier for lore queries

        Returns:
            LLM response content
        """
        # Get relevant lore
        lore_context = self.get_relevant_lore(context, project_id)

        # Build full prompt with lore
        full_prompt = f"""{prompt}

{lore_context}

Context:
{context}

Output (JSON only):"""

        # Build kwargs for LLM
        llm_kwargs = {"temperature": self.temperature}
        if self.seed is not None:
            llm_kwargs["seed"] = self.seed

        # Invoke LLM with retry logic for API errors
        max_api_retries = 3
        last_error = None

        for attempt in range(max_api_retries):
            try:
                response = self.llm.invoke(full_prompt, **llm_kwargs)

                # Handle different response types
                if hasattr(response, 'content'):
                    return response.content
                else:
                    return str(response)

            except Exception as e:
                last_error = e
                error_msg = str(e).lower()

                # Check if it's a JSON parsing error from the API response
                if 'jsondecodeerror' in error_msg or 'expecting value' in error_msg:
                    if attempt < max_api_retries - 1:
                        print(f"    [API returned malformed JSON, retrying... ({attempt + 1}/{max_api_retries})]")
                        import time
                        time.sleep(2 ** attempt)  # Exponential backoff: 1s, 2s, 4s
                        continue
                    else:
                        raise ValueError(f"OpenRouter API returned malformed JSON after {max_api_retries} attempts. This is an API issue, not a prompt issue. Try again in a moment.")
                else:
                    # Different error, don't retry
                    raise

"""LLM intake engine adapter - AI-powered email analysis."""

import json
import logging
from typing import Any

from anthropic import AsyncAnthropic
from openai import AsyncOpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.domain.models.intake_result import AIIntakeResult, Recommendations
from app.core.domain.models.normalized_email import NormalizedEmail
from app.core.domain.value_objects.ai_result import Confidence, ExtractedEntity, Intent, Summary
from app.core.domain.value_objects.recommendation import DealRecommendation, TaskRecommendation
from app.core.ports.services.ai_intake_port import AIIntakePort
from app.settings import get_settings

logger = logging.getLogger(__name__)


class LLMIntakeEngine(AIIntakePort):
    """
    AI-powered email analysis using LLM (OpenAI or Anthropic).

    Generates:
    - Email summary with key points
    - Intent classification
    - Extracted entities (dates, people, organizations)
    - Task recommendations
    - Deal recommendations
    - Confidence score
    """

    def __init__(self):
        """Initialize LLM client based on settings."""
        settings = get_settings()
        self.provider = settings.ai_provider
        self.model = settings.ai_model

        if self.provider == "openai":
            self.client = AsyncOpenAI(api_key=settings.openai_api_key)
        elif self.provider == "anthropic":
            self.client = AsyncAnthropic(api_key=settings.anthropic_api_key)
        else:
            raise ValueError(f"Unsupported AI provider: {self.provider}")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
    )
    async def analyze(
        self,
        email: NormalizedEmail,
        context: dict,
    ) -> AIIntakeResult:
        """
        Use LLM to analyze email and generate recommendations.

        Args:
            email: Normalized email domain entity
            context: CRM context (contact info, recent interactions, etc.)

        Returns:
            AIIntakeResult with summary, intent, entities, and recommendations

        Raises:
            ValueError: If email analysis fails
            RuntimeError: If LLM service is unavailable
        """
        # Build prompt with email and context
        prompt = self._build_prompt(email, context)

        # Call LLM with structured output
        try:
            if self.provider == "openai":
                response = await self._call_openai(prompt)
            else:  # anthropic
                response = await self._call_anthropic(prompt)
        except Exception as e:
            logger.error(f"LLM call failed: {e}")
            raise RuntimeError(f"LLM service unavailable: {e}")

        # Parse response into domain entities
        return self._parse_response(response, email)

    def _build_prompt(self, email: NormalizedEmail, context: dict) -> str:
        """Build analysis prompt with email content and CRM context."""
        sender = email.from_address.email
        subject = email.headers.subject
        body = email.body.normalized_text

        # Build context section
        context_str = ""
        if context.get("is_existing_contact"):
            contact = context["contact"]
            context_str += f"\n**Existing Contact:**\n"
            context_str += f"- Name: {contact.get('name')}\n"
            context_str += f"- Company: {contact.get('company', 'Unknown')}\n"

            interactions = context.get("recent_interactions", [])
            if interactions:
                context_str += f"\n**Recent Interactions:** ({len(interactions)} total)\n"
                for interaction in interactions[:3]:  # Show top 3
                    context_str += f"- {interaction.get('type')}: {interaction.get('title', 'N/A')} ({interaction.get('status')})\n"
        else:
            context_str += "\n**New Contact:** No previous history in CRM.\n"

        # Build the prompt
        prompt = f"""Analyze this customer email and provide structured output.

**Email:**
From: {sender}
Subject: {subject}

Body:
{body}

**CRM Context:**{context_str}

**Analysis Required:**

1. **Summary**: Provide a concise 1-2 sentence summary of the email.

2. **Key Points**: List 2-4 key points or requests (bullet points).

3. **Intent**: Classify the primary intent as one of:
   - inquiry (asking for information)
   - complaint (expressing dissatisfaction)
   - request (requesting action/service)
   - follow_up (following up on previous communication)
   - other

4. **Entities**: Extract important entities:
   - PERSON (names of people mentioned)
   - DATE (specific dates or time references)
   - MONEY (dollar amounts)
   - ORGANIZATION (company names)
   For each entity, provide: type, value, confidence (0.0-1.0)

5. **Task Recommendations**: Suggest 0-3 tasks that should be created:
   - title (brief, actionable)
   - description (what needs to be done and why)
   - priority (low/medium/high)
   - due_date (ISO format like "2025-12-20", or null)

6. **Deal Recommendations**: Suggest 0-1 deals/opportunities:
   - contact_email (use sender's email)
   - deal_stage (qualification/proposal/negotiation)
   - value (estimated dollar amount)
   - notes (why this is an opportunity)

7. **Confidence**: Provide overall confidence score (0.0-1.0) and reasoning.
   - Above 0.85: very clear, actionable email
   - 0.70-0.84: clear intent, minor ambiguity
   - Below 0.70: unclear or complex, needs human review

**Output Format (JSON):**
{{
  "summary": "...",
  "key_points": ["point1", "point2"],
  "intent": "inquiry|complaint|request|follow_up|other",
  "entities": [
    {{"type": "PERSON", "value": "John Doe", "confidence": 0.9}}
  ],
  "task_recommendations": [
    {{
      "title": "...",
      "description": "...",
      "priority": "high",
      "due_date": "2025-12-20"
    }}
  ],
  "deal_recommendations": [
    {{
      "contact_email": "{sender}",
      "deal_stage": "qualification",
      "value": 5000.0,
      "notes": "..."
    }}
  ],
  "confidence": {{
    "overall_score": 0.85,
    "reasoning": "..."
  }}
}}

Respond with ONLY valid JSON, no additional text.
"""
        return prompt

    async def _call_openai(self, prompt: str) -> dict[str, Any]:
        """Call OpenAI API with structured output."""
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": "You are an AI assistant that analyzes customer emails for a CRM system. Always respond with valid JSON only.",
                },
                {"role": "user", "content": prompt},
            ],
            response_format={"type": "json_object"},
            temperature=0.3,  # Lower temperature for more consistent output
        )

        content = response.choices[0].message.content
        return json.loads(content)

    async def _call_anthropic(self, prompt: str) -> dict[str, Any]:
        """Call Anthropic API with structured output."""
        response = await self.client.messages.create(
            model=self.model,
            max_tokens=2048,
            messages=[
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
        )

        # Extract JSON from response
        content = response.content[0].text

        # Try to extract JSON (Claude might add explanation text)
        try:
            # Look for JSON object in the response
            start = content.find("{")
            end = content.rfind("}") + 1
            if start != -1 and end > start:
                json_str = content[start:end]
                return json.loads(json_str)
            else:
                return json.loads(content)
        except json.JSONDecodeError:
            logger.error(f"Failed to parse Anthropic response as JSON: {content}")
            raise ValueError("LLM did not return valid JSON")

    def _parse_response(self, response: dict[str, Any], email: NormalizedEmail) -> AIIntakeResult:
        """Parse LLM JSON response into domain entities."""
        # Parse summary
        summary = Summary(
            text=response.get("summary", "No summary provided"),
            key_points=response.get("key_points", []),
        )

        # Parse intent
        intent_str = response.get("intent", "other").lower()
        try:
            intent = Intent(intent_str)
        except ValueError:
            intent = Intent.OTHER

        # Parse entities
        entities = []
        for entity_data in response.get("entities", []):
            try:
                entity = ExtractedEntity(
                    entity_type=entity_data.get("type", "UNKNOWN"),
                    value=entity_data.get("value", ""),
                    confidence=float(entity_data.get("confidence", 0.5)),
                )
                entities.append(entity)
            except (ValueError, TypeError):
                continue

        # Parse confidence
        confidence_data = response.get("confidence", {})
        confidence = Confidence(
            overall_score=float(confidence_data.get("overall_score", 0.5)),
            reasoning=confidence_data.get("reasoning", "No reasoning provided"),
        )

        # Parse task recommendations
        tasks = []
        for task_data in response.get("task_recommendations", []):
            try:
                task = TaskRecommendation(
                    title=task_data.get("title", ""),
                    description=task_data.get("description", ""),
                    priority=task_data.get("priority", "medium"),
                    due_date=task_data.get("due_date"),
                )
                tasks.append(task)
            except (ValueError, TypeError):
                continue

        # Parse deal recommendations
        deals = []
        for deal_data in response.get("deal_recommendations", []):
            try:
                deal = DealRecommendation(
                    contact_email=deal_data.get("contact_email", email.from_address.email),
                    deal_stage=deal_data.get("deal_stage", "qualification"),
                    value=float(deal_data.get("value", 0)),
                    notes=deal_data.get("notes", ""),
                )
                deals.append(deal)
            except (ValueError, TypeError):
                continue

        recommendations = Recommendations(tasks=tasks, deals=deals)

        # Build AIIntakeResult
        ai_result = AIIntakeResult(
            summary=summary,
            intent=intent,
            entities=entities,
            confidence=confidence,
        )

        # Attach recommendations (we'll store them separately in IntakeRecord)
        # For now, return AI result - use case will handle recommendations
        ai_result.recommendations = recommendations  # Add as attribute for use case

        return ai_result

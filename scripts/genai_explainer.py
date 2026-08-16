# ==============================================================================
# Script: scripts/genai_explainer.py
# Project: MedClaim-GenAI
# Description: Uses LangChain + an OpenAI chat model to generate a root-cause
#              analysis and a formal insurance appeal justification letter
#              for a flagged / denied Medicare claim.
#
# Setup:
#   export OPENAI_API_KEY="your-key-here"
#   pip install -r requirements.txt
# ==============================================================================

import os
import logging
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger("genai_explainer")

SYSTEM_PROMPT = """You are an expert Healthcare Revenue Cycle Management (RCM)
and Medical Billing Compliance Specialist.

Analyze the denied medical claim detail provided and produce a professional
output containing exactly two sections:

1. ROOT CAUSE ANALYSIS
   A clear, structured explanation of the most likely reason(s) for the
   denial, referencing the denial reason code and claim characteristics.

2. APPEAL JUSTIFICATION LETTER
   A formal, respectful, policy-appropriate letter addressed to the payer,
   requesting reconsideration, that a billing team could review and send
   with minimal editing.

Do not fabricate specific clinical facts not provided. Where information is
missing, note it explicitly as something the billing team should supply."""

USER_PROMPT = """Claim Parameters:
- Claim ID: {claim_id}
- Provider ID: {provider_id}
- Billed / Payment Amount: ${billed_amount}
- Denial Reason Code: {denial_code}"""


def generate_appeal_documentation(
    claim_id: str,
    denial_code: str,
    billed_amount: float,
    provider_id: str,
    model_name: str = "gpt-4o-mini",
    temperature: float = 0.3,
) -> str:
    """
    Generates a root-cause analysis and formal appeal letter for a single
    flagged claim using a LangChain LCEL pipeline.

    Requires the OPENAI_API_KEY environment variable to be set.
    """
    if not os.environ.get("OPENAI_API_KEY"):
        raise EnvironmentError(
            "OPENAI_API_KEY is not set. Run: export OPENAI_API_KEY='your-key-here'"
        )

    logger.info(f"Generating GenAI appeal documentation for Claim ID: {claim_id} ...")

    llm = ChatOpenAI(model=model_name, temperature=temperature)

    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT),
        ("user", USER_PROMPT),
    ])

    chain = prompt | llm | StrOutputParser()

    response = chain.invoke({
        "claim_id": claim_id,
        "provider_id": provider_id,
        "billed_amount": f"{billed_amount:,.2f}",
        "denial_code": denial_code,
    })

    return response


def generate_for_flagged_batch(flagged_df, limit: int = 5) -> list[dict]:
    """
    Convenience wrapper: runs generate_appeal_documentation() across the
    top N rows of a flagged-claims DataFrame (e.g. from clean_flagged_claims.csv),
    sorted by anomaly severity if available.
    """
    results = []
    subset = flagged_df.head(limit)
    for _, row in subset.iterrows():
        try:
            text = generate_appeal_documentation(
                claim_id=row.get("CLM_ID", "UNKNOWN"),
                denial_code=row.get("RISK_CATEGORY", "UNSPECIFIED"),
                billed_amount=float(row.get("CLM_PMT_AMT", 0) or 0),
                provider_id=row.get("PRVDR_NUM", "UNKNOWN"),
            )
            results.append({"claim_id": row.get("CLM_ID"), "documentation": text})
        except Exception as e:
            logger.error(f"Failed to generate documentation for {row.get('CLM_ID')}: {e}")
    return results


if __name__ == "__main__":
    # Example usage:
    # output = generate_appeal_documentation(
    #     claim_id="-10000930775141",
    #     denial_code="High Risk / Fraud Flag",
    #     billed_amount=379024.23,
    #     provider_id="33S394",
    # )
    # print(output)
    pass


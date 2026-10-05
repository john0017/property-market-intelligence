# ============================================================
# AI MARKET ANALYST
# ============================================================
#
# This module handles communication between our deterministic
# property-market analytics and the OpenAI API.
#
# IMPORTANT ARCHITECTURE PRINCIPLE
# --------------------------------
#
# The LLM does NOT calculate our underlying market metrics.
#
# Python calculates:
#
#   - House-price growth
#   - Rental growth
#   - Price/rent divergence
#   - Real house-price growth
#
# The LLM receives those validated values and performs:
#
#   - interpretation
#   - comparison
#   - risk identification
#   - opportunity identification
#   - explanation
#
# ============================================================


import os

import pandas as pd

from dotenv import load_dotenv
from openai import OpenAI


# ------------------------------------------------------------
# LOAD API KEY
# ------------------------------------------------------------

load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")


if not api_key:
    raise ValueError(
        "OPENAI_API_KEY was not found in the .env file."
    )


# ------------------------------------------------------------
# CREATE OPENAI CLIENT
# ------------------------------------------------------------

client = OpenAI(
    api_key=api_key
)


# ============================================================
# HELPER FUNCTION
# ============================================================

def clean_number(value):
    """
    Convert a Pandas/numpy number into a normal Python number.

    Missing values are converted to the string
    'Not available'.

    This makes the evidence package easier for both humans
    and the LLM to read.
    """

    if value is None or pd.isna(value):
        return "Not available"

    return round(float(value), 2)


# ============================================================
# BUILD MARKET EVIDENCE
# ============================================================

def build_market_evidence(
    primary_market,
    comparison_market,
    primary_row,
    comparison_row
):
    """
    Build the controlled evidence package supplied to the LLM.

    The model should analyse THIS information rather than
    inventing market statistics from its general knowledge.

    Parameters
    ----------
    primary_market : str
        Name of the selected primary market.

    comparison_market : str
        Name of the comparison market.

    primary_row : pandas.Series
        Latest validated observation for the primary market.

    comparison_row : pandas.Series
        Latest validated observation for comparison market.

    Returns
    -------
    str
        Human-readable evidence package.
    """


    primary_evidence = f"""
MARKET: {primary_market}
Quarter: {primary_row['quarter']}

SOURCE FACTS
House Price YoY Growth:
{clean_number(primary_row['house_price_yoy_pct'])}%

Rental YoY Growth:
{clean_number(primary_row['rent_yoy_pct'])}%

Inflation:
{clean_number(primary_row['inflation_pct'])}%

Unemployment:
{clean_number(primary_row['unemployment_pct'])}%

GDP Growth:
{clean_number(primary_row['gdp_growth_pct'])}%

Policy Rate:
{clean_number(primary_row['policy_rate_pct'])}%


CALCULATED INDICATORS

Price / Rent Divergence:
{clean_number(primary_row['price_rent_divergence_pp'])}
percentage points

Real House Price Growth:
{clean_number(primary_row['real_house_price_growth_pct'])}%
"""


    comparison_evidence = f"""
MARKET: {comparison_market}
Quarter: {comparison_row['quarter']}

SOURCE FACTS
House Price YoY Growth:
{clean_number(comparison_row['house_price_yoy_pct'])}%

Rental YoY Growth:
{clean_number(comparison_row['rent_yoy_pct'])}%

Inflation:
{clean_number(comparison_row['inflation_pct'])}%

Unemployment:
{clean_number(comparison_row['unemployment_pct'])}%

GDP Growth:
{clean_number(comparison_row['gdp_growth_pct'])}%

Policy Rate:
{clean_number(comparison_row['policy_rate_pct'])}%


CALCULATED INDICATORS

Price / Rent Divergence:
{clean_number(comparison_row['price_rent_divergence_pp'])}
percentage points

Real House Price Growth:
{clean_number(comparison_row['real_house_price_growth_pct'])}%
"""


    evidence = f"""
============================================================
VALIDATED MARKET EVIDENCE
============================================================

{primary_evidence}

------------------------------------------------------------

{comparison_evidence}

============================================================
END OF EVIDENCE
============================================================
"""


    return evidence


# ============================================================
# AI ANALYSIS
# ============================================================

def analyse_markets(
    question,
    primary_market,
    comparison_market,
    primary_row,
    comparison_row
):
    """
    Send validated market evidence plus the user's question
    to OpenAI.

    The model is instructed to treat the supplied evidence as
    authoritative for numerical claims.
    """


    # --------------------------------------------------------
    # BUILD EVIDENCE
    # --------------------------------------------------------

    evidence = build_market_evidence(
        primary_market,
        comparison_market,
        primary_row,
        comparison_row
    )


    # --------------------------------------------------------
    # SYSTEM / ANALYST INSTRUCTIONS
    # --------------------------------------------------------
    #
    # These instructions define how the model should behave.
    #
    # The important safeguards are:
    #
    #   - don't invent statistics
    #   - don't pretend missing evidence exists
    #   - distinguish evidence from interpretation
    #   - don't make unsupported forecasts
    # --------------------------------------------------------

    instructions = """
You are an international property-market research analyst.

You are analysing markets for an investment analyst who is
screening international property markets.

EVIDENCE RULES

Use the supplied VALIDATED MARKET EVIDENCE as the authoritative
source for numerical claims about the selected markets.

Do not invent statistics.

Do not replace supplied statistics with numbers from your
general knowledge.

If evidence required to answer the question is unavailable,
explicitly state that the available evidence is insufficient.

Do not produce unsupported property-price forecasts.

You may interpret relationships between the supplied
indicators, but clearly distinguish interpretation from
observed facts.

When discussing risks or opportunities, explain which
indicators support the conclusion.

A positive Price / Rent Divergence means house prices are
growing faster than rents.

A negative Price / Rent Divergence means rents are growing
faster than house prices.

Real House Price Growth is an analytical approximation
calculated as:

House Price YoY Growth - Inflation

It is not a formal inflation-adjusted property-price index.

Do not present the analysis as investment advice.

SOURCE HIERARCHY

Treat quantitative statistical data as the authority for numerical
market observations.

Use contextual documents only for policy, regulatory and structural
market interpretation.

Do not use contextual documents to override numerical observations.

When making an important contextual claim, identify the source in
plain language, for example:

"According to the Central Bank of Ireland..."
"Banco de España identifies..."
"Under Spain's Law 12/2023..."

Do not claim that a source supports a conclusion unless that
conclusion is present in or reasonably derived from the supplied
evidence.

RESPONSE STYLE

Be concise and analytical.

Prefer evidence-backed reasoning over generic property-market
commentary.

When appropriate, structure the answer using:

Summary
Evidence
Risks
Opportunities
What to investigate next

Do not force those headings when the user's question can be
answered more directly.
"""


    # --------------------------------------------------------
    # USER INPUT
    # --------------------------------------------------------
    #
    # The model receives BOTH:
    #
    #     evidence
    #     +
    #     user question
    #
    # This is the core grounding mechanism in Version 1.
    # --------------------------------------------------------

    user_input = f"""
{evidence}

USER QUESTION

{question}
"""


    # --------------------------------------------------------
    # CALL OPENAI RESPONSES API
    # --------------------------------------------------------

    response = client.responses.create(
        model="gpt-6-luna",
        instructions=instructions,
        input=user_input
    )


    # Return only the generated text to Streamlit.
    return response.output_text
# ============================================================
# INTERNATIONAL PROPERTY MARKET INTELLIGENCE
# ============================================================
#
# Streamlit prototype
#
# PURPOSE
# -------
# This application allows an analyst/investor to:
#
#   1. Select an international property market
#   2. Compare it with another market
#   3. Review key property and economic indicators
#   4. Explore historical trends
#   5. Understand calculated market indicators
#
# The numerical analysis is deterministic.
#
# In the next version we will add an OpenAI-powered
# "AI Market Analyst" that interprets this validated data.
#
# ============================================================


# ------------------------------------------------------------
# IMPORT LIBRARIES
# ------------------------------------------------------------

import pandas as pd
import streamlit as st
from pathlib import Path
from ai import analyse_markets

# ------------------------------------------------------------
# STREAMLIT PAGE CONFIGURATION
# ------------------------------------------------------------
#
# This must be the first Streamlit command in the script.
#
# layout="wide" gives us more horizontal space, which works
# better for dashboards.
# ------------------------------------------------------------

st.set_page_config(
    page_title="Property Market Intelligence",
    page_icon="🏠",
    layout="wide"
)


# ------------------------------------------------------------
# APPLICATION TITLE
# ------------------------------------------------------------

st.title("International Property Market Intelligence")

st.caption(
    "Compare property-market performance, economic conditions "
    "and investment signals across international markets."
)


# ============================================================
# LOAD DATA
# ============================================================


# ------------------------------------------------------------
# DEFINE FILE LOCATIONS
# ------------------------------------------------------------

DATA_FILE = Path("data/market_data.csv")
SOURCE_FILE = Path("data/data_sources.csv")


# ------------------------------------------------------------
# CHECK THAT DATA EXISTS
# ------------------------------------------------------------
#
# Rather than allowing the application to crash with a
# confusing Python error, show a useful message if the data
# files cannot be found.
# ------------------------------------------------------------

if not DATA_FILE.exists():

    st.error(
        "Market data file not found. "
        "Run the data preparation notebook first."
    )

    st.stop()


# ------------------------------------------------------------
# LOAD MARKET DATA
# ------------------------------------------------------------
#
# @st.cache_data tells Streamlit to cache the result.
#
# Streamlit reruns the Python script whenever the user changes
# a widget. Without caching, the CSV would be read repeatedly.
# ------------------------------------------------------------

@st.cache_data
def load_market_data():

    df = pd.read_csv(DATA_FILE)

    # Convert quarter strings such as "2025Q1"
    # back into Pandas quarterly periods.
    df["quarter"] = pd.PeriodIndex(
        df["quarter"],
        freq="Q"
    )

    # Ensure observations are in chronological order.
    df = df.sort_values(
        ["country", "quarter"]
    ).reset_index(drop=True)

    return df


market_data = load_market_data()


# ------------------------------------------------------------
# LOAD SOURCE METADATA
# ------------------------------------------------------------

@st.cache_data
def load_sources():

    if SOURCE_FILE.exists():
        return pd.read_csv(SOURCE_FILE)

    return pd.DataFrame()


data_sources = load_sources()


# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.header("Market Selection")


# ------------------------------------------------------------
# GET AVAILABLE COUNTRIES
# ------------------------------------------------------------

countries = sorted(
    market_data["country"]
    .dropna()
    .unique()
    .tolist()
)


# ------------------------------------------------------------
# PRIMARY MARKET
# ------------------------------------------------------------

primary_market = st.sidebar.selectbox(
    "Primary Market",
    countries,
    index=0
)


# ------------------------------------------------------------
# COMPARISON MARKET
# ------------------------------------------------------------
#
# Remove the primary market from the comparison list so the
# user cannot compare Ireland with Ireland, for example.
# ------------------------------------------------------------

comparison_options = [
    country
    for country in countries
    if country != primary_market
]


comparison_market = st.sidebar.selectbox(
    "Compare With",
    comparison_options,
    index=0
)


# ------------------------------------------------------------
# FILTER DATA
# ------------------------------------------------------------

primary_data = (
    market_data[
        market_data["country"] == primary_market
    ]
    .copy()
)


comparison_data = (
    market_data[
        market_data["country"] == comparison_market
    ]
    .copy()
)


# ============================================================
# FIND LATEST COMPLETE OBSERVATION
# ============================================================
#
# Different datasets can be released at different times.
#
# For the headline comparison we therefore find the latest
# quarter containing the important property indicators.
#
# This prevents us from accidentally presenting incomplete
# data as if it were complete.
# ============================================================


def get_latest_complete_row(df):

    required_columns = [
        "house_price_yoy_pct",
        "rent_yoy_pct",
        "inflation_pct",
        "unemployment_pct"
    ]

    available = df.dropna(
        subset=required_columns
    )

    if available.empty:
        return None

    return available.iloc[-1]


primary_latest = get_latest_complete_row(
    primary_data
)

comparison_latest = get_latest_complete_row(
    comparison_data
)


# ============================================================
# HELPER FUNCTIONS
# ============================================================


def format_percent(value):
    """
    Format numerical values as percentages.

    Example:
        4.237 -> "4.24%"
    """

    if pd.isna(value):
        return "N/A"

    return f"{value:.2f}%"


def format_pp(value):
    """
    Format percentage-point indicators.

    Example:
        3.12 -> "+3.12 pp"
    """

    if pd.isna(value):
        return "N/A"

    return f"{value:+.2f} pp"


def safe_value(row, column):
    """
    Safely retrieve a value from a row.

    This prevents errors if a column is unavailable
    or the row does not exist.
    """

    if row is None:
        return None

    if column not in row.index:
        return None

    return row[column]


# ============================================================
# MARKET HEADER
# ============================================================

st.divider()

st.subheader(
    f"{primary_market} vs {comparison_market}"
)


if primary_latest is not None:

    st.caption(
        f"Latest complete {primary_market} observation: "
        f"{primary_latest['quarter']}"
    )


# ============================================================
# KPI CARDS
# ============================================================
#
# These headline indicators provide a quick snapshot of the
# primary market.
#
# Later, the AI analyst will receive these same validated
# metrics as part of its evidence package.
# ============================================================

st.markdown("### Market Snapshot")


col1, col2, col3, col4 = st.columns(4)


with col1:

    st.metric(
        "House Price Growth",
        format_percent(
            safe_value(
                primary_latest,
                "house_price_yoy_pct"
            )
        )
    )


with col2:

    st.metric(
        "Rental Growth",
        format_percent(
            safe_value(
                primary_latest,
                "rent_yoy_pct"
            )
        )
    )


with col3:

    st.metric(
        "Inflation",
        format_percent(
            safe_value(
                primary_latest,
                "inflation_pct"
            )
        )
    )


with col4:

    st.metric(
        "Unemployment",
        format_percent(
            safe_value(
                primary_latest,
                "unemployment_pct"
            )
        )
    )


# ------------------------------------------------------------
# SECOND ROW OF KPIs
# ------------------------------------------------------------

col5, col6, col7, col8 = st.columns(4)


with col5:

    st.metric(
        "GDP Growth",
        format_percent(
            safe_value(
                primary_latest,
                "gdp_growth_pct"
            )
        )
    )


with col6:

    st.metric(
        "Policy Rate",
        format_percent(
            safe_value(
                primary_latest,
                "policy_rate_pct"
            )
        )
    )


with col7:

    st.metric(
        "Real House Price Growth",
        format_percent(
            safe_value(
                primary_latest,
                "real_house_price_growth_pct"
            )
        )
    )


with col8:

    st.metric(
        "Price / Rent Divergence",
        format_pp(
            safe_value(
                primary_latest,
                "price_rent_divergence_pp"
            )
        )
    )


# ============================================================
# MARKET COMPARISON TABLE
# ============================================================

st.divider()

st.markdown("### Market Comparison")


# ------------------------------------------------------------
# CREATE COMPARISON TABLE
# ------------------------------------------------------------
#
# We explicitly build the table from the latest validated
# observations rather than simply displaying the raw dataset.
# ------------------------------------------------------------

comparison_table = pd.DataFrame({

    "Indicator": [
        "House Price Growth",
        "Rental Growth",
        "Inflation",
        "Unemployment",
        "GDP Growth",
        "Policy Rate",
        "Real House Price Growth",
        "Price / Rent Divergence"
    ],

    primary_market: [
        format_percent(
            safe_value(
                primary_latest,
                "house_price_yoy_pct"
            )
        ),

        format_percent(
            safe_value(
                primary_latest,
                "rent_yoy_pct"
            )
        ),

        format_percent(
            safe_value(
                primary_latest,
                "inflation_pct"
            )
        ),

        format_percent(
            safe_value(
                primary_latest,
                "unemployment_pct"
            )
        ),

        format_percent(
            safe_value(
                primary_latest,
                "gdp_growth_pct"
            )
        ),

        format_percent(
            safe_value(
                primary_latest,
                "policy_rate_pct"
            )
        ),

        format_percent(
            safe_value(
                primary_latest,
                "real_house_price_growth_pct"
            )
        ),

        format_pp(
            safe_value(
                primary_latest,
                "price_rent_divergence_pp"
            )
        )
    ],

    comparison_market: [
        format_percent(
            safe_value(
                comparison_latest,
                "house_price_yoy_pct"
            )
        ),

        format_percent(
            safe_value(
                comparison_latest,
                "rent_yoy_pct"
            )
        ),

        format_percent(
            safe_value(
                comparison_latest,
                "inflation_pct"
            )
        ),

        format_percent(
            safe_value(
                comparison_latest,
                "unemployment_pct"
            )
        ),

        format_percent(
            safe_value(
                comparison_latest,
                "gdp_growth_pct"
            )
        ),

        format_percent(
            safe_value(
                comparison_latest,
                "policy_rate_pct"
            )
        ),

        format_percent(
            safe_value(
                comparison_latest,
                "real_house_price_growth_pct"
            )
        ),

        format_pp(
            safe_value(
                comparison_latest,
                "price_rent_divergence_pp"
            )
        )
    ]
})


st.dataframe(
    comparison_table,
    hide_index=True,
    use_container_width=True
)


# ============================================================
# HISTORICAL TRENDS
# ============================================================

st.divider()

st.markdown("### Market Trends")


# ------------------------------------------------------------
# COMBINE SELECTED MARKETS
# ------------------------------------------------------------

selected_markets = market_data[
    market_data["country"].isin(
        [
            primary_market,
            comparison_market
        ]
    )
].copy()


# Convert quarter into text for Streamlit chart labels.
selected_markets["quarter_label"] = (
    selected_markets["quarter"]
    .astype(str)
)


# ============================================================
# HOUSE PRICE GROWTH CHART
# ============================================================

st.markdown("#### Annual House Price Growth")


house_price_chart = selected_markets.pivot(
    index="quarter_label",
    columns="country",
    values="house_price_yoy_pct"
)


# Remove periods where both markets contain no data.
house_price_chart = (
    house_price_chart
    .dropna(how="all")
)


st.line_chart(
    house_price_chart,
    use_container_width=True
)


# ============================================================
# RENTAL GROWTH CHART
# ============================================================

st.markdown("#### Annual Rental Growth")


rent_chart = selected_markets.pivot(
    index="quarter_label",
    columns="country",
    values="rent_yoy_pct"
)


rent_chart = (
    rent_chart
    .dropna(how="all")
)


st.line_chart(
    rent_chart,
    use_container_width=True
)


# ============================================================
# PRICE / RENT DIVERGENCE
# ============================================================

st.markdown("#### Price / Rent Divergence")


divergence_chart = selected_markets.pivot(
    index="quarter_label",
    columns="country",
    values="price_rent_divergence_pp"
)


divergence_chart = (
    divergence_chart
    .dropna(how="all")
)


st.line_chart(
    divergence_chart,
    use_container_width=True
)


st.caption(
    "Positive divergence means house prices are growing "
    "faster than rents. Negative divergence means rents are "
    "growing faster than house prices."
)


# ============================================================
# MACROECONOMIC CONDITIONS
# ============================================================

st.divider()

st.markdown("### Economic Context")


macro_col1, macro_col2 = st.columns(2)


# ------------------------------------------------------------
# INFLATION
# ------------------------------------------------------------

with macro_col1:

    st.markdown("#### Inflation")

    inflation_chart = selected_markets.pivot(
        index="quarter_label",
        columns="country",
        values="inflation_pct"
    )

    inflation_chart = (
        inflation_chart
        .dropna(how="all")
    )

    st.line_chart(
        inflation_chart,
        use_container_width=True
    )


# ------------------------------------------------------------
# UNEMPLOYMENT
# ------------------------------------------------------------

with macro_col2:

    st.markdown("#### Unemployment")

    unemployment_chart = selected_markets.pivot(
        index="quarter_label",
        columns="country",
        values="unemployment_pct"
    )

    unemployment_chart = (
        unemployment_chart
        .dropna(how="all")
    )

    st.line_chart(
        unemployment_chart,
        use_container_width=True
    )


# ============================================================
# GDP
# ============================================================

st.markdown("#### GDP Growth")


gdp_chart = selected_markets.pivot(
    index="quarter_label",
    columns="country",
    values="gdp_growth_pct"
)


gdp_chart = (
    gdp_chart
    .dropna(how="all")
)


st.line_chart(
    gdp_chart,
    use_container_width=True
)


# ============================================================
# LATEST ANALYTICAL SIGNALS
# ============================================================
#
# These aren't AI conclusions.
#
# They are simple deterministic observations generated from
# the calculated metrics.
#
# This distinction becomes important once we add the LLM.
# ============================================================

st.divider()

st.markdown("### Analytical Signals")


if primary_latest is not None:

    divergence = safe_value(
        primary_latest,
        "price_rent_divergence_pp"
    )

    real_growth = safe_value(
        primary_latest,
        "real_house_price_growth_pct"
    )


    # --------------------------------------------------------
    # PRICE / RENT SIGNAL
    # --------------------------------------------------------

    if pd.notna(divergence):

        if divergence > 0:

            st.info(
                f"**Price/Rent:** House prices in "
                f"{primary_market} are growing "
                f"{abs(divergence):.2f} percentage points "
                f"faster than rents."
            )

        elif divergence < 0:

            st.info(
                f"**Price/Rent:** Rents in "
                f"{primary_market} are growing "
                f"{abs(divergence):.2f} percentage points "
                f"faster than house prices."
            )

        else:

            st.info(
                "**Price/Rent:** House-price and rental "
                "growth are currently aligned."
            )


    # --------------------------------------------------------
    # REAL HOUSE-PRICE SIGNAL
    # --------------------------------------------------------

    if pd.notna(real_growth):

        if real_growth > 0:

            st.info(
                f"**Real Price Growth:** House-price growth "
                f"is approximately {real_growth:.2f} "
                f"percentage points above inflation."
            )

        elif real_growth < 0:

            st.info(
                f"**Real Price Growth:** House-price growth "
                f"is approximately {abs(real_growth):.2f} "
                f"percentage points below inflation."
            )


# ============================================================
# AI MARKET ANALYST
# ============================================================
#
# The AI receives the same validated market information shown
# in the dashboard.
#
# It does NOT independently retrieve or calculate the
# underlying statistics.
#
# This creates a clear separation:
#
# DATA / CALCULATIONS
#         ↓
#       Python
#
# INTERPRETATION
#         ↓
#       OpenAI
#
# ============================================================


st.divider()

st.markdown("### AI Market Analyst")


st.caption(
    "Ask questions about the selected markets using the "
    "validated evidence shown in this dashboard."
)


# ------------------------------------------------------------
# SUGGESTED QUESTIONS
# ------------------------------------------------------------

st.markdown("**Try asking:**")

st.markdown(
    f"""
- Compare {primary_market} and {comparison_market}.
- What are the main risks in {primary_market}?
- What opportunities do you see in {comparison_market}?
- Where are rents growing faster than property prices?
- Which market currently shows stronger property momentum?
- What additional information should an investor investigate?
"""
)


# ------------------------------------------------------------
# USER QUESTION
# ------------------------------------------------------------

question = st.text_area(
    "Question",
    placeholder=(
        f"What are the main risks when comparing "
        f"{primary_market} with {comparison_market}?"
    ),
    height=100
)


# ------------------------------------------------------------
# ANALYSE BUTTON
# ------------------------------------------------------------

analyse_button = st.button(
    "Analyse Markets",
    type="primary"
)


# ------------------------------------------------------------
# RUN AI ANALYSIS
# ------------------------------------------------------------

if analyse_button:

    # Make sure the user actually entered a question.
    if not question.strip():

        st.warning(
            "Enter a question before running the analysis."
        )


    # Make sure we have validated market observations.
    elif (
        primary_latest is None
        or comparison_latest is None
    ):

        st.error(
            "There is insufficient market data to perform "
            "this comparison."
        )


    else:

        # Show a loading indicator while waiting for OpenAI.
        with st.spinner(
            "Analysing market evidence..."
        ):

            try:

                analysis = analyse_markets(
                    question=question,
                    primary_market=primary_market,
                    comparison_market=comparison_market,
                    primary_row=primary_latest,
                    comparison_row=comparison_latest
                )


                # Display the model response.
                st.markdown("#### Analysis")

                st.markdown(
                    analysis
                )


            except Exception as error:

                # During development we show the error so
                # problems such as API authentication or
                # billing can be diagnosed quickly.

                st.error(
                    "The AI analysis could not be completed."
                )

                st.exception(
                    error
                )


# ============================================================
# DATA SOURCES
# ============================================================

st.divider()


with st.expander(
    "Data Sources & Methodology"
):

    st.markdown(
        """
        **Data architecture**

        The application separates three types of information:

        **Source Facts** — observations obtained from official
        statistical sources.

        **Calculated Indicators** — metrics calculated
        deterministically in Python.

        **AI Interpretation** — natural-language analysis
        generated from the validated evidence layer.

        This separation reduces reliance on the language model
        for factual or numerical calculations.
        """
    )


    if not data_sources.empty:

        st.markdown("#### Sources")

        st.dataframe(
            data_sources,
            hide_index=True,
            use_container_width=True
        )


    st.markdown(
        """
        #### Calculated Indicators

        **Price / Rent Divergence**

        House Price YoY Growth − Rent YoY Growth

        **Real House Price Growth**

        House Price YoY Growth − Inflation

        These metrics are screening indicators rather than
        investment recommendations.
        """
    )


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "Prototype for international property-market screening. "
    "Not investment advice."
)
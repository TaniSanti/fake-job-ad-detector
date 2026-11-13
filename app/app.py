import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

import streamlit as st
from src.predict import predict_job, get_indicators
from src.duplicate_detector import calculate_similarity


# ==================================================
# Page Configuration
# ==================================================

st.set_page_config(
    page_title="Fake Job Advertisement Detector",
    page_icon="🔎",
    layout="centered"
)


# ==================================================
# Header
# ==================================================

st.title("🔎 Fake Job Advertisement Detector")

st.write(
    "Paste a job advertisement below to assess whether "
    "it is likely legitimate or potentially fraudulent."
)

st.info(
    "This tool provides a machine-learning-based assessment. "
    "It should be used as a screening aid, not as definitive "
    "proof of fraud."
)


# ==================================================
# Analyse One Job Advertisement
# ==================================================

st.subheader("Job Advertisement")

SCAMWATCH_EXAMPLE_ADS = [
    {
        "title": "Example 1 — Remote product-rating assistant",
        "signs": "High income for little effort, no interview, product-rating tasks, and an early BSB request.",
        "text": (
            "Remote Product Rating Assistant\\n"
            "We are hiring a fully remote product rating assistant. Earn a high "
            "income for little effort, working from home for a few hours each day. "
            "No experience required. The hiring process is quick and no interview "
            "is required. Your tasks will include rating products. Provide your "
            "BSB and account number to proceed with recruitment."
        ),
    },
    {
        "title": "Example 2 — Online product-task assistant",
        "signs": "High pay for easy tasks, cryptocurrency top-ups, and banking details requested before employment.",
        "text": (
            "Online Product Task Assistant\\n"
            "Complete simple tasks from home and earn high pay for a few hours "
            "each day. Your work includes rating products. Before you begin, top "
            "up your cryptocurrency account to unlock tasks and receive your "
            "commission. Provide your banking information before employment."
        ),
    },
    {
        "title": "Example 3 — Remote payment-processing assistant",
        "signs": "No interview, transfers through a personal bank account, and an early personal-bank-details request.",
        "text": (
            "Remote Payment Processing Assistant\\n"
            "No interview required. Receive money into your personal bank account, "
            "then transfer money to other accounts for our clients. We will provide "
            "a commission for each transfer. Send your personal bank details before "
            "an interview to continue recruitment."
        ),
    },
    {
        "title": "Example 4 — Urgent remote assistant",
        "signs": "Limited positions, immediate action, guaranteed income for little work, and bank details requested to proceed.",
        "text": (
            "Urgent Remote Assistant — Only 20 positions available. Apply "
            "immediately. We guarantee high income for little work. This is a "
            "fully remote role and no experience is required. The hiring process "
            "is quick and no interview is required. Send us your bank account "
            "details to proceed with recruitment."
        ),
    },
]

with st.expander(
    "Copyable sample advertisements using Scamwatch warning signs",
    expanded=True,
):
    st.caption(
        "Copy an example into the analysis box, then click Analyse. "
        "These fictional samples demonstrate warning indicators; they are "
        "not proof that a real job is fraudulent."
    )

    for example in SCAMWATCH_EXAMPLE_ADS:
        st.markdown(f"**{example['title']}**")
        st.caption(example["signs"])
        st.code(example["text"], language=None)

job_text = st.text_area(
    "Paste the complete job advertisement below:",
    height=300,
    placeholder="Paste a sample above or paste a real advertisement here...",
    key="job_ad_text",
)

# ==================================================
# Prediction
# ==================================================

if st.button(
    "Analyse Job Advertisement",
    type="primary"
):

    if not job_text.strip():

        st.warning(
            "Please enter a job advertisement first."
        )

    else:

        # ------------------------------------------
        # Run ML prediction and risk detection
        # ------------------------------------------

        result = predict_job(job_text)


        # ------------------------------------------
        # Assessment Result
        # ------------------------------------------

        st.subheader("Assessment Result")

        if result["prediction"] == 1:

            st.error(
                "⚠️ Potentially Fraudulent"
            )

        else:

            st.success(
                "✅ Likely Legitimate"
            )


        # ------------------------------------------
        # Fraud Probability
        # ------------------------------------------

        probability = result["fraud_probability"]

        st.metric(
            "Estimated Fraud Probability",
            f"{probability:.1%}"
        )

        st.progress(probability)

        st.caption(
            "0% = very low estimated fraud probability | "
            "100% = very high estimated fraud probability"
        )

        st.caption(
            "The probability represents the model's estimated "
            "likelihood that the advertisement belongs to the "
            "fraudulent class."
        )




        # ------------------------------------------
        # Additional Risk Indicators
        # ------------------------------------------

        risk_indicators = result.get(
            "risk_indicators",
            []
        )

        if risk_indicators:

            st.subheader(
                "Additional Risk Indicators"
            )

            st.write(
                "The following patterns may require "
                "additional review."
            )

            st.write(
                "They are not definitive evidence of fraud."
            )

            for item in risk_indicators:

                category = item["category"].replace(
                    "_",
                    " "
                ).title()

                phrase = item["phrase"]

                st.warning(
                    f"**{category}** — {phrase}"
                )

        else:

            st.success(
                "No additional rule-based risk indicators "
                "were identified."
            )

        st.caption(
            "Risk indicators are based on predefined patterns "
            "and should not be interpreted as definitive "
            "evidence of fraud."
        )


# ==================================================
# Compare Two Job Advertisements
# ==================================================

st.divider()

st.subheader(
    " Compare Two Job Advertisements"
)

st.write(
    "Compare two job advertisements to identify potentially "
    "reused or duplicated job-ad content."
)


# ------------------------------------------
# Job A
# ------------------------------------------

job_a_compare = st.text_area(
    "Job Advertisement A",
    height=250,
    placeholder=(
        "Paste the first job advertisement here..."
    ),
    key="job_a_compare"
)


# ------------------------------------------
# Job B
# ------------------------------------------

job_b_compare = st.text_area(
    "Job Advertisement B",
    height=250,
    placeholder=(
        "Paste the second job advertisement here..."
    ),
    key="job_b_compare"
)


# ------------------------------------------
# Compare Button
# ------------------------------------------

if st.button(
    "Compare Job Advertisements",
    type="secondary"
):

    if (
        not job_a_compare.strip()
        or not job_b_compare.strip()
    ):

        st.warning(
            "Please enter both job advertisements "
            "before comparing."
        )

    else:

        # Calculate textual similarity
        similarity = calculate_similarity(
            job_a_compare,
            job_b_compare
        )


        # ------------------------------------------
        # Similarity Result
        # ------------------------------------------

        st.subheader(
            "Similarity Assessment"
        )

        st.metric(
            "Content Similarity",
            f"{similarity:.2%}"
        )

        st.progress(
            similarity
        )


        # ------------------------------------------
        # Interpretation
        # ------------------------------------------

        if similarity >= 0.90:

            st.error(
                "🔴 High Content Similarity"
            )

            st.write(
                "These advertisements contain substantial "
                "textual overlap and may represent reused "
                "or duplicated job-ad content."
            )

            st.write(
                "Consider verifying whether the employer, "
                "job title, and position details are genuine."
            )


        elif similarity >= 0.70:

            st.warning(
                "🟡 Moderate Content Similarity"
            )

            st.write(
                "Some substantial wording overlap was detected. "
                "The advertisements may share a template or "
                "similar structure."
            )


        else:

            st.success(
                "🟢 Low Content Similarity"
            )

            st.write(
                "No strong evidence of duplicated wording "
                "was detected between these advertisements."
            )


        # ------------------------------------------
        # Disclaimer
        # ------------------------------------------

        st.caption(
            "Similarity is based on textual patterns and "
            "should not be interpreted as definitive "
            "evidence of fraud."
        )


# ==================================================
# Footer
# ==================================================

st.divider()

st.caption(
    "Fake Job Advertisement Detector | "
    "Machine Learning + Rule-Based Risk Analysis + "
    "Text Similarity Detection"
)
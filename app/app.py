import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

import streamlit as st
from src.predict import predict_job, get_indicators
from src.duplicate_detector import calculate_similarity
from src.abn_lookup import (
    ABNLookupError,
    extract_abn,
    is_valid_abn,
    lookup_by_abn,
    verify_business,
)


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

job_text = st.text_area(
    "Paste the complete job advertisement below:",
    height=300,
    placeholder="Paste the complete job advertisement here..."
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
# Business ABN Verification
# ==================================================

st.divider()
st.subheader("Business ABN Verification")
st.write(
    "Check the Australian Business Register for a business mentioned "
    "in the advertisement. You can search by ABN, business name, or both."
)

suggested_abn = extract_abn(job_text)
if st.session_state.get("_abn_source_ad") != job_text:
    st.session_state["abn_lookup_input"] = suggested_abn
    st.session_state["_abn_source_ad"] = job_text

abn_input = st.text_input(
    "ABN (11 digits)",
    key="abn_lookup_input",
    placeholder="Enter an ABN, or leave blank to search by name",
)
company_name_input = st.text_input(
    "Business or company name (optional)",
    key="abn_company_name_input",
    placeholder="Enter the name shown in the job advertisement",
)

if suggested_abn:
    st.caption(f"Possible ABN found in the advertisement: {suggested_abn}")

if st.button("Verify Business", key="verify_business_button"):
    if not abn_input.strip() and not company_name_input.strip():
        st.warning("Enter an ABN or a business name to search.")
        st.session_state.pop("abn_lookup_result", None)
    elif abn_input.strip() and not is_valid_abn(abn_input):
        st.error("The ABN must contain 11 digits and pass the ABN checksum.")
        st.session_state.pop("abn_lookup_result", None)
    else:
        try:
            st.session_state["abn_lookup_result"] = verify_business(
                abn_input,
                company_name_input,
                secrets=st.secrets,
            )
            st.session_state.pop("abn_selected_entity", None)
        except ABNLookupError as error:
            st.session_state.pop("abn_lookup_result", None)
            st.error(str(error))

abn_result = st.session_state.get("abn_lookup_result")
if abn_result:
    if abn_result["mode"] == "abn":
        entity = abn_result["entity"]
        if entity.get("status", "").lower() == "active":
            st.success("The ABR record reports this ABN as Active.")
        elif entity.get("status", "").lower() == "cancelled":
            st.warning("The ABR record reports this ABN as Cancelled.")
        else:
            st.warning("The ABR record returned an unrecognised ABN status.")

        st.write(f"**ABN:** {entity.get('abn') or 'Not provided'}")
        st.write(f"**Entity name:** {entity.get('entity_name') or 'Not provided'}")
        st.write(f"**ABN status:** {entity.get('status') or 'Not provided'}")
        st.write(f"**Entity type:** {entity.get('entity_type') or 'Not provided'}")
        st.write(f"**GST:** {entity.get('gst_status') or 'Not provided'}")
        if entity.get("gst_from"):
            st.write(f"**GST effective from:** {entity['gst_from']}")
        st.write(f"**State or territory:** {entity.get('state') or 'Not provided'}")
        if entity.get("registration_date"):
            st.write(f"**Registration date:** {entity['registration_date']}")

        comparison = abn_result.get("name_comparison")
        if comparison:
            if comparison["status"] == "exact":
                st.info("The supplied name matches the returned entity name.")
            elif comparison["status"] == "similar":
                st.warning(
                    "The supplied name is similar to the returned entity name. "
                    "Please check the exact legal or business name."
                )
            elif comparison["status"] == "different":
                st.warning(
                    "The supplied name differs from the returned ABR entity name."
                )
            else:
                st.info("A company-name comparison was not available.")

    else:
        matches = abn_result.get("matches", [])
        if not matches:
            st.warning("No business-name matches were returned by the ABR.")
        else:
            st.write(
                f"The ABR returned {len(matches)} possible matching record(s). "
                "Select the business that appears relevant, then verify its ABN."
            )
            options = list(range(len(matches)))
            selected_index = st.selectbox(
                "Possible ABR matches",
                options,
                format_func=lambda index: (
                    f"{matches[index].get('entity_name') or 'Name not provided'} — "
                    f"ABN {matches[index].get('abn')} — "
                    f"{matches[index].get('status') or 'Status not provided'}"
                ),
                key="abn_match_selection",
            )
            selected_match = matches[selected_index]
            if st.button(
                "Verify Selected Business",
                key="verify_selected_business_button",
            ):
                try:
                    st.session_state["abn_selected_entity"] = lookup_by_abn(
                        selected_match["abn"],
                        secrets=st.secrets,
                    )
                except ABNLookupError as error:
                    st.error(str(error))

            selected_entity = st.session_state.get("abn_selected_entity")
            if selected_entity:
                if selected_entity.get("status", "").lower() == "active":
                    st.success("The selected ABR record reports this ABN as Active.")
                elif selected_entity.get("status", "").lower() == "cancelled":
                    st.warning("The selected ABR record reports this ABN as Cancelled.")
                st.write(f"**ABN:** {selected_entity.get('abn') or 'Not provided'}")
                st.write(
                    f"**Entity name:** "
                    f"{selected_entity.get('entity_name') or 'Not provided'}"
                )
                st.write(
                    f"**ABN status:** "
                    f"{selected_entity.get('status') or 'Not provided'}"
                )
                st.write(
                    f"**Entity type:** "
                    f"{selected_entity.get('entity_type') or 'Not provided'}"
                )
                st.write(
                    f"**GST:** "
                    f"{selected_entity.get('gst_status') or 'Not provided'}"
                )
                st.write(
                    f"**State or territory:** "
                    f"{selected_entity.get('state') or 'Not provided'}"
                )

st.info(
    "ABN verification confirms information recorded by the Australian "
    "Business Register. It does not confirm that a job advertisement or "
    "recruiter is genuine."
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

import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(
    page_title="OTT Analytics Dashboard",
    page_icon="📺",
    layout="wide"
)

# ============================================================
# FILES
# Put these five Excel files in the same folder as this script.
# ============================================================
FILES = {
    "content": "content_library .xlsx",
    "ratings": "ratings feedback .xlsx",
    "subscription": "subscription retention .xlsx",
    "profile": "user profile .xlsx",
    "activity": "viewing activity .xlsx",
}


# ============================================================
# LOAD DATA
# ============================================================
@st.cache_data
def load_data():
    content = pd.read_excel(FILES["content"])
    ratings = pd.read_excel(FILES["ratings"])
    subscription = pd.read_excel(FILES["subscription"])
    profile = pd.read_excel(FILES["profile"])
    activity = pd.read_excel(FILES["activity"])

    # Clean column names
    for df in [content, ratings, subscription, profile, activity]:
        df.columns = df.columns.str.strip()

    # --------------------------------------------------------
    # Relationship 1: User_ID
    # profile 1 ---- * activity
    # profile 1 ---- * ratings
    # profile 1 ---- 1 subscription
    # --------------------------------------------------------

    # --------------------------------------------------------
    # Relationship 2: Content_ID / show_id
    #
    # Your files use:
    #   ratings/viewing_activity -> C00001
    #   content_library          -> S00001
    #
    # The numeric part is the same content key, so create a
    # common key for Streamlit joins.
    # --------------------------------------------------------
    content["Content_Key"] = (
        content["show_id"].astype(str).str.extract(r"(\d+)")[0].astype(int)
    )
    ratings["Content_Key"] = (
        ratings["Content_ID"].astype(str).str.extract(r"(\d+)")[0].astype(int)
    )
    activity["Content_Key"] = (
        activity["Content_ID"].astype(str).str.extract(r"(\d+)")[0].astype(int)
    )

    # Make User_ID text consistently
    for df in [ratings, subscription, profile, activity]:
        df["User_ID"] = df["User_ID"].astype(str).str.strip()

    # Merge the dimension information into the activity table.
    # This is the Streamlit equivalent of using the Power BI
    # relationships for analysis.
    activity_full = activity.merge(
        profile,
        on="User_ID",
        how="left",
        suffixes=("", "_Profile")
    )

    activity_full = activity_full.merge(
        subscription[["User_ID", "Monthly_Fee", "Renewal_Status", "Churn_Flag"]],
        on="User_ID",
        how="left"
    )

    activity_full = activity_full.merge(
        content[
            [
                "Content_Key", "show_id", "type", "title", "Platform",
                "country", "release_year", "rating", "listed_in",
                "Duration_Minutes", "Numeric_Rating", "Popularity_Score",
                "Engagement_Proxy"
            ]
        ],
        on="Content_Key",
        how="left"
    )

    # Ratings joined to user/profile and content
    ratings_full = ratings.merge(
        profile,
        on="User_ID",
        how="left",
        suffixes=("", "_Profile")
    ).merge(
        content[
            ["Content_Key", "show_id", "title", "type", "Platform",
             "country", "release_year", "listed_in"]
        ],
        on="Content_Key",
        how="left"
    )

    return content, ratings, subscription, profile, activity_full, ratings_full


try:
    content, ratings, subscription, profile, activity, ratings_full = load_data()
except FileNotFoundError as e:
    st.error(
        f"Could not find one of the Excel files.\n\n"
        f"Make sure all five files are in the same folder as this Python file.\n\n"
        f"Missing file: `{e.filename}`"
    )
    st.stop()


# ============================================================
# HELPER FUNCTIONS
# ============================================================
def fmt_num(value):
    return f"{value:,.0f}"


def apply_filters(df):
    """Apply sidebar filters to a dataframe containing activity data."""
    filtered = df.copy()

    if selected_platform != "All":
        filtered = filtered[filtered["Platform"] == selected_platform]

    if selected_region != "All":
        filtered = filtered[filtered["Region"] == selected_region]

    if selected_age != "All":
        filtered = filtered[filtered["Age_Group"] == selected_age]

    if selected_device != "All":
        filtered = filtered[filtered["Device_Type"] == selected_device]

    if selected_subscription != "All":
        filtered = filtered[
            filtered["Subscription_Type"] == selected_subscription
        ]

    return filtered


# ============================================================
# SIDEBAR
# ============================================================
st.sidebar.title("OTT Dashboard")
st.sidebar.caption("Interactive analysis using the five Excel tables.")

platforms = sorted(activity["Platform"].dropna().unique().tolist())
regions = sorted(activity["Region"].dropna().unique().tolist())
ages = sorted(activity["Age_Group"].dropna().unique().tolist())
devices = sorted(activity["Device_Type"].dropna().unique().tolist())
subs = sorted(activity["Subscription_Type"].dropna().unique().tolist())

selected_platform = st.sidebar.selectbox(
    "Platform", ["All"] + platforms
)
selected_region = st.sidebar.selectbox(
    "Region", ["All"] + regions
)
selected_age = st.sidebar.selectbox(
    "Age Group", ["All"] + ages
)
selected_device = st.sidebar.selectbox(
    "Device Type", ["All"] + devices
)
selected_subscription = st.sidebar.selectbox(
    "Subscription Type", ["All"] + subs
)

filtered_activity = apply_filters(activity)

# Apply matching user/content filters to ratings
filtered_user_ids = set(filtered_activity["User_ID"].dropna().unique())
filtered_content_keys = set(filtered_activity["Content_Key"].dropna().unique())

filtered_ratings = ratings_full[
    ratings_full["User_ID"].isin(filtered_user_ids)
    & ratings_full["Content_Key"].isin(filtered_content_keys)
].copy()


# ============================================================
# HEADER
# ============================================================
st.title("📺 OTT Analytics Dashboard")
st.write(
    "Explore viewing behaviour, audience characteristics, platform performance, "
    "content engagement and customer feedback."
)

st.info(
    "Use the filters on the left. To investigate one platform in detail, "
    "open the **Platform Drill-Through** page and select a platform."
)


# ============================================================
# NAVIGATION
# ============================================================
page = st.radio(
    "Navigate",
    [
        "Overview",
        "Customer Behaviour",
        "Audience Overview",
        "Content & Viewing Behaviour",
        "Platform Analysis",
        "Feedback Analysis",
        "Platform Drill-Through",
    ],
    horizontal=True
)


# ============================================================
# OVERVIEW
# ============================================================
if page == "Overview":
    st.subheader("Overall Performance")

    total_watch = filtered_activity["Watch_Duration_Minutes"].sum()
    total_views = len(filtered_activity)
    avg_completion = filtered_activity["Completion_Percentage"].mean()
    avg_rating = filtered_ratings["Rating"].mean()

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Watch Minutes", fmt_num(total_watch))
    c2.metric("Total Viewing Sessions", fmt_num(total_views))
    c3.metric("Avg Completion", f"{avg_completion:.1f}%")
    c4.metric(
        "Avg Customer Rating",
        f"{avg_rating:.2f}" if pd.notna(avg_rating) else "N/A"
    )

    col1, col2 = st.columns(2)

    with col1:
        device = (
            filtered_activity.groupby("Device_Type", as_index=False)
            ["Watch_Duration_Minutes"].sum()
            .sort_values("Watch_Duration_Minutes", ascending=False)
        )
        fig = px.bar(
            device,
            x="Device_Type",
            y="Watch_Duration_Minutes",
            title="Watch Time by Device Type",
            text_auto=True
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        platform = (
            filtered_activity.groupby("Platform", as_index=False)
            ["Watch_Duration_Minutes"].sum()
            .sort_values("Watch_Duration_Minutes", ascending=False)
        )
        fig = px.bar(
            platform,
            x="Platform",
            y="Watch_Duration_Minutes",
            title="Watch Time by Platform",
            text_auto=True
        )
        st.plotly_chart(fig, use_container_width=True)

    col3, col4 = st.columns(2)

    with col3:
        age = (
            filtered_activity.groupby("Age_Group", as_index=False)
            ["Watch_Duration_Minutes"].sum()
            .sort_values("Watch_Duration_Minutes", ascending=False)
        )
        fig = px.bar(
            age,
            x="Age_Group",
            y="Watch_Duration_Minutes",
            title="Watch Time by Age Group",
            text_auto=True
        )
        st.plotly_chart(fig, use_container_width=True)

    with col4:
        sentiment = (
            filtered_ratings["Feedback_Category"]
            .value_counts()
            .rename_axis("Feedback_Category")
            .reset_index(name="Count")
        )
        fig = px.pie(
            sentiment,
            names="Feedback_Category",
            values="Count",
            title="Customer Sentiment"
        )
        st.plotly_chart(fig, use_container_width=True)


# ============================================================
# CUSTOMER BEHAVIOUR
# ============================================================
elif page == "Customer Behaviour":
    st.subheader("Customer Behaviour")

    col1, col2 = st.columns(2)

    with col1:
        engagement = (
            filtered_activity["Engagement_Level"]
            .value_counts()
            .rename_axis("Engagement_Level")
            .reset_index(name="Users")
        )
        fig = px.bar(
            engagement,
            x="Engagement_Level",
            y="Users",
            title="Users by Engagement Level",
            text_auto=True
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        rewatch = (
            filtered_activity["Rewatched_Flag"]
            .map({"Y": "Rewatched", "N": "Not Rewatched"})
            .value_counts()
            .rename_axis("Category")
            .reset_index(name="Sessions")
        )
        fig = px.pie(
            rewatch,
            names="Category",
            values="Sessions",
            title="Rewatched vs Not Rewatched"
        )
        st.plotly_chart(fig, use_container_width=True)

    col3, col4 = st.columns(2)

    with col3:
        time = (
            filtered_activity.groupby("Time_of_Day", as_index=False)
            ["Watch_Duration_Minutes"].sum()
            .sort_values("Watch_Duration_Minutes", ascending=False)
        )
        fig = px.bar(
            time,
            x="Time_of_Day",
            y="Watch_Duration_Minutes",
            title="Watch Time by Time of Day",
            text_auto=True
        )
        st.plotly_chart(fig, use_container_width=True)

    with col4:
        completion = (
            filtered_activity.groupby("Completion_Percentage", as_index=False)
            .size()
            .sort_values("Completion_Percentage")
        )
        fig = px.histogram(
            filtered_activity,
            x="Completion_Percentage",
            nbins=15,
            title="Completion Percentage Distribution"
        )
        st.plotly_chart(fig, use_container_width=True)


# ============================================================
# AUDIENCE OVERVIEW
# ============================================================
elif page == "Audience Overview":
    st.subheader("Audience Overview")

    col1, col2 = st.columns(2)

    with col1:
        gender = (
            filtered_activity["Gender"]
            .value_counts()
            .rename_axis("Gender")
            .reset_index(name="Users")
        )
        fig = px.pie(
            gender,
            names="Gender",
            values="Users",
            title="Audience by Gender"
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        region = (
            filtered_activity.groupby("Region", as_index=False)
            ["Watch_Duration_Minutes"].sum()
            .sort_values("Watch_Duration_Minutes", ascending=False)
        )
        fig = px.bar(
            region,
            x="Region",
            y="Watch_Duration_Minutes",
            title="Watch Time by Region",
            text_auto=True
        )
        st.plotly_chart(fig, use_container_width=True)

    age_device = (
        filtered_activity.groupby(
            ["Age_Group", "Device_Type"], as_index=False
        )["Watch_Duration_Minutes"].sum()
    )
    fig = px.bar(
        age_device,
        x="Age_Group",
        y="Watch_Duration_Minutes",
        color="Device_Type",
        barmode="group",
        title="Watch Time by Age Group and Device"
    )
    st.plotly_chart(fig, use_container_width=True)


# ============================================================
# CONTENT & VIEWING BEHAVIOUR
# ============================================================
elif page == "Content & Viewing Behaviour":
    st.subheader("Content & Viewing Behaviour")

    col1, col2 = st.columns(2)

    with col1:
        content_type = (
            filtered_activity.groupby("type", as_index=False)
            ["Watch_Duration_Minutes"].sum()
            .sort_values("Watch_Duration_Minutes", ascending=False)
        )
        fig = px.bar(
            content_type,
            x="type",
            y="Watch_Duration_Minutes",
            title="Watch Time: Movies vs TV Shows",
            text_auto=True
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        top_content = (
            filtered_activity.groupby("title", as_index=False)
            ["Watch_Duration_Minutes"].sum()
            .sort_values("Watch_Duration_Minutes", ascending=False)
            .head(10)
        )
        fig = px.bar(
            top_content.sort_values("Watch_Duration_Minutes"),
            x="Watch_Duration_Minutes",
            y="title",
            orientation="h",
            title="Top 10 Content by Watch Time"
        )
        st.plotly_chart(fig, use_container_width=True)

    col3, col4 = st.columns(2)

    with col3:
        paused = (
            filtered_activity.groupby("Paused_Times", as_index=False)
            .size()
            .rename(columns={"size": "Sessions"})
        )
        fig = px.bar(
            paused,
            x="Paused_Times",
            y="Sessions",
            title="Sessions by Number of Pauses"
        )
        st.plotly_chart(fig, use_container_width=True)

    with col4:
        recent = (
            filtered_activity.groupby("release_year", as_index=False)
            ["Watch_Duration_Minutes"].sum()
            .sort_values("release_year")
        )
        fig = px.line(
            recent,
            x="release_year",
            y="Watch_Duration_Minutes",
            markers=True,
            title="Watch Time by Content Release Year"
        )
        st.plotly_chart(fig, use_container_width=True)


# ============================================================
# PLATFORM ANALYSIS
# ============================================================
elif page == "Platform Analysis":
    st.subheader("Platform Analysis")

    platform_summary = (
        filtered_activity.groupby("Platform")
        .agg(
            Watch_Minutes=("Watch_Duration_Minutes", "sum"),
            Sessions=("Session_ID", "nunique"),
            Avg_Completion=("Completion_Percentage", "mean"),
            Avg_Watch_Duration=("Watch_Duration_Minutes", "mean"),
        )
        .reset_index()
    )

    st.dataframe(
        platform_summary.style.format({
            "Watch_Minutes": "{:,.0f}",
            "Sessions": "{:,.0f}",
            "Avg_Completion": "{:.1f}%",
            "Avg_Watch_Duration": "{:.1f}",
        }),
        use_container_width=True,
        hide_index=True
    )

    col1, col2 = st.columns(2)

    with col1:
        fig = px.bar(
            platform_summary.sort_values("Watch_Minutes"),
            x="Watch_Minutes",
            y="Platform",
            orientation="h",
            title="Total Watch Time by Platform",
            text_auto=True
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        fig = px.bar(
            platform_summary.sort_values("Avg_Completion"),
            x="Avg_Completion",
            y="Platform",
            orientation="h",
            title="Average Completion by Platform"
        )
        st.plotly_chart(fig, use_container_width=True)


# ============================================================
# FEEDBACK ANALYSIS
# ============================================================
elif page == "Feedback Analysis":
    st.subheader("Customer Feedback Analysis")

    col1, col2 = st.columns(2)

    with col1:
        sentiment = (
            filtered_ratings.groupby("Feedback_Category")
            .size()
            .reset_index(name="Feedback_Count")
        )
        fig = px.bar(
            sentiment,
            x="Feedback_Category",
            y="Feedback_Count",
            title="Feedback by Sentiment",
            text_auto=True
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        feedback_platform = (
            filtered_ratings.groupby(
                ["Platform", "Feedback_Category"]
            )
            .size()
            .reset_index(name="Count")
        )
        fig = px.bar(
            feedback_platform,
            x="Platform",
            y="Count",
            color="Feedback_Category",
            barmode="group",
            title="Feedback by Platform"
        )
        st.plotly_chart(fig, use_container_width=True)

    age_feedback = (
        filtered_ratings.groupby(
            ["Age_Group", "Feedback_Category"]
        )
        .size()
        .reset_index(name="Count")
    )
    fig = px.bar(
        age_feedback,
        x="Age_Group",
        y="Count",
        color="Feedback_Category",
        barmode="group",
        title="Feedback by Age Group"
    )
    st.plotly_chart(fig, use_container_width=True)


# ============================================================
# PLATFORM DRILL-THROUGH
# ============================================================
elif page == "Platform Drill-Through":
    st.subheader("Platform Drill-Through")

    st.write(
        "Select one platform. Every visual below automatically changes to "
        "show only that platform's customers, viewing behaviour and feedback."
    )

    drill_platform = st.selectbox(
        "Select Platform",
        sorted(activity["Platform"].dropna().unique())
    )

    drill_activity = activity[
        activity["Platform"] == drill_platform
    ].copy()

    drill_user_ids = set(drill_activity["User_ID"].dropna().unique())
    drill_content_keys = set(drill_activity["Content_Key"].dropna().unique())

    drill_ratings = ratings_full[
        ratings_full["User_ID"].isin(drill_user_ids)
        & ratings_full["Content_Key"].isin(drill_content_keys)
        & (ratings_full["Platform"] == drill_platform)
    ].copy()

    # Four charts requested for the drill-through page
    col1, col2 = st.columns(2)

    with col1:
        device = (
            drill_activity.groupby("Device_Type", as_index=False)
            ["Watch_Duration_Minutes"].sum()
            .sort_values("Watch_Duration_Minutes", ascending=False)
        )
        fig = px.bar(
            device,
            x="Device_Type",
            y="Watch_Duration_Minutes",
            title=f"{drill_platform} — Watch Time by Device Type",
            text_auto=True
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        age = (
            drill_activity.groupby("Age_Group", as_index=False)
            ["Watch_Duration_Minutes"].sum()
            .sort_values("Watch_Duration_Minutes", ascending=False)
        )
        fig = px.bar(
            age,
            x="Age_Group",
            y="Watch_Duration_Minutes",
            title=f"{drill_platform} — Watch Time by Age Group",
            text_auto=True
        )
        st.plotly_chart(fig, use_container_width=True)

    col3, col4 = st.columns(2)

    with col3:
        rewatch = (
            drill_activity["Rewatched_Flag"]
            .map({"Y": "Rewatched", "N": "Not Rewatched"})
            .value_counts()
            .rename_axis("Category")
            .reset_index(name="Sessions")
        )
        fig = px.pie(
            rewatch,
            names="Category",
            values="Sessions",
            title=f"{drill_platform} — Rewatched vs Not Rewatched"
        )
        st.plotly_chart(fig, use_container_width=True)

    with col4:
        feedback = (
            drill_ratings["Feedback_Category"]
            .value_counts()
            .rename_axis("Feedback_Category")
            .reset_index(name="Count")
        )
        fig = px.pie(
            feedback,
            names="Feedback_Category",
            values="Count",
            title=f"{drill_platform} — Customer Sentiment"
        )
        st.plotly_chart(fig, use_container_width=True)

    # Drill-through KPIs
    st.markdown("### Platform Summary")
    total_watch = drill_activity["Watch_Duration_Minutes"].sum()
    sessions = drill_activity["Session_ID"].nunique()
    completion = drill_activity["Completion_Percentage"].mean()
    rating = drill_ratings["Rating"].mean()

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Watch Minutes", fmt_num(total_watch))
    k2.metric("Sessions", fmt_num(sessions))
    k3.metric("Avg Completion", f"{completion:.1f}%")
    k4.metric(
        "Avg Rating",
        f"{rating:.2f}" if pd.notna(rating) else "N/A"
    )

    st.markdown("### Top Content on Selected Platform")
    top = (
        drill_activity.groupby(["title", "type"], as_index=False)
        .agg(
            Watch_Minutes=("Watch_Duration_Minutes", "sum"),
            Sessions=("Session_ID", "nunique")
        )
        .sort_values("Watch_Minutes", ascending=False)
        .head(10)
    )

    st.dataframe(
        top.style.format({
            "Watch_Minutes": "{:,.0f}",
            "Sessions": "{:,.0f}"
        }),
        use_container_width=True,
        hide_index=True
    )


# ============================================================
# FOOTER / DATA RELATIONSHIPS
# ============================================================
st.divider()
with st.expander("Show data relationships used by this app"):
    st.markdown("""
**1. `user_profile` → `viewing_activity`**  
`User_ID` (1-to-many)

**2. `user_profile` → `ratings_feedback`**  
`User_ID` (1-to-many)

**3. `user_profile` → `subscription_retention`**  
`User_ID` (1-to-1)

**4. `content_library` → `viewing_activity`**  
Content key relationship. `content_library.show_id` and
`viewing_activity.Content_ID` have different prefixes, so the numeric
part is normalized into `Content_Key`.

**5. `content_library` → `ratings_feedback`**  
Same normalized `Content_Key` relationship.

This reproduces the analytical effect of the Power BI relationships
inside Streamlit using pandas merges.
""")

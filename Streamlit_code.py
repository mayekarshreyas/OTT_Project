import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# =========================================================
# PAGE CONFIGURATION
# =========================================================

st.set_page_config(
    page_title="OTT Analytics Dashboard",
    page_icon="📺",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("📺 OTT Platform Analytics Dashboard")
st.caption(
    "Business Intelligence Dashboard | Customer Behaviour, "
    "Audience, Content & Platform Analysis"
)

# =========================================================
# LOAD DATA
# =========================================================

@st.cache_data
def load_data():

    folder_path = r"C:\Data Analyst\Topic 7\OTT_Project\Datasets\Excel_datasets"

    files = {
        "content": "content_library.xlsx",
        "ratings": "ratings_feedback.xlsx",
        "subscription": "subscription_retention.xlsx",
        "user": "user_profile.xlsx",
        "viewing": "viewing_activity.xlsx"
    }

    data = {}

    for key, file in files.items():
        file_path = f"{folder_path}\\{file}"

        try:
            temp_df = pd.read_excel(file_path)

            temp_df.columns = (
                temp_df.columns
                .astype(str)
                .str.strip()
                .str.replace(r"\s+", "_", regex=True)
            )

            data[key] = temp_df

        except Exception as e:
            st.error(f"Could not load {file}: {e}")
            data[key] = pd.DataFrame()

    return data


data = load_data()

content_df = data["content"]
ratings_df = data["ratings"]
subscription_df = data["subscription"]
user_df = data["user"]
viewing_df = data["viewing"]


# =========================================================
# HELPER FUNCTIONS
# =========================================================

def clean_columns(df):
    if df.empty:
        return df

    df = df.copy()

    df.columns = (
        df.columns
        .astype(str)
        .str.strip()
        .str.replace(r"\s+", "_", regex=True)
    )

    return df


def find_column(df, options):

    if df.empty:
        return None

    # Exact match first
    for option in options:
        if option in df.columns:
            return option

    # Case-insensitive match
    lower_map = {str(c).lower(): c for c in df.columns}

    for option in options:
        if option.lower() in lower_map:
            return lower_map[option.lower()]

    return None


def numeric_sum(df, column):

    if column is None or column not in df.columns:
        return 0

    return pd.to_numeric(
        df[column],
        errors="coerce"
    ).fillna(0).sum()


def numeric_mean(df, column):

    if column is None or column not in df.columns:
        return 0

    return pd.to_numeric(
        df[column],
        errors="coerce"
    ).mean()


def show_no_data(message="No data available for this visualization."):

    st.info(message)


# =========================================================
# CLEAN DATA
# =========================================================

content_df = clean_columns(content_df)
ratings_df = clean_columns(ratings_df)
subscription_df = clean_columns(subscription_df)
user_df = clean_columns(user_df)
viewing_df = clean_columns(viewing_df)


# =========================================================
# CREATE MASTER DATASET
# =========================================================

df = viewing_df.copy()


# ---------------------------------------------------------
# MERGE USER PROFILE
# ---------------------------------------------------------

if not user_df.empty and "User_ID" in df.columns and "User_ID" in user_df.columns:

    user_columns = [
        c for c in [
            "User_ID",
            "Gender",
            "Age_Group",
            "Region",
            "Country",
            "Subscription_Type",
            "Platform",
            "Device_Type"
        ]
        if c in user_df.columns
    ]

    if len(user_columns) > 1:

        user_temp = user_df[user_columns].drop_duplicates("User_ID")

        df = df.merge(
            user_temp,
            on="User_ID",
            how="left",
            suffixes=("", "_user")
        )

        # Fill missing columns from user table
        for col_name in user_columns:

            if col_name == "User_ID":
                continue

            duplicate_col = f"{col_name}_user"

            if duplicate_col in df.columns:

                if col_name in df.columns:
                    df[col_name] = df[col_name].fillna(
                        df[duplicate_col]
                    )
                    df.drop(columns=[duplicate_col], inplace=True)

                else:
                    df.rename(
                        columns={duplicate_col: col_name},
                        inplace=True
                    )


# ---------------------------------------------------------
# MERGE SUBSCRIPTION DATA
# ---------------------------------------------------------

if (
    not subscription_df.empty
    and "User_ID" in df.columns
    and "User_ID" in subscription_df.columns
):

    sub_columns = [
        c for c in [
            "User_ID",
            "Subscription_Type",
            "Churn",
            "Churn_Flag",
            "Is_Churned",
            "Renewal_Status"
        ]
        if c in subscription_df.columns
    ]

    if len(sub_columns) > 1:

        sub_temp = subscription_df[sub_columns].drop_duplicates("User_ID")

        df = df.merge(
            sub_temp,
            on="User_ID",
            how="left",
            suffixes=("", "_subscription")
        )

        for col_name in sub_columns:

            if col_name == "User_ID":
                continue

            duplicate_col = f"{col_name}_subscription"

            if duplicate_col in df.columns:

                if col_name in df.columns:
                    df[col_name] = df[col_name].fillna(
                        df[duplicate_col]
                    )
                    df.drop(columns=[duplicate_col], inplace=True)

                else:
                    df.rename(
                        columns={duplicate_col: col_name},
                        inplace=True
                    )


# ---------------------------------------------------------
# MERGE RATINGS / FEEDBACK
# ---------------------------------------------------------

if (
    not ratings_df.empty
    and "User_ID" in df.columns
    and "User_ID" in ratings_df.columns
):

    rating_columns = [
        c for c in [
            "User_ID",
            "Rating",
            "Average_Rating",
            "Feedback_Category",
            "Feedback"
        ]
        if c in ratings_df.columns
    ]

    if len(rating_columns) > 1:

        rating_temp = ratings_df[rating_columns].copy()

        # Avoid duplicate User_ID records
        if "User_ID" in rating_temp.columns:
            rating_temp = rating_temp.groupby(
                "User_ID",
                as_index=False
            ).first()

        df = df.merge(
            rating_temp,
            on="User_ID",
            how="left",
            suffixes=("", "_rating")
        )

        for col_name in rating_columns:

            if col_name == "User_ID":
                continue

            duplicate_col = f"{col_name}_rating"

            if duplicate_col in df.columns:

                if col_name in df.columns:
                    df[col_name] = df[col_name].fillna(
                        df[duplicate_col]
                    )
                    df.drop(columns=[duplicate_col], inplace=True)

                else:
                    df.rename(
                        columns={duplicate_col: col_name},
                        inplace=True
                    )


# ---------------------------------------------------------
# MERGE CONTENT LIBRARY
# ---------------------------------------------------------

# Try Content_ID first
content_key = None

if "Content_ID" in df.columns and "Content_ID" in content_df.columns:
    content_key = "Content_ID"

elif "Content_ID" in df.columns and "Content_Id" in content_df.columns:
    content_key = "Content_Id"

elif "Show_ID" in df.columns and "Show_ID" in content_df.columns:
    content_key = "Show_ID"


if not content_df.empty and content_key:

    content_columns = [
        c for c in [
            content_key,
            "Content_ID",
            "Show_ID",
            "Content_Title",
            "Title",
            "Content_Name",
            "Genre",
            "Content_Genre",
            "Country",
            "type",
            "Type",
            "Release_Year"
        ]
        if c in content_df.columns
    ]

    # Remove duplicate column names
    content_columns = list(dict.fromkeys(content_columns))

    if len(content_columns) > 1:

        content_temp = content_df[content_columns].copy()

        content_temp = content_temp.drop_duplicates(
            subset=[content_key]
        )

        df = df.merge(
            content_temp,
            on=content_key,
            how="left",
            suffixes=("", "_content")
        )

        # Resolve duplicate columns
        for base_col in [
            "Content_Title",
            "Title",
            "Content_Name",
            "Genre",
            "Content_Genre",
            "Country",
            "type",
            "Type"
        ]:

            duplicate_col = f"{base_col}_content"

            if duplicate_col in df.columns:

                if base_col in df.columns:
                    df[base_col] = df[base_col].fillna(
                        df[duplicate_col]
                    )
                    df.drop(
                        columns=[duplicate_col],
                        inplace=True
                    )

                else:
                    df.rename(
                        columns={duplicate_col: base_col},
                        inplace=True
                    )


# =========================================================
# COLUMN DETECTION
# =========================================================

watch_col = find_column(
    df,
    [
        "Watch_Duration_Minutes",
        "Duration_Minutes",
        "Watch_Minutes",
        "Watch_Duration"
    ]
)

completion_col = find_column(
    df,
    [
        "Completion_Percentage",
        "Completion_Percent",
        "Completion"
    ]
)

rating_col = find_column(
    df,
    [
        "Rating",
        "Average_Rating"
    ]
)

session_col = find_column(
    df,
    [
        "Viewing_Sessions",
        "Sessions",
        "Viewing_Session"
    ]
)

churn_col = find_column(
    df,
    [
        "Churn",
        "Churn_Flag",
        "Is_Churned"
    ]
)

content_col = find_column(
    df,
    [
        "Content_Title",
        "Title",
        "Content_Name",
        "Show_Name"
    ]
)

genre_col = find_column(
    df,
    [
        "Genre",
        "Content_Genre"
    ]
)

engagement_col = find_column(
    df,
    [
        "Watch_Engagement",
        "Engagement_Level",
        "Engagement"
    ]
)


# =========================================================
# SIDEBAR
# =========================================================

st.sidebar.header("📑 Dashboard Pages")

page = st.sidebar.radio(
    "Select Page",
    [
        "📊 Overall Performance",
        "👥 Customer Behaviour",
        "👤 Audience Overview",
        "🎬 Content & Viewing",
        "📱 Churn Analysis"
    ]
)


# =========================================================
# FILTERS
# =========================================================

st.sidebar.markdown("---")
st.sidebar.header("🎛️ Filters")

filtered_df = df.copy()


def add_filter(column, label):

    global filtered_df

    if column not in df.columns:
        return

    values = (
        df[column]
        .dropna()
        .astype(str)
        .unique()
        .tolist()
    )

    values = sorted(values)

    if len(values) == 0:
        return

    selected = st.sidebar.multiselect(
        label,
        values,
        default=values,
        key="filter_" + column
    )

    if selected:

        filtered_df = filtered_df[
            filtered_df[column]
            .astype(str)
            .isin(selected)
        ]

    else:

        filtered_df = filtered_df.iloc[0:0]


filter_list = [
    ("Gender", "Gender"),
    ("Age_Group", "Age Group"),
    ("Region", "Region"),
    ("Subscription_Type", "Subscription Type"),
    ("Platform", "Platform"),
    ("type", "Content Type"),
    ("Type", "Content Type"),
    ("Feedback_Category", "Feedback Category"),
    ("Country", "Country"),
    ("Time_of_Day", "Time of Day"),
    ("Device_Type", "Device Type"),
    ("Watch_Engagement", "Watch Engagement"),
    ("Completion_Category", "Completion Category"),
    ("Rewatched_Flag", "Rewatched")
]


for column, label in filter_list:

    if column in df.columns:
        add_filter(column, label)


st.sidebar.markdown("---")

st.sidebar.write(
    f"**Filtered Records:** {len(filtered_df):,}"
)


# =========================================================
# PAGE 1 — OVERALL PERFORMANCE
# =========================================================

if page == "📊 Overall Performance":

    st.header("📊 Overall Performance")

    viewers = (
        filtered_df["User_ID"].nunique()
        if "User_ID" in filtered_df.columns
        else len(filtered_df)
    )

    sessions = (
        numeric_sum(filtered_df, session_col)
        if session_col
        else len(filtered_df)
    )

    watch = numeric_sum(
        filtered_df,
        watch_col
    )

    avg_completion = numeric_mean(
        filtered_df,
        completion_col
    )

    avg_rating = numeric_mean(
        filtered_df,
        rating_col
    )

    a, b, c, d, e = st.columns(5)

    a.metric(
        "Total Viewers",
        f"{viewers / 1000:.1f}K"
    )

    b.metric(
        "Viewing Sessions",
        f"{sessions / 1000:.1f}K"
    )

    c.metric(
        "Total Watch Minutes",
        f"{watch / 1_000_000:.2f}M"
    )

    d.metric(
        "Total Watch Hours",
        f"{watch / 60_000:.2f}K"
    )

    e.metric(
        "Avg Completion",
        f"{avg_completion:.2f}%"
    )

    st.markdown("---")

    c1, c2 = st.columns(2)

    # Platform watch time
    if "Platform" in filtered_df.columns and watch_col:

        x = (
            filtered_df
            .groupby("Platform")[watch_col]
            .sum()
            .reset_index()
        )

        fig = px.bar(
            x,
            x=watch_col,
            y="Platform",
            orientation="h",
            title="Total Watch Time by Platform",
            text_auto=".2s"
        )

        c1.plotly_chart(
            fig,
            use_container_width=True
        )

    # Completion
    if completion_col and "Platform" in filtered_df.columns:

        x = (
            filtered_df
            .groupby("Platform")[completion_col]
            .mean()
            .reset_index()
        )

        fig = px.bar(
            x,
            x="Platform",
            y=completion_col,
            title="Average Completion by Platform",
            text_auto=".2f"
        )

        c2.plotly_chart(
            fig,
            use_container_width=True
        )


# =========================================================
# PAGE 2 — CUSTOMER BEHAVIOUR
# =========================================================

elif page == "👥 Customer Behaviour":

    st.header("👥 Customer Behaviour")

    c1, c2 = st.columns(2)

    # -----------------------------------------------------
    # CHURN BY REGION
    # -----------------------------------------------------

    if (
        "Region" in filtered_df.columns
        and churn_col
    ):

        temp = filtered_df.copy()

        temp[churn_col] = pd.to_numeric(
            temp[churn_col],
            errors="coerce"
        )

        x = (
            temp
            .groupby("Region")[churn_col]
            .mean()
            .reset_index(name="Churn Rate")
        )

        x["Churn Rate"] = x["Churn Rate"] * 100

        fig = px.bar(
            x,
            x="Churn Rate",
            y="Region",
            orientation="h",
            title="Churn Rate by Region",
            text="Churn Rate"
        )

        fig.update_traces(
            texttemplate="%{text:.2f}%",
            textposition="outside"
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

    st.markdown("---")

    # -----------------------------------------------------
    # SUBSCRIPTION CHURN
    # -----------------------------------------------------

    c1, c2 = st.columns(2)

    if (
        "Subscription_Type" in filtered_df.columns
        and churn_col
    ):

        temp = filtered_df.copy()

        temp[churn_col] = pd.to_numeric(
            temp[churn_col],
            errors="coerce"
        )

        x = (
            temp
            .groupby("Subscription_Type")[churn_col]
            .mean()
            .reset_index(name="Churn Rate")
        )

        x["Churn Rate"] = x["Churn Rate"] * 100

        fig = px.bar(
            x,
            x="Subscription_Type",
            y="Churn Rate",
            title="Churn Rate by Subscription Type",
            text="Churn Rate"
        )

        fig.update_traces(
            texttemplate="%{text:.2f}%",
            textposition="outside"
        )

        c1.plotly_chart(
            fig,
            use_container_width=True
        )

# VIEWING TIME
    # -----------------------------------------------------

    if (
        "Time_of_Day" in filtered_df.columns
    ):

        if session_col:

            x = (
                filtered_df
                .groupby("Time_of_Day")[session_col]
                .sum()
                .reset_index(name="Viewing Sessions")
            )

        else:

            x = (
                filtered_df["Time_of_Day"]
                .value_counts()
                .reset_index()
            )

            x.columns = [
                "Time_of_Day",
                "Viewing Sessions"
            ]

        fig = px.bar(
            x,
            x="Time_of_Day",
            y="Viewing Sessions",
            title="Viewing Behaviour by Time of Day",
            text_auto=".2s"
        )

        c2.plotly_chart(
            fig,
            use_container_width=True
        )


# =========================================================
# PAGE 3 — AUDIENCE OVERVIEW
# =========================================================

elif page == "👤 Audience Overview":

    st.header("👤 Audience Overview")

    # -----------------------------------------------------
    # TOP CONTENT
    # -----------------------------------------------------

    c1, c2 = st.columns(2)

    if content_col:

        x = (
            filtered_df[content_col]
            .value_counts()
            .head(10)
            .reset_index()
        )

        x.columns = [
            content_col,
            "Viewing Sessions"
        ]

        x = x.sort_values(
            "Viewing Sessions"
        )

        fig = px.bar(
            x,
            x="Viewing Sessions",
            y=content_col,
            orientation="h",
            title="Top 10 Most Watched Content",
            text="Viewing Sessions"
        )

        fig.update_traces(
            textposition="outside"
        )

        c1.plotly_chart(
            fig,
            use_container_width=True
        )

    # -----------------------------------------------------
    # GENRE
    # -----------------------------------------------------

    if genre_col:

        x = (
            filtered_df[genre_col]
            .value_counts()
            .head(15)
            .reset_index()
        )

        x.columns = [
            genre_col,
            "Viewing Sessions"
        ]

        x = x.sort_values(
            "Viewing Sessions"
        )

        fig = px.bar(
            x,
            x="Viewing Sessions",
            y=genre_col,
            orientation="h",
            title="Most Popular Genres",
            text="Viewing Sessions"
        )

        fig.update_traces(
            textposition="outside"
        )

        c2.plotly_chart(
            fig,
            use_container_width=True
        )

    st.markdown("---")

    # -----------------------------------------------------
    # AGE GROUP
    # -----------------------------------------------------

    c1, c2 = st.columns(2)

    if "Age_Group" in filtered_df.columns:

        if "User_ID" in filtered_df.columns:

            audience_data = (
                filtered_df
                .groupby("Age_Group")["User_ID"]
                .nunique()
                .reset_index(
                    name="Audience Size"
                )
            )

        else:

            audience_data = (
                filtered_df["Age_Group"]
                .value_counts()
                .reset_index()
            )

            audience_data.columns = [
                "Age_Group",
                "Audience Size"
            ]

        if completion_col:

            completion_data = (
                filtered_df
                .groupby("Age_Group")[completion_col]
                .mean()
                .reset_index(
                    name="Avg Completion"
                )
            )

            audience_data = audience_data.merge(
                completion_data,
                on="Age_Group",
                how="left"
            )

            fig = go.Figure()

            fig.add_trace(
                go.Bar(
                    x=audience_data["Age_Group"],
                    y=audience_data["Audience Size"],
                    name="Audience Size"
                )
            )

            fig.add_trace(
                go.Scatter(
                    x=audience_data["Age_Group"],
                    y=audience_data["Avg Completion"],
                    mode="lines+markers",
                    name="Avg Completion %",
                    yaxis="y2"
                )
            )

            fig.update_layout(
                title="Audience Size vs Completion by Age Group",
                yaxis=dict(
                    title="Audience Size"
                ),
                yaxis2=dict(
                    title="Avg Completion %",
                    overlaying="y",
                    side="right"
                )
            )

            c1.plotly_chart(
                fig,
                use_container_width=True
            )

        else:

            fig = px.bar(
                audience_data,
                x="Age_Group",
                y="Audience Size",
                title="Audience Size by Age Group",
                text_auto=True
            )

            c1.plotly_chart(
                fig,
                use_container_width=True
            )

    # -----------------------------------------------------
    # ENGAGEMENT
    # -----------------------------------------------------

    if engagement_col:

        x = (
            filtered_df[engagement_col]
            .value_counts()
            .reset_index()
        )

        x.columns = [
            engagement_col,
            "Audience"
        ]

        fig = px.pie(
            x,
            names=engagement_col,
            values="Audience",
            hole=0.45,
            title="Audience by Engagement Level"
        )

        c2.plotly_chart(
            fig,
            use_container_width=True
        )


# =========================================================
# PAGE 4 — CONTENT & VIEWING
# =========================================================

elif page == "🎬 Content & Viewing":

    st.header("🎬 Content & Viewing Behaviour")

    c1, c2, c3 = st.columns(3)

    # -----------------------------------------------------
    # DEVICE PERFORMANCE
    # -----------------------------------------------------

    if (
        "Device_Type" in filtered_df.columns
        and watch_col
        and completion_col
    ):

        x = (
            filtered_df
            .groupby("Device_Type")
            .agg(
                Watch_Duration=(watch_col, "mean"),
                Completion=(completion_col, "mean")
            )
            .reset_index()
        )

        fig = px.scatter(
            x,
            x="Watch_Duration",
            y="Completion",
            color="Device_Type",
            text="Device_Type",
            title="Watch Duration vs Completion"
        )

        fig.update_traces(
            textposition="top center"
        )

        c1.plotly_chart(
            fig,
            use_container_width=True
        )

    # -----------------------------------------------------
    # FEEDBACK
    # -----------------------------------------------------

    if "Feedback_Category" in filtered_df.columns:

        x = (
            filtered_df["Feedback_Category"]
            .value_counts()
            .reset_index()
        )

        x.columns = [
            "Feedback_Category",
            "Count"
        ]

        fig = px.pie(
            x,
            names="Feedback_Category",
            values="Count",
            hole=0.45,
            title="Feedback Category Distribution"
        )

        c2.plotly_chart(
            fig,
            use_container_width=True
        )

    # -----------------------------------------------------
    # REWATCHED
    # -----------------------------------------------------

    if "Rewatched_Flag" in filtered_df.columns:

        if session_col:

            x = (
                filtered_df
                .groupby("Rewatched_Flag")[session_col]
                .sum()
                .reset_index(
                    name="Sessions"
                )
            )

        else:

            x = (
                filtered_df["Rewatched_Flag"]
                .value_counts()
                .reset_index()
            )

            x.columns = [
                "Rewatched_Flag",
                "Sessions"
            ]

        fig = px.bar(
            x,
            x="Rewatched_Flag",
            y="Sessions",
            title="Total Sessions by Rewatched Flag",
            text_auto=True
        )

        c3.plotly_chart(
            fig,
            use_container_width=True
        )

    st.markdown("---")

    c1, c2 = st.columns(2)

    # -----------------------------------------------------
    # DEVICE WATCH TIME
    # -----------------------------------------------------

    if (
        "Device_Type" in filtered_df.columns
        and watch_col
    ):

        x = (
            filtered_df
            .groupby("Device_Type")[watch_col]
            .sum()
            .reset_index()
        )

        fig = px.bar(
            x,
            x="Device_Type",
            y=watch_col,
            title="Total Watch Duration by Device",
            text_auto=".2s"
        )

        c1.plotly_chart(
            fig,
            use_container_width=True
        )

    # -----------------------------------------------------
    # COMPLETION CATEGORY
    # -----------------------------------------------------

    if "Completion_Category" in filtered_df.columns:

        x = (
            filtered_df["Completion_Category"]
            .value_counts()
            .reset_index()
        )

        x.columns = [
            "Completion_Category",
            "Sessions"
        ]

        fig = px.bar(
            x,
            x="Completion_Category",
            y="Sessions",
            title="Viewing Sessions by Completion Category",
            text_auto=True
        )

        c2.plotly_chart(
            fig,
            use_container_width=True
        )

# =========================================================
# PAGE 5 — PLATFORM ANALYSIS
# =========================================================

elif page == "📱 Churn Analysis":

    st.header("📱 Churn Analysis")

    # -----------------------------------------------------
    # COUNTRY / TV SHOW
    # -----------------------------------------------------

    c1, c2 = st.columns(2)

    type_col = find_column(
        filtered_df,
        ["type", "Type", "Content_Type"]
    )

    country_col = find_column(
        filtered_df,
        ["Country", "Content_Country"]
    )

    if country_col and type_col:

        tv_data = filtered_df[
            filtered_df[type_col]
            .astype(str)
            .str.lower()
            .isin([
                "tv show",
                "tv_show",
                "tvshow"
            ])
        ]

        x = (
            tv_data[country_col]
            .value_counts()
            .head(10)
            .reset_index()
        )

        x.columns = [
            country_col,
            "TV Shows"
        ]

        if not x.empty:

            fig = px.treemap(
                x,
                path=[country_col],
                values="TV Shows",
                title="Top 10 Countries by TV Show Titles"
            )

            c1.plotly_chart(
                fig,
                use_container_width=True
            )

    # -----------------------------------------------------
    # TOTAL WATCH TIME
    # -----------------------------------------------------

    if (
        "Platform" in filtered_df.columns
        and watch_col
    ):

        x = (
            filtered_df
            .groupby("Platform")[watch_col]
            .sum()
            .reset_index()
        )

        fig = px.bar(
            x,
            x=watch_col,
            y="Platform",
            orientation="h",
            title="Total Watch Time by Platform",
            text_auto=".2s"
        )

        c2.plotly_chart(
            fig,
            use_container_width=True
        )

    st.markdown("---")

    # -----------------------------------------------------
    # CHURN BY AGE
    # -----------------------------------------------------

    c1, c2, c3 = st.columns(3)

    if (
        "Age_Group" in filtered_df.columns
        and churn_col
    ):

        temp = filtered_df.copy()

        temp[churn_col] = pd.to_numeric(
            temp[churn_col],
            errors="coerce"
        )

        x = (
            temp
            .groupby("Age_Group")[churn_col]
            .mean()
            .reset_index(
                name="Churn Rate"
            )
        )

        x["Churn Rate"] *= 100

        fig = px.bar(
            x,
            x="Age_Group",
            y="Churn Rate",
            title="Churn Rate by Age Group",
            text="Churn Rate"
        )

        fig.update_traces(
            texttemplate="%{text:.2f}%",
            textposition="outside"
        )

        c1.plotly_chart(
            fig,
            use_container_width=True
        )

    # -----------------------------------------------------
    # AVERAGE RATING
    # -----------------------------------------------------

    if (
        "Platform" in filtered_df.columns
        and rating_col
    ):

        x = (
            filtered_df
            .groupby("Platform")[rating_col]
            .mean()
            .reset_index()
        )

        fig = px.bar(
            x,
            x="Platform",
            y=rating_col,
            title="Average Rating by Platform",
            text_auto=".2f"
        )

        c2.plotly_chart(
            fig,
            use_container_width=True
        )

    # -----------------------------------------------------
    # AVERAGE WATCH TIME
    # -----------------------------------------------------

    if (
        "Platform" in filtered_df.columns
        and watch_col
    ):

        x = (
            filtered_df
            .groupby("Platform")[watch_col]
            .mean()
            .reset_index()
        )

        fig = px.bar(
            x,
            x=watch_col,
            y="Platform",
            orientation="h",
            title="Average Watch Time per Session",
            text_auto=".0f"
        )

        c3.plotly_chart(
            fig,
            use_container_width=True
        )

    # -----------------------------------------------------
    # FEEDBACK BY PLATFORM
    # -----------------------------------------------------

    if (
        "Platform" in filtered_df.columns
        and "Feedback_Category" in filtered_df.columns
    ):

        st.markdown("---")

        x = (
            filtered_df
            .groupby(
                [
                    "Platform",
                    "Feedback_Category"
                ]
            )
            .size()
            .reset_index(
                name="Count"
            )
        )

        fig = px.bar(
            x,
            x="Platform",
            y="Count",
            color="Feedback_Category",
            title="Feedback Sentiment by Platform",
            barmode="stack",
            text_auto=".2s"
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )


# =========================================================
# FOOTER
# =========================================================

st.markdown("---")

st.caption(
    "📺 OTT Analytics Dashboard | "
    "Built with Streamlit, Pandas & Plotly"
)
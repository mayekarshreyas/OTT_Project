import streamlit as st
import pandas as pd
import plotly.express as px

# 1. Page Configuration & Theme Setting
st.set_page_config(
    page_title="OTT Dashboard",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling to mimic Power BI Dashboard layout
st.markdown("""
    <style>
    .stMetric {
        background-color: #f8f9fa;
        padding: 15px;
        border-radius: 8px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        text-align: center;
    }
    </style>
""", unsafe_allow_html=True)

# 2. Data Loading & Caching Strategy
@st.cache_data
def load_data(files):
    data = {}
    try:
        data['viewing'] = pd.read_excel(files.get('viewing', 'viewing activity .xlsx'))
        data['user'] = pd.read_excel(files.get('user', 'user profile .xlsx'))
        data['retention'] = pd.read_excel(files.get('retention', 'subscription retention .xlsx'))
        data['ratings'] = pd.read_excel(files.get('ratings', 'ratings feedback .xlsx'))
        data['content'] = pd.read_excel(files.get('content', 'content library .xlsx'))
    except Exception as e:
        st.error(f"Error loading Excel files: {e}")
    return data

# Sidebar Data Ingestion
st.sidebar.title("⚙️ Dashboard Controls")
st.sidebar.subheader("1. Data Sources")

uploaded_files = st.sidebar.file_uploader(
    "Upload Excel Files (Optional)", 
    type=["xlsx", "xls"], 
    accept_multiple_files=True
)

file_map = {}
if uploaded_files:
    for f in uploaded_files:
        if 'viewing' in f.name.lower(): file_map['viewing'] = f
        elif 'user' in f.name.lower(): file_map['user'] = f
        elif 'retention' in f.name.lower(): file_map['retention'] = f
        elif 'ratings' in f.name.lower(): file_map['ratings'] = f
        elif 'content' in f.name.lower(): file_map['content'] = f

data = load_data(file_map)

# Ensure data is populated
if not data:
    st.stop()

# 3. Global Filters Sidebar
st.sidebar.subheader("2. Global Filters")

gender_filter = st.sidebar.multiselect("Gender", options=data['user']['Gender'].dropna().unique(), default=data['user']['Gender'].dropna().unique())
age_filter = st.sidebar.multiselect("Age Group", options=data['user']['Age_Group'].dropna().unique(), default=data['user']['Age_Group'].dropna().unique())
region_filter = st.sidebar.multiselect("Region", options=data['user']['Region'].dropna().unique(), default=data['user']['Region'].dropna().unique())
sub_filter = st.sidebar.multiselect("Subscription Type", options=data['user']['Subscription_Type'].dropna().unique(), default=data['user']['Subscription_Type'].dropna().unique())
platform_filter = st.sidebar.multiselect("Platform", options=data['content']['Platform'].dropna().unique(), default=data['content']['Platform'].dropna().unique())

# Apply Filters
filtered_users = data['user'][
    (data['user']['Gender'].isin(gender_filter)) &
    (data['user']['Age_Group'].isin(age_filter)) &
    (data['user']['Region'].isin(region_filter)) &
    (data['user']['Subscription_Type'].isin(sub_filter))
]

filtered_user_ids = filtered_users['User_ID'].unique()
filtered_viewing = data['viewing'][data['viewing']['User_ID'].isin(filtered_user_ids)]
filtered_retention = data['retention'][data['retention']['User_ID'].isin(filtered_user_ids)]
filtered_ratings = data['ratings'][data['ratings']['User_ID'].isin(filtered_user_ids)]
filtered_content = data['content'][data['content']['Platform'].isin(platform_filter)]

# 4. Tab Navigation (Matching Power BI Pages)
tab1, tab2, tab3, tab4 = st.tabs([
    " Customer Behaviour", 
    " Audience Overview", 
    " Content & Viewing", 
    " Platform Analysis"
])

# ==========================================
# TAB 1: CUSTOMER BEHAVIOUR
# ==========================================
with tab1:
    st.title("Customer Behaviour Dashboard")
    
    # Top KPI Bar
    kpi1, kpi2, kpi3, kpi4, kpi5, kpi6 = st.columns(6)
    kpi1.metric("Total Viewers", f"{filtered_users['User_ID'].nunique():,}")
    kpi2.metric("Viewing Sessions", f"{len(filtered_viewing):,}")
    kpi3.metric("Total Watch Hours", f"{filtered_viewing['Watch_Duration_Minutes'].sum() / 60:,.1f}K")
    kpi4.metric("Avg Watch Duration", f"{filtered_viewing['Watch_Duration_Minutes'].mean():.2f}")
    kpi5.metric("Avg Completion %", f"{filtered_viewing['Completion_Percentage'].mean():.2f}%")
    kpi6.metric("Avg Rating", f"{filtered_ratings['Rating'].mean():.2f}")
    
    st.markdown("---")
    
    # Row 1: Charts
    c1, c2, c3 = st.columns(3)
    
    with c1:
        st.subheader("Watch Duration & Avg Rating by Platform")
        merged_vc = filtered_viewing.merge(data['content'], on='Content_ID', how='inner')
        plat_summary = merged_vc.groupby('Platform').agg(
            Total_Duration=('Watch_Duration_Minutes', 'sum'),
            Avg_Rating=('Numeric_Rating', 'mean')
        ).reset_index()
        
        fig = px.bar(plat_summary, x='Platform', y='Total_Duration', text_auto='.2s', color='Platform')
        fig.add_scatter(x=plat_summary['Platform'], y=plat_summary['Avg_Rating'], mode='lines+markers', name='Avg Rating', yaxis='y2')
        fig.update_layout(yaxis2=dict(overlaying='y', side='right'), showlegend=False, template="plotly_white")
        st.plotly_chart(fig, use_container_width=True)
        
    with c2:
        st.subheader("Churn by Region")
        churn_reg = filtered_retention.merge(filtered_users, on='User_ID').groupby('Region')['Churn_Flag'].mean().reset_index()
        fig_churn = px.line(churn_reg, x='Region', y='Churn_Flag', markers=True, title="Churn Rate per Region")
        fig_churn.update_layout(template="plotly_white")
        st.plotly_chart(fig_churn, use_container_width=True)

    with c3:
        st.subheader("Total Watch Time by Platform")
        fig_wt = px.line(plat_summary, x='Platform', y='Total_Duration', markers=True)
        fig_wt.update_layout(template="plotly_white")
        st.plotly_chart(fig_wt, use_container_width=True)

# ==========================================
# TAB 2: AUDIENCE OVERVIEW
# ==========================================
with tab2:
    st.title("Audience Overview")
    
    col_a, col_b = st.columns(2)
    
    with col_a:
        st.subheader("Top 10 Most Watched Content")
        top_content = filtered_viewing.merge(data['content'], on='Content_ID').groupby('title')['Watch_Duration_Minutes'].sum().reset_index()
        top_content = top_content.sort_values(by='Watch_Duration_Minutes', ascending=False).head(10)
        fig_top = px.bar(top_content, y='title', x='Watch_Duration_Minutes', orientation='h', color='Watch_Duration_Minutes')
        fig_top.update_layout(yaxis={'categoryorder':'total ascending'}, template="plotly_white", showlegend=False)
        st.plotly_chart(fig_top, use_container_width=True)
        
    with col_b:
        st.subheader("Most Popular Genre")
        genre_df = filtered_content.groupby('listed_in')['Popularity_Score'].sum().reset_index().sort_values(by='Popularity_Score', ascending=False).head(10)
        fig_genre = px.bar(genre_df, y='listed_in', x='Popularity_Score', orientation='h')
        fig_genre.update_layout(yaxis={'categoryorder':'total ascending'}, template="plotly_white")
        st.plotly_chart(fig_genre, use_container_width=True)
        
    col_c, col_d = st.columns(2)
    
    with col_c:
        st.subheader("Audience Size vs Completion by Age Group")
        age_summary = filtered_users.merge(filtered_viewing, on='User_ID').groupby('Age_Group').agg(
            User_Count=('User_ID', 'nunique'),
            Avg_Completion=('Completion_Percentage', 'mean')
        ).reset_index()
        fig_age = px.bar(age_summary, x='Age_Group', y='User_Count', color='Age_Group')
        st.plotly_chart(fig_age, use_container_width=True)

    with col_d:
        st.subheader("Audience by Engagement Level")
        eng_summary = filtered_users['Engagement_Level'].value_counts().reset_index()
        fig_donut = px.pie(eng_summary, names='Engagement_Level', values='count', hole=0.5)
        st.plotly_chart(fig_donut, use_container_width=True)

# ==========================================
# TAB 3: CONTENT & VIEWING BEHAVIOUR
# ==========================================
with tab3:
    st.title("Content and Viewing Behaviour")
    
    r1_1, r1_2, r1_3 = st.columns(3)
    
    with r1_1:
        st.subheader("Watch Duration vs Completion")
        fig_scatter = px.scatter(
            filtered_viewing.sample(min(500, len(filtered_viewing))), 
            x='Watch_Duration_Minutes', 
            y='Completion_Percentage',
            color='Device_Type'
        )
        st.plotly_chart(fig_scatter, use_container_width=True)
        
    with r1_2:
        st.subheader("Feedback Category Distribution")
        fb_dist = filtered_ratings['Feedback_Category'].value_counts().reset_index()
        fig_fb = px.pie(fb_dist, names='Feedback_Category', values='count')
        st.plotly_chart(fig_fb, use_container_width=True)

    with r1_3:
        st.subheader("Total Sessions by Rewatched Flag")
        rewatch_df = filtered_viewing['Rewatched_Flag'].value_counts().reset_index()
        fig_rewatch = px.bar(rewatch_df, x='Rewatched_Flag', y='count', color='Rewatched_Flag')
        st.plotly_chart(fig_rewatch, use_container_width=True)

    r2_1, r2_2, r2_3 = st.columns(3)
    
    with r2_1:
        st.subheader("Watch Duration by Device")
        dev_df = filtered_viewing.groupby('Device_Type')['Watch_Duration_Minutes'].sum().reset_index()
        fig_dev = px.bar(dev_df, x='Device_Type', y='Watch_Duration_Minutes')
        st.plotly_chart(fig_dev, use_container_width=True)
        
    with r2_2:
        st.subheader("Viewing by Time of Day")
        tod_df = filtered_viewing.groupby('Time_of_Day')['Session_ID'].count().reset_index()
        fig_tod = px.bar(tod_df, x='Time_of_Day', y='Session_ID')
        st.plotly_chart(fig_tod, use_container_width=True)
        
    with r2_3:
        st.subheader("Churn by Subscription")
        sub_churn = filtered_retention.groupby('Subscription_Type')['Churn_Flag'].mean().reset_index()
        fig_sub_churn = px.bar(sub_churn, x='Subscription_Type', y='Churn_Flag')
        st.plotly_chart(fig_sub_churn, use_container_width=True)

# ==========================================
# TAB 4: PLATFORM ANALYSIS
# ==========================================
with tab4:
    st.title("Platform Analysis")
    
    p1, p2, p3 = st.columns(3)
    
    with p1:
        st.subheader("Top 10 Countries by TV Show Titles")
        country_df = filtered_content[filtered_content['type'] == 'TV Show']['country'].value_counts().head(10).reset_index()
        fig_tree = px.treemap(country_df, path=['country'], values='count')
        st.plotly_chart(fig_tree, use_container_width=True)
        
    with p2:
        st.subheader("Total Watch Time by Platform")
        plat_wt = filtered_viewing.merge(data['content'], on='Content_ID').groupby('Platform')['Watch_Duration_Minutes'].sum().reset_index()
        fig_pwt = px.bar(plat_wt, x='Watch_Duration_Minutes', y='Platform', orientation='h')
        st.plotly_chart(fig_pwt, use_container_width=True)
        
    with p3:
        st.subheader("Churn by Age Group")
        age_churn = filtered_users.merge(filtered_retention, on='User_ID').groupby('Age_Group')['Churn_Flag'].mean().reset_index()
        fig_ac = px.line(age_churn, x='Age_Group', y='Churn_Flag', markers=True)
        st.plotly_chart(fig_ac, use_container_width=True)

    p4, p5, p6 = st.columns(3)
    
    with p4:
        st.subheader("Average Rating by Platform")
        plat_rat = filtered_ratings.merge(data['content'], on='Content_ID').groupby('Platform')['Rating'].mean().reset_index()
        fig_pr = px.bar(plat_rat, x='Platform', y='Rating')
        st.plotly_chart(fig_pr, use_container_width=True)
        
    with p5:
        st.subheader("Feedback Sentiment by Platform")
        plat_fb = filtered_ratings.merge(data['content'], on='Content_ID').groupby(['Platform', 'Feedback_Category']).size().reset_index(name='count')
        fig_pfb = px.bar(plat_fb, x='Platform', y='count', color='Feedback_Category', barmode='stack')
        st.plotly_chart(fig_pfb, use_container_width=True)
        
    with p6:
        st.subheader("Avg Watch Time per Session by Platform")
        plat_session = filtered_viewing.merge(data['content'], on='Content_ID').groupby('Platform')['Watch_Duration_Minutes'].mean().reset_index()
        fig_ps = px.bar(plat_session, x='Watch_Duration_Minutes', y='Platform', orientation='h')
        st.plotly_chart(fig_ps, use_container_width=True)
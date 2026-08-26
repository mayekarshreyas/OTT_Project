# OTT Analytics Case Study

## 📄 Case Study Description
An OTT streaming company has planned to expand its market presence by analyzing user engagement, content preferences, and retention patterns using the provided dataset.

---

## 📊 Data Description

### 1. User Profile Table (`user_profile`)
- **Total Records:** 2000  
- **Columns:**
  - `User_ID` – Unique identifier for each user  
  - `Gender` – Male / Female / Other  
  - `Age_Group` – Age bucket (18–25, 26–35, 36–50, 50+)  
  - `Region` – Geographic region (North, South, East, West, Central)  
  - `Subscription_Type` – Free Trial / Basic / Premium  
  - `Subscription_Start_Date` – Date subscription began  
  - `Subscription_End_Date` – Date subscription ended or renewed  
  - `Device_Type` – Mobile / Smart TV / Laptop / Tablet  
  - `Engagement_Level` – Low / Medium / High (derived later from activity)

---

### 2. Content Library Table (`content_library`)
- **Total Records:** 17,797  
- **Columns:**
  - `show_id` – Unique identifier for content  
  - `type` – Movie / TV Show  
  - `title` – Title of the content  
  - `director`, `cast`, `country` – Metadata fields  
  - `release_year` – Year of release  
  - `rating` – Maturity rating or numeric rating  
  - `duration` – Duration in minutes or seasons  
  - `listed_in` – Genres/categories  
  - `description` – Short synopsis  
  - `Platform` – NetStream / AmazePrime / DizPlay+   
  - **Derived Columns:** `Duration_Minutes`, `Content_Age_Years`, `Numeric_Rating`, `Popularity_Score`, `Engagement_Proxy`, `Is_Recent`, `Genre_Count`

---

### 3. Viewing Activity Table (`viewing_activity`)
- **Total Records:** 30,000  
- **Columns:**
  - `Session_ID` – Unique viewing session identifier  
  - `User_ID` – Links to User Profile  
  - `Content_ID` – Links to Content Library  
  - `View_Date` – Date of viewing  
  - `Watch_Duration_Minutes` – Minutes watched  
  - `Completion_Percentage` – % of content completed  
  - `Paused_Times` – Number of pauses during session  
  - `Rewatched_Flag` – Y/N if rewatched  
  - `Time_of_Day` – Morning / Afternoon / Evening / Night  
  - `Device_Type` – Device used for viewing

---

### 4. Subscription & Retention Table (`subscription_retention`)
- **Total Records:** 2000  
- **Columns:**
  - `User_ID` – Links to User Profile  
  - `Subscription_Type` – Free Trial / Basic / Premium  
  - `Monthly_Fee` – Fee charged per month  
  - `Renewal_Status` – Renewed / Not Renewed  
  - `Churn_Flag` – 1 if churned, 0 if retained

---

### 5. Ratings & Feedback Table (`ratings_feedback`)
- **Total Records:** 12,000  
- **Columns:**
  - `User_ID` – Links to User Profile  
  - `Content_ID` – Links to Content Library  
  - `Rating` – User rating (1–5 scale)  
  - `Liked_Flag` – Y/N if liked  
  - `Feedback_Category` – Positive / Neutral / Negative sentiment

---

## 🎯 Usage
This dataset can be used to:
- Analyze **content trends** (genres, platforms, release years).  
- Study **user behavior** (age groups, regions, devices, time-of-day viewing).  
- Model **engagement and retention** (completion %, rewatch, churn).  
- Explore **feedback correlations** (ratings vs. engagement).
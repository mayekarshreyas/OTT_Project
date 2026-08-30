use ott_db;

# Create a customer-level analytical view.
# The user and subscription information are combined with aggregated
# viewing and feedback information.
# Viewing activity is aggregated separately by User_ID to calculate
# sessions, watch time, completion, pauses and rewatching.
# Feedback is also aggregated separately by User_ID to calculate
# average rating and total likes.
# Aggregating first prevents many-to-many JOIN multiplication.
CREATE VIEW user_engagement AS

SELECT
    u.User_ID,
    u.Gender,
    u.Age_Group,
    u.Region,
    u.Subscription_Type,

    s.Monthly_Fee,
    s.Renewal_Status,
    s.Churn_Flag,

    COALESCE(v.Total_Sessions, 0) AS Total_Sessions,
    COALESCE(v.Total_Watch_Minutes, 0) AS Total_Watch_Minutes,
    COALESCE(v.Avg_Completion_Percentage, 0) AS Avg_Completion_Percentage,
    COALESCE(v.Total_Pauses, 0) AS Total_Pauses,
    COALESCE(v.Rewatched_Sessions, 0) AS Rewatched_Sessions,

    COALESCE(r.Avg_Rating, 0) AS Avg_Rating,
    COALESCE(r.Total_Likes, 0) AS Total_Likes

FROM user_profile u

LEFT JOIN subscription_retention s
    ON u.User_ID = s.User_ID

LEFT JOIN
(
    SELECT
        User_ID,

        COUNT(Session_ID) AS Total_Sessions,

        SUM(Watch_Duration_Minutes) AS Total_Watch_Minutes,

        AVG(Completion_Percentage) AS Avg_Completion_Percentage,

        SUM(Paused_Times) AS Total_Pauses,

        SUM(
            CASE
                WHEN Rewatched_Flag = 'Y' THEN 1
                ELSE 0
            END
        ) AS Rewatched_Sessions

    FROM viewing_activity
    GROUP BY User_ID
) v
    ON u.User_ID = v.User_ID

LEFT JOIN
(
    SELECT
        User_ID,

        AVG(Rating) AS Avg_Rating,

        SUM(
            CASE
                WHEN Liked_Flag = 'Y' THEN 1
                ELSE 0
            END
        ) AS Total_Likes

    FROM ratings_feedback
    GROUP BY User_ID
) r
    ON u.User_ID = r.User_ID;
    


# Calculate the percentage of users who have churned.
# Churn_Flag = 1 represents a churned user.
# This gives us an overall view of customer retention performance.
SELECT
    ROUND(
        100.0 * SUM(Churn_Flag) / COUNT(*),
        2
    ) AS Churn_Rate
FROM user_engagement;
    
   
# Calculate the percentage of users whose subscription status is Renewed.
# This measures how successfully the platform retains subscribers.
SELECT
    ROUND(
        100.0 *
        SUM(
            CASE
                WHEN Renewal_Status = 'Renewed' THEN 1
                ELSE 0
            END
        ) / COUNT(*),
        2
    ) AS Renewal_Rate
FROM user_engagement;


# Calculate the average total watch time per user.
# This provides an overall measure of user engagement.
SELECT
    ROUND(AVG(Total_Watch_Minutes), 2) AS Avg_Watch_Minutes
FROM user_engagement;


# Calculate the average content completion percentage.
# This shows how much of the content users typically watch.
SELECT
    ROUND(AVG(Avg_Completion_Percentage), 2) AS Avg_Completion
FROM user_engagement;


# Compare churn across subscription types.
# We calculate total users, churned users and churn rate for each plan.
# This can identify which subscription type has the highest retention problem.
SELECT
    Subscription_Type,
    COUNT(*) AS Users,
    SUM(Churn_Flag) AS Churned_Users,
    ROUND(
        100.0 * SUM(Churn_Flag) / COUNT(*),
        2
    ) AS Churn_Rate
FROM user_engagement
GROUP BY Subscription_Type
ORDER BY Churn_Rate DESC;


# Compare engagement metrics between churned and non-churned users.
# This helps determine whether watch time, sessions, completion
# and rewatching behavior are associated with customer retention.
SELECT
    Churn_Flag,
    COUNT(*) AS Users,

    ROUND(
        AVG(Total_Watch_Minutes), 2
    ) AS Avg_Watch_Minutes,

    ROUND(
        AVG(Total_Sessions), 2
    ) AS Avg_Sessions,

    ROUND(
        AVG(Avg_Completion_Percentage), 2
    ) AS Avg_Completion,

    ROUND(
        AVG(Rewatched_Sessions), 2
    ) AS Avg_Rewatched_Sessions

FROM user_engagement
GROUP BY Churn_Flag;


# Compare churn rates across age groups.
# This helps identify demographic segments with higher retention risk.
SELECT
    Age_Group,
    COUNT(*) AS Users,
    SUM(Churn_Flag) AS Churned_Users,
    ROUND(
        100.0 * SUM(Churn_Flag) / COUNT(*),
        2
    ) AS Churn_Rate
FROM user_engagement
GROUP BY Age_Group
ORDER BY Churn_Rate DESC;


# Compare churn rates across genders.
# This helps determine whether retention differs between demographic groups.
SELECT
    Gender,
    COUNT(*) AS Users,
    SUM(Churn_Flag) AS Churned_Users,
    ROUND(
        100.0 * SUM(Churn_Flag) / COUNT(*),
        2
    ) AS Churn_Rate
FROM user_engagement
GROUP BY Gender
ORDER BY Churn_Rate DESC;


# Compare churn rates across regions.
# This identifies geographic areas with relatively higher churn.
SELECT
    Region,
    COUNT(*) AS Users,
    SUM(Churn_Flag) AS Churned_Users,
    ROUND(
        100.0 * SUM(Churn_Flag) / COUNT(*),
        2
    ) AS Churn_Rate
FROM user_engagement
GROUP BY Region
ORDER BY Churn_Rate DESC;


# Identify users with paid subscriptions and the highest total watch time.
# This helps identify highly engaged customers who may represent
# valuable customer segments.
SELECT
    User_ID,
    Subscription_Type,
    Monthly_Fee,
    Total_Watch_Minutes,
    Total_Sessions,
    Avg_Completion_Percentage,
    Avg_Rating,
    Churn_Flag
FROM user_engagement
WHERE Monthly_Fee > 0
ORDER BY Total_Watch_Minutes DESC
LIMIT 20;


# Identify users with relatively low watch time and low completion.
# This creates a simple rule-based engagement-risk segment.
# It is NOT a machine-learning churn prediction model.
SELECT
    User_ID,
    Subscription_Type,
    Total_Watch_Minutes,
    Total_Sessions,
    Avg_Completion_Percentage,
    Monthly_Fee,
    Churn_Flag
FROM user_engagement
WHERE
    Total_Watch_Minutes < 100
    AND Avg_Completion_Percentage < 40
ORDER BY Total_Watch_Minutes;


# Compare viewing behavior across device types.
# We measure the number of sessions, average watch duration
# and average completion percentage for each device.
SELECT
    Device_Type,
    COUNT(*) AS Sessions,
    ROUND(
        AVG(Watch_Duration_Minutes), 2
    ) AS Avg_Watch_Duration,
    ROUND(
        AVG(Completion_Percentage), 2
    ) AS Avg_Completion
FROM viewing_activity
GROUP BY Device_Type
ORDER BY Avg_Watch_Duration DESC;


# Compare viewing behavior across different times of day.
# This identifies periods when users watch longer and complete
# a higher percentage of content.
SELECT
    Time_of_Day,
    COUNT(*) AS Sessions,
    ROUND(
        AVG(Watch_Duration_Minutes), 2
    ) AS Avg_Watch_Duration,
    ROUND(
        AVG(Completion_Percentage), 2
    ) AS Avg_Completion
FROM viewing_activity
GROUP BY Time_of_Day
ORDER BY Avg_Watch_Duration DESC;


# Compare sessions that were rewatched with sessions that were not.
# This helps understand whether rewatching is associated with
# longer viewing duration or higher completion.

SELECT
    Rewatched_Flag,
    COUNT(*) AS Sessions,
    ROUND(
        AVG(Watch_Duration_Minutes), 2
    ) AS Avg_Watch_Duration,
    ROUND(
        AVG(Completion_Percentage), 2
    ) AS Avg_Completion
FROM viewing_activity
GROUP BY Rewatched_Flag;


# Count rewatched sessions across different times of day.
# This identifies when users are most likely to rewatch content.

SELECT
    Time_of_Day,
    COUNT(*) AS Rewatched_Sessions
FROM viewing_activity
WHERE Rewatched_Flag = 'Y'
GROUP BY Time_of_Day
ORDER BY Rewatched_Sessions DESC;


# Compare average pauses and completion across different times of day.
# This helps investigate whether interruption behavior is associated
# with lower or higher content completion.
SELECT
    Time_of_Day,
    ROUND(
        AVG(Paused_Times), 2
    ) AS Avg_Pauses,
    ROUND(
        AVG(Completion_Percentage), 2
    ) AS Avg_Completion
FROM viewing_activity
GROUP BY Time_of_Day
ORDER BY Avg_Pauses DESC;


# Count how many feedback records exist for each rating.
# This shows the overall distribution of user ratings.
SELECT
    Rating,
    COUNT(*) AS Rating_Count
FROM ratings_feedback
GROUP BY Rating
ORDER BY Rating;# Count how many feedback records exist for each rating.
# This shows the overall distribution of user ratings.



# Count feedback records by feedback category.
# This identifies the most common types of user feedback.
SELECT
    Feedback_Category,
    COUNT(*) AS Feedback_Count
FROM ratings_feedback
GROUP BY Feedback_Category
ORDER BY Feedback_Count DESC;


# Compare total feedback and likes within each feedback category.
# This helps identify categories associated with positive user reactions.
SELECT
    Feedback_Category,
    COUNT(*) AS Total_Feedback,
    SUM(
        CASE
            WHEN Liked_Flag = 'Y' THEN 1
            ELSE 0
        END
    ) AS Likes
FROM ratings_feedback
GROUP BY Feedback_Category
ORDER BY Likes DESC;



# Join viewing_activity with ratings_feedback using their common Content_ID.
# This combines viewing behavior with user feedback for the same content.
# We will calculate the number of views, average watch duration,
# average completion, average rating and number of likes.
#
# This gives us a useful business view of content engagement
# and audience feedback without forcing an invalid JOIN to content_library.

SELECT
    v.Content_ID,
    COUNT(v.Session_ID) AS Total_Views,
    ROUND(AVG(v.Watch_Duration_Minutes), 2) AS Avg_Watch_Duration,
    ROUND(AVG(v.Completion_Percentage), 2) AS Avg_Completion,
    ROUND(AVG(r.Rating), 2) AS Avg_Rating,
    SUM(
        CASE
            WHEN r.Liked_Flag = 'Y' THEN 1
            ELSE 0
        END
    ) AS Total_Likes

FROM viewing_activity v

INNER JOIN ratings_feedback r
    ON v.Content_ID = r.Content_ID

GROUP BY v.Content_ID

ORDER BY Total_Views DESC;


# Join user_profile with subscription_retention using User_ID.
# This combines customer demographic information with subscription
# and churn information.
# We will use this relationship for our customer-retention analysis.

SELECT
    u.User_ID,
    u.Gender,
    u.Age_Group,
    u.Region,
    u.Subscription_Type,
    s.Monthly_Fee,
    s.Renewal_Status,
    s.Churn_Flag
FROM user_profile u
INNER JOIN subscription_retention s
    ON u.User_ID = s.User_ID
LIMIT 20;


# Compare subscription types based on total users,
# number of churned users, and churn rate.
# This helps identify which subscription type has the
# biggest customer-retention problem.

SELECT
    Subscription_Type,
    COUNT(*) AS Total_Users,
    SUM(Churn_Flag) AS Churned_Users,
    ROUND(
        100.0 * SUM(Churn_Flag) / COUNT(*),
        2
    ) AS Churn_Rate
FROM subscription_retention
GROUP BY Subscription_Type
ORDER BY Churn_Rate DESC;



# Identify users whose total watch time is greater than
# the average watch time of all users.
# The inner query calculates the overall average watch time.
# The outer query finds users above that benchmark.
# This demonstrates the use of a subquery.

SELECT
    User_ID,
    Subscription_Type,
    Total_Watch_Minutes,
    Avg_Completion_Percentage,
    Churn_Flag
FROM user_engagement
WHERE Total_Watch_Minutes >
(
    SELECT AVG(Total_Watch_Minutes)
    FROM user_engagement
)
ORDER BY Total_Watch_Minutes DESC;


# Identify churned users whose watch time is below
# the average watch time of all users.
# The subquery calculates the overall average.
# This helps identify churned users with relatively low engagement.

SELECT
    User_ID,
    Subscription_Type,
    Total_Watch_Minutes,
    Avg_Completion_Percentage,
    Churn_Flag
FROM user_engagement
WHERE Churn_Flag = 1
  AND Total_Watch_Minutes <
(
    SELECT AVG(Total_Watch_Minutes)
    FROM user_engagement
)
ORDER BY Total_Watch_Minutes;


# Create a derived table containing user counts and churned users
# for each subscription type.
# The outer query then calculates the churn rate from that derived table.
# This demonstrates a derived table using a subquery in the FROM clause.

SELECT
    Subscription_Type,
    Total_Users,
    Churned_Users,
    ROUND(
        100.0 * Churned_Users / Total_Users,
        2
    ) AS Churn_Rate
FROM
(
    SELECT
        Subscription_Type,
        COUNT(*) AS Total_Users,
        SUM(Churn_Flag) AS Churned_Users
    FROM subscription_retention
    GROUP BY Subscription_Type
) AS subscription_summary
ORDER BY Churn_Rate DESC;


# Create a derived table that calculates average engagement
# for each churn status.
# The outer query classifies the engagement level based on
# the average watch time.
# This demonstrates derived-table analysis.

SELECT
    Churn_Flag,
    Users,
    Avg_Watch_Minutes,
    CASE
        WHEN Avg_Watch_Minutes >= 300 THEN 'High Engagement'
        WHEN Avg_Watch_Minutes >= 150 THEN 'Medium Engagement'
        ELSE 'Low Engagement'
    END AS Engagement_Segment
FROM
(
    SELECT
        Churn_Flag,
        COUNT(*) AS Users,
        ROUND(AVG(Total_Watch_Minutes), 2) AS Avg_Watch_Minutes
    FROM user_engagement
    GROUP BY Churn_Flag
) AS engagement_summary;


# Create a stored procedure that returns engagement information
# for a specific user.
# The input parameter allows us to reuse the same analysis
# for different User_ID values without rewriting the query.

DELIMITER //

CREATE PROCEDURE GetCustomerEngagement(IN p_User_ID VARCHAR(50))
BEGIN

    SELECT
        User_ID,
        Subscription_Type,
        Monthly_Fee,
        Renewal_Status,
        Churn_Flag,
        Total_Sessions,
        Total_Watch_Minutes,
        Avg_Completion_Percentage,
        Total_Pauses,
        Rewatched_Sessions,
        Avg_Rating,
        Total_Likes
    FROM user_engagement
    WHERE User_ID = p_User_ID;

END //

DELIMITER ;




# Create a stored procedure that checks whether a User_ID exists
# before returning customer information.
# If the User_ID does not exist, the procedure raises an error
# instead of silently returning an empty result.
#
# This demonstrates exception/error handling in a stored procedure.

DELIMITER //

CREATE PROCEDURE GetCustomerEngagementSafe(IN p_User_ID VARCHAR(50))
BEGIN

    DECLARE user_count INT DEFAULT 0;

    SELECT COUNT(*)
    INTO user_count
    FROM user_engagement
    WHERE User_ID = p_User_ID;

    IF user_count = 0 THEN

        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'User_ID does not exist';

    ELSE

        SELECT
            User_ID,
            Subscription_Type,
            Monthly_Fee,
            Renewal_Status,
            Churn_Flag,
            Total_Sessions,
            Total_Watch_Minutes,
            Avg_Completion_Percentage,
            Total_Pauses,
            Rewatched_Sessions,
            Avg_Rating,
            Total_Likes
        FROM user_engagement
        WHERE User_ID = p_User_ID;

    END IF;

END //

DELIMITER ;



# Create a reusable view summarizing customer performance
# by subscription type.
# This makes subscription-level retention metrics available
# without rewriting the aggregation query each time.

CREATE VIEW subscription_summary AS

SELECT
    Subscription_Type,
    COUNT(*) AS Total_Users,
    SUM(Churn_Flag) AS Churned_Users,

    ROUND(
        100.0 * SUM(Churn_Flag) / COUNT(*),
        2
    ) AS Churn_Rate,

    ROUND(
        AVG(Total_Watch_Minutes),
        2
    ) AS Avg_Watch_Minutes,

    ROUND(
        AVG(Avg_Completion_Percentage),
        2
    ) AS Avg_Completion

FROM user_engagement

GROUP BY Subscription_Type;


# Display the subscription summary view.
# This verifies that the view was created successfully
# and provides a reusable subscription-level analysis.

SELECT *
FROM subscription_summary
ORDER BY Churn_Rate DESC;

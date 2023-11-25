'''
Dashboard
To run the file, use the command: streamlit run dashboard.py
'''

import os
import re
from datetime import datetime

import altair as alt
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import streamlit as st


def getBrand(filePath):
    pattern = r"(\w+)_[tweets|mentioned]"
    matches = re.search(pattern, filePath)

    if matches:
        return matches.group(1)
    raise ValueError(f"No brand found in the filePath '{filePath}'")

def getSinceUntilDate(filePath):
    # Extract the dates using regular expressions
    pattern = r"from_(\d{4}-\d{2}-\d{2})_to_(\d{4}-\d{2}-\d{2})"
    matches = re.search(pattern, filePath)

    if matches:
        since = datetime.strptime(matches.group(1), "%Y-%m-%d")
        until = datetime.strptime(matches.group(2), "%Y-%m-%d")
        return since, until
    else:
        raise ValueError(f"No dates found in the filePath '{filePath}'")

def getAvgPositiveSentimentScore(df):
    df = df[["pred"]]
    average = int(df[df["pred"] == 2].count() / df.count() * 100)
    return average

def getTweetImpression(df):
    totalTweets = df.shape[0]
    totalViews = df["viewCount"].sum()
    avgViewsPerTweet = round(totalViews / totalTweets, 2)
    return avgViewsPerTweet

def getNumTweetsPerDay(df, since, until):
    totalDays =  (until - since).days
    totalTweets = df.shape[0]
    numTweetsPerDay = round(totalTweets / totalDays, 2)
    return numTweetsPerDay

def getAvgEngagementRatePerTweetByFollowers(df, totalFollowers):
    totalLikes = df["likeCount"].sum()
    totalRetweets = df["retweetCount"].sum()
    totalTweets = df.shape[0]
    avgEngagementRate = round(((totalLikes + totalRetweets) / totalTweets) / totalFollowers, 2) * 100
    return avgEngagementRate

def getAvgMentionedPerDay(df, since, until):
    totalDays =  (until - since).days
    totalMentioned = df.shape[0]
    numMentionedPerDay = round(totalMentioned / totalDays, 2)
    return numMentionedPerDay

def getMetrics(predPath, tweetPath, mentionedPath, totalFollowers):
    dfPred = pd.read_csv(predPath)
    dfTweets = pd.read_csv(tweetPath)
    dfTweets["date"] = pd.to_datetime(dfTweets["date"]).dt.date # convert date to datetime object
    sinceT, untilT  = getSinceUntilDate(tweetPath) # get start and end date
    dfMentioned = pd.read_csv(mentionedPath)
    dfMentioned["date"] = pd.to_datetime(dfMentioned["date"]).dt.date # convert date to datetime object
    sinceM, untilM  = getSinceUntilDate(mentionedPath) # get start and end date

    return [
        getBrand(tweetPath),
        getAvgPositiveSentimentScore(dfPred),
        getTweetImpression(dfTweets),
        getNumTweetsPerDay(dfTweets, sinceT, untilT),
        getAvgEngagementRatePerTweetByFollowers(dfTweets, totalFollowers),
        getAvgMentionedPerDay(dfMentioned, sinceM, untilM)]

def plotGraph(df, column, title=None, showLegend=False):
    brandColors = ["#be332e", "#db6e35", "#1e4a7e", "#2d2f3e", "#32717b"]

    if title is None:
        title = f"{column} by Brand"
    if showLegend:
        legend = alt.Legend(title="Brand", orient="top", labelFontSize=12, titleFontSize=14)
    else:
        legend = None

    chart = alt.Chart(df).mark_bar().encode(
        x="Brand",
        y=column,
        color=alt.Color("Brand", scale=alt.Scale(range=brandColors), legend=legend),
        tooltip=[alt.Tooltip('Brand:N'), alt.Tooltip(column + ':Q', format='.2f')]
    ).properties(
        width=400,
        height=400,
        title=alt.TitleParams(title)
    )

    st.altair_chart(chart, use_container_width=False)

def main():
    predPaths = [
        "./Datasets/SA_Pred/cc_pred.csv",
        "./Datasets/SA_Pred/fanta_pred.csv",
        "./Datasets/SA_Pred/pepsi_pred.csv",
        "./Datasets/SA_Pred/ph_pred.csv",
        "./Datasets/SA_Pred/sprite_pred.csv",
    ]

    tweetPaths = [
        "./Datasets/Tweets/CocaCola_tweets_from_2022-06-01_to_2023-05-31.csv",
        "./Datasets/Tweets/Fanta_tweets_from_2022-06-01_to_2023-05-31.csv",
        "./Datasets/Tweets/Pepsi_tweets_from_2022-06-01_to_2023-05-31.csv",
        "./Datasets/Tweets/PrimeHydrate_tweets_from_2022-06-01_to_2023-05-31.csv",
        "./Datasets/Tweets/Sprite_tweets_from_2022-06-01_to_2023-05-31.csv"
    ]

    mentionedPaths = [
        "./Datasets/Mentioned/CocaCola_mentioned_from_2023-05-01_to_2023-05-31.csv",
        "./Datasets/Mentioned/Fanta_mentioned_from_2023-05-01_to_2023-05-31.csv",
        "./Datasets/Mentioned/Pepsi_mentioned_from_2023-05-01_to_2023-05-31.csv",
        "./Datasets/Mentioned/PrimeHydrate_mentioned_from_2023-05-01_to_2023-05-31.csv",
        "./Datasets/Mentioned/Sprite_mentioned_from_2023-05-01_to_2023-05-31.csv"
    ]

    # Collected manually from Social Blade as of 30 June
    totalFollowersList = [
        3371668, # cola
        156346, # fanta
        3085508, # pepsi
        391154, # prime
        299037 # sprite
    ]

    st.set_page_config(
        page_title="Soft Drinks: Twitter Analytics",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    allMetrics = []
    for i in range(5):
        metrics = getMetrics(predPaths[i], tweetPaths[i], mentionedPaths[i], totalFollowersList[i])
        allMetrics.append(metrics)

    dfMetrics = pd.DataFrame(allMetrics, columns=["Brand", "Average Positive Sentiment Score (%)", "Tweet Impression", "Tweeting Frequency", "Average Engagement Rate (%)", "Daily Brand Mentioned"])
    dfMetrics.loc[dfMetrics["Brand"].str.lower() == "primehydrate", "Brand"] = "Prime"
    dfMetrics["Brand"] = dfMetrics["Brand"].str.title()

    st.title("Soft Drinks: Twitter Analytics")

    # Plot graphs for each metrics
    c1, c2 = st.columns(2, gap="large")
    with c1:
        plotGraph(dfMetrics, "Average Positive Sentiment Score (%)", showLegend=True)
    with c2:
        plotGraph(dfMetrics, "Tweet Impression")

    c1, c2, c3 = st.columns(3, gap="large")
    with c1:
        plotGraph(dfMetrics, "Tweeting Frequency")
    with c2:
        plotGraph(dfMetrics, "Average Engagement Rate (%)")
    with c3:
        plotGraph(dfMetrics, "Daily Brand Mentioned", "Daily Brand Mentioned")

if __name__ == "__main__":
    main()
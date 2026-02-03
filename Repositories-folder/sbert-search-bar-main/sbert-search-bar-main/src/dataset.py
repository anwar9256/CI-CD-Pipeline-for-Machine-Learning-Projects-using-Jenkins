# import libraries
import pandas as pd

# 1. Project Description Data
def get_project_description():
    """
    Retrieves project description data from local CSV file.
    """
    try:
        project_description = pd.read_csv("data/project_description.csv")
        return project_description
    except Exception as e:
        print("Error loading project_description.csv:", e)


# 2. Video Titles Data
def get_video_titles():
    """
    Retrieves video titles data from local CSV file.
    """
    try:
        project_topics = pd.read_csv("data/project_topics.csv")
        return project_topics
    except Exception as e:
        print("Error loading project_topics.csv:", e)


# 3. Abbreviations Data
def get_abbreviations():
    """
    Retrieves abbreviations data from local Excel file.
    """
    try:
        Abbreviations = pd.read_excel("data/Abbreviations.xlsx")
        return Abbreviations
    except Exception as e:
        print("Error loading Abbreviations.xlsx:", e)

# Import Python libraries and packages
import pandas as pd
import numpy as np
import streamlit as st

# Import Matplotlib - will help us draw the shot charts and display data on them
import matplotlib as mpl
import matplotlib.pyplot as plt

from matplotlib import cm 
from matplotlib.patches import Rectangle, Circle, Arc, ConnectionPatch
from matplotlib.patches import Polygon
from matplotlib.patches import PathPatch
from matplotlib.collections import PatchCollection
from matplotlib.colors import LinearSegmentedColormap, ListedColormap, BoundaryNorm
from matplotlib.path import Path
from PIL import Image

import mpld3
import plotly.express as px

import sys
import json 
import requests

# Import data from NBA api
from nba_api.stats.static import players
from nba_api.stats.static import teams
from nba_api.stats.endpoints import shotchartdetail
from nba_api.stats.endpoints import teamdashboardbyyearoveryear

#------------------------------------------------------------------------------------------------------

# Configure Streamlit app where the dashboard will be presented
# Page title & icon 
st.set_page_config(page_title='NBA ShotChart Dashboard', # ref: https://discuss.streamlit.io/t/fav-icon-title-customization/10662/2
                   page_icon=':basketball:')
# Title
st.title('Welcome to the NBA ShotChart Dashboard', anchor=None)

#------------------------------------------------------------------------------------------------------

# Get the required data from the NBA api, give the user a list of options,
# build the JSON shot chart response around the user's input
def get_shotchartdetail(team_id, season, seasontype):

    # Get all NBA teams & players
    nba_teams = teams.get_teams()
    nba_players = players.get_players()

    # Create dictionary for team full name and team id
    teamIdLookup = {team['full_name']: team['id'] for team in nba_teams}
    # Create list of team names
    teamList = list(teamIdLookup.keys())

    # Create a list of seasons to choose from
    seasons = ['2022-23', '2021-22', '2020-21', '2019-20', '2018-19',
               '2017-18', '2016-17', '2015-16', '2014-15', '2013-14',
               '2012-13', '2011-12', '2010-11', '2009-10', '2008-09',
               '2007-08', '2006-07', '2005-06', '2004-05', '2003-04',
               '2002-03', '2001-02', '2000-01', '1999-00', '1998-99',
               '1997-98', '1996-97']
    
    # Add season types
    seasontypes = ['Regular Season', 'Playoffs']

    # Allow user to select a team
    selected_team = st.sidebar.selectbox('Select a team: ', teamList)
    team_id = teamIdLookup.get(selected_team)

    # Allow user to select a season
    season = st.sidebar.selectbox("Select season: ", seasons)
    
    # Allow user to select a season type
    seasontype = st.sidebar.selectbox('Select season type: ', seasontypes)

    # API to get team dashboard info on shooting splits info, to show for each shotchart for a team the user selects
    teamstats = teamdashboardbyyearoveryear.TeamDashboardByYearOverYear(team_id=int(team_id),
                                                                        season=season,
                                                                        season_type_all_star=seasontype)
    teamstats_df = teamstats.get_data_frames()[0]

    # Select the columns we want to show
    selectedteamstats_df = teamstats_df[["FG_PCT", "FG3_PCT", "FT_PCT"]]
    # Rename the columns
    finalteamstats_df = selectedteamstats_df.rename(columns={'FG_PCT': 'FG %', 'FG3_PCT': '3PT %', 'FT_PCT': 'FT %'})
    # Change decimal to percentage: Field-goal percentages
    finalteamstats_df['FG %'] = finalteamstats_df['FG %'].apply(lambda x: '{:.1%}'.format(x))
    # Change decimal to percentage: Three-point field goal percentages
    finalteamstats_df['3PT %'] = finalteamstats_df['3PT %'].apply(lambda x: '{:.1%}'.format(x))
    # Change decimal to percentage: Free-throw percentages
    finalteamstats_df['FT %'] = finalteamstats_df['FT %'].apply(lambda x: '{:.1%}'.format(x))

    # Calling the same API to get team season info for a team user selects
    teaminfo = teamdashboardbyyearoveryear.TeamDashboardByYearOverYear(team_id=int(team_id),
                                                                        season=season,
                                                                        season_type_all_star=seasontype)

    teaminfo_df = teaminfo.get_data_frames()[0]

    # Select the columns we want to show
    selectedteaminfo_df = teaminfo_df[["W", "L", "W_PCT"]]
    # Rename the columns
    finalteaminfo_df = selectedteaminfo_df.rename(columns={'W': 'Wins', 'L': 'Losses', 'W_PCT': 'Win %'})
    # Change decimal to percentage: Win percentages
    finalteaminfo_df['Win %'] = finalteaminfo_df['Win %'].apply(lambda x: '{:.0%}'.format(x))

    # JSON shotchart response to obtain team shot chart data, based on user input
    json_shotchart = shotchartdetail.ShotChartDetail(team_id=int(team_id), 
                                                        player_id=0,
                                                        season_type_all_star= seasontype,
                                                        season_nullable= season,
                                                        context_measure_simple="FGA").get_data_frames()                                   
    
    # Label to inform user of their selections
    st.write('You selected Shot Chart data for:')
    st.write(selected_team + ', ' + season + ' - ' + seasontype)
    st.sidebar.subheader('Team Shooting Splits')
    st.sidebar.write(finalteamstats_df)
    st.sidebar.subheader(seasontype + ' Record')
    st.sidebar.write(finalteaminfo_df)

    # Return shotchart
    return json_shotchart[0], json_shotchart[1]

#------------------------------------------------------------------------------------------------------

# Create all various parts of an NBA basketball court
# Ref: https://github.com/savvastj/nbashots/blob/master/nbashots/charts.py
def draw_court(ax=None, color="blue", lw=1, outer_lines=False):

    if ax is None:
        ax = plt.gca()

    # Basket/Hoop
    hoop = Circle((0,0), radius=7.5, linewidth=lw, color=color, fill=False)

    # Backboard
    backboard = Rectangle((-30, -12.5), 60, 0, linewidth=lw, color=color)

    # The paint (outer and inner Box)
    # Outer box
    outer_box = Rectangle((-80, -47.5), 160, 190, linewidth=lw, color=color, fill=False)
    # Inner box
    inner_box = Rectangle((-60, -47.5), 120, 190, linewidth=lw, color=color, fill=False)

    # Free-throw arcs (top and bottom)
    # FT top arc
    top_free_throw = Arc((0, 142.5), 120, 120, theta1=0, theta2=180, linewidth=lw, color=color, fill=False)
    # FT bottom arc
    bottom_free_throw = Arc((0, 142.5), 120, 120, theta1=180, theta2=0, linewidth=lw, color=color)

    # Restricted area
    restricted = Arc((0, 0), 80, 80, theta1=0, theta2=180, linewidth=lw, color=color)

    # Three-point line
    corner_three_a = Rectangle((-220, -47.5), 0, 140, linewidth=lw, color=color)
    corner_three_b = Rectangle((220, -47.5), 0, 140, linewidth=lw, color=color)
    three_arc = Arc((0, 0), 475, 475, theta1=22, theta2=158, linewidth=lw, color=color)

    # Center court
    center_outer_arc = Arc((0, 422.5), 120, 120, theta1=180, theta2=0, linewidth=lw, color=color)
    center_inner_arc = Arc((0, 422.5), 40, 40, theta1=180, theta2=0, linewidth=lw, color=color)

    # List of court elements
    court_elements = [hoop, backboard, outer_box, inner_box, top_free_throw, bottom_free_throw, restricted, corner_three_a, corner_three_b, three_arc, center_outer_arc, center_inner_arc]

    # Outer_lines = True
    if outer_lines:
        outer_lines = Rectangle((-250, -47.5), 500, 470, linewidth=lw, color=color, fill=False)
        court_elements.append(outer_lines)

    for element in court_elements:
        ax.add_patch(element)

#------------------------------------------------------------------------------------------------------

# Shot chart function: plots every attempted shot (made/missed) from the selected shot chart on the basketball court
# Ref: https://github.com/savvastj/nbashots/blob/master/nbashots/charts.py
def shot_chart(data, title="", color="b", xlim=(-250, 250), ylim=(422.5, -47.5), line_color="black",
               court_color="white", court_lw=2, outer_lines=False,
               flip_court=False, gridsize=None,
               ax=None, despine=False):

    if ax is None:
        ax = plt.gca()

    if not flip_court:
        ax.set_xlim(xlim)
        ax.set_ylim(ylim)
    else:
        ax.set_xlim(xlim[::-1])
        ax.set_ylim(ylim[::-1])

    ax.tick_params(labelbottom="off", labelleft="off")
    ax.set_title(title, fontsize=18, fontweight="bold")
    
    # Draw the court using the draw_court()
    draw_court(ax, color=line_color, lw=court_lw, outer_lines=outer_lines)

    # Distinquish colours for made and missed shots
    # Missed shots
    x_missed = data[data['EVENT_TYPE'] == 'Missed Shot']['LOC_X']
    y_missed = data[data['EVENT_TYPE'] == 'Missed Shot']['LOC_Y']
    # Made shots
    x_made = data[data['EVENT_TYPE'] == 'Made Shot']['LOC_X']
    y_made = data[data['EVENT_TYPE'] == 'Made Shot']['LOC_Y']

    # Plot missed shots
    ax.scatter(x_missed, y_missed, c='darkred', marker="x", s=300, linewidths=3)
    # Plot made shots
    ax.scatter(x_made, y_made, facecolors='none', edgecolors='limegreen', marker='o', s=100, linewidths=3)
    
    # Set the spines to match the rest of court lines, makes outer_lines
    for spine in ax.spines:
        ax.spines[spine].set_lw(court_lw)
        ax.spines[spine].set_color(line_color)

    if despine:
        ax.spines["top"].set_visible(False)
        ax.spines["bottom"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.spines["left"].set_visible(False)

    return ax

#------------------------------------------------------------------------------------------------------

# Display the shot chart
if __name__ == "__main__":

# Get arguments
    if (len(sys.argv) == 1):
        team_id = get_shotchartdetail
        season =  get_shotchartdetail
        seasontype = get_shotchartdetail
    else:
        team_id = sys.argv[1]
        season = sys.argv[2]
        seasontype = sys.argv[3]

    # Set size for shot chart figure
    plt.rcParams['figure.figsize'] = (12, 11)

    # Retrieve the shot data & plot shot chart
    player_shotchart_df, league_avg = get_shotchartdetail(team_id, season, seasontype)
    shot_chart(player_shotchart_df)
    
    # Establish the figure
    fig = plt.figure(1)
    # Show figure on Streamlit
    st.pyplot(fig) 

#GO TO POWERSHELL AND RUN COMMAND:  streamlit run streamlit-data-aggviz.py
import streamlit as st
import os
import pandas as pd
import altair as alt

st.set_page_config(layout="wide")

st.title("Sacramento Campaign Finance 2014 - 2023")
st.write("This application is designed to empower public investigation into Sacramento campaign finance data. Filter the data using the various parameters on the left, for example by campaign or committee, by the last name listed for contributions (which includes individuals, businesses, and orgs), or by year or date. Then, explore and visualize the filtered data in the bar and line charts below, selecting a category to aggregate the filtered data on. Below the charts is the output of the full filtered (or unfiltered) dataset, which you may download as a CSV file.")

folder_path = 'data/'

@st.cache_data
def read_jsons_from_folder(folder_path):
    all_files = [f for f in os.listdir(folder_path) if f.endswith('.json')]
    df_list = []
    
    for file in all_files:
        file_path = os.path.join(folder_path, file)
        df = pd.read_json(file_path)
        df_list.append(df)
    
    combined_df = pd.concat(df_list, ignore_index=True)

    combined_df['Campaigns-allYears'] = combined_df['filerName'].str[:-5] \
        .where(combined_df['filerName'].str[-4:].str.isnumeric(), combined_df['filerName'])
    combined_df['agencyName'] = combined_df['agencyName'].replace("City Council", "Sacramento City")
    combined_df['agencyName'] = combined_df['agencyName'].replace("Board of Supervisors", "Sacramento County")
    combined_df['year'] = combined_df['year'].astype(str)


    combined_df['amount'] = combined_df['amount'].astype(int)
    combined_df['date'] = pd.to_datetime(combined_df['date'])
    combined_df['datestring'] = combined_df['date'].dt.strftime('%B %d, %Y')  # 1. Add a column for the string representation of the date

    original_df = combined_df[['agencyName', 'filerName', 'Campaigns-allYears', 'amount', 'year',  'contributorLastName', 'contributorFirstName', 'contributorType','date','datestring', 'contributorCity', 'contributorZip', 'contributorOccupation', 'contributorEmployer','committeeType','transactionId']]

    column_mapping = {
        'agencyName':'Entity',
        'filerName':'Campaign/PAC',
        'Campaigns-allYears':'Campaigns/PACs-all years',
        'amount':'Contribution',
        'year':'Year',
        'date':'Timestamp',
        'datestring':'Date',
        'contributorLastName':'Contributor Last Name',
        'contributorFirstName':'Contributor First Name',
        'committeeType':'Committee Type',
        'contributorType': 'Contributor Type',
        'contributorCity':'Contributor City',
        'contributorZip':'Contributor Zip',
        'contributorOccupation':'Contributor Occupation',
        'contributorEmployer':'Contributor Employer',
        'transactionId':'Transaction ID #'
    }

    original_df.rename(columns=column_mapping, inplace=True)
    
    return original_df


original_df = read_jsons_from_folder(folder_path)

# Define the function to get filtered values
def get_filtered_values(column, active_filters):
    df = original_df.copy()
    for key, value in active_filters.items():
        if key != column and value != 'All':
            df = df[df[key] == (int(value) if key == 'year' else value)]
    return ['All'] + sorted(list(df[column].astype(str).unique()))
st.sidebar.write("Use the search bars below to filter the dataset. You may type directly into each bar, and add additional filtering terms for the Campaign/PAC column, Campaign/PACs-all years column (combines campaigns for the same candidate across multiple elections by removing any years at the end of campaign names), and Contributor Last Name column.")

# Initialize the session state for campaign_pac_filters if it doesn't exist
if 'campaign_pac_filters' not in st.session_state:
    st.session_state.campaign_pac_filters = ['All']
if 'campaign_pac_button_clicked_count' not in st.session_state:
    st.session_state.campaign_pac_button_clicked_count = 0

# Button to add a new filter for Campaign/PAC
if st.sidebar.button("Add another Campaign/PAC filter"):
    st.session_state.campaign_pac_button_clicked_count += 1

# Ensure 'campaign_pac_filters' length matches 'campaign_pac_button_clicked_count'
while len(st.session_state.campaign_pac_filters) <= st.session_state.campaign_pac_button_clicked_count:
    st.session_state.campaign_pac_filters.append('All')

# Display all existing filters for Campaign/PAC
for i in range(len(st.session_state.campaign_pac_filters)):
    current_filter = st.session_state.campaign_pac_filters[i]
    st.session_state.campaign_pac_filters[i] = st.sidebar.selectbox(
        f"Select Campaign/PAC {i + 1}",
        options=get_filtered_values('Campaign/PAC', {}),
        index=0,
        key=f'campaign_pac_filter_{i}'
    )
    
    
# Initialize the session state for campaigns_all_years_filters if it doesn't exist
if 'campaigns_all_years_filters' not in st.session_state:
    st.session_state.campaigns_all_years_filters = ['All']
if 'campaigns_all_years_button_clicked_count' not in st.session_state:
    st.session_state.campaigns_all_years_button_clicked_count = 0

# Button to add a new filter for Campaigns/PACs-all years
if st.sidebar.button("Add another Campaigns/PACs-all years filter"):
    st.session_state.campaigns_all_years_button_clicked_count += 1

# Ensure 'campaigns_all_years_filters' length matches 'campaigns_all_years_button_clicked_count'
while len(st.session_state.campaigns_all_years_filters) <= st.session_state.campaigns_all_years_button_clicked_count:
    st.session_state.campaigns_all_years_filters.append('All')

# Display all existing filters for Campaigns/PACs-all years
for i in range(len(st.session_state.campaigns_all_years_filters)):
    current_filter = st.session_state.campaigns_all_years_filters[i]
    st.session_state.campaigns_all_years_filters[i] = st.sidebar.selectbox(
        f"Select Campaigns/PACs-all years {i + 1}",
        options=get_filtered_values('Campaigns/PACs-all years', {}),
        index=0,
        key=f'campaigns_all_years_filter_{i}'
    )
    
# Initialize the session state for contributor_last_name_filters if it doesn't exist
if 'contributor_last_name_filters' not in st.session_state:
    st.session_state.contributor_last_name_filters = ['All']
if 'button_clicked_count' not in st.session_state:
    st.session_state.button_clicked_count = 0

# Button to add a new filter for Contributor Last Name
if st.sidebar.button("Add another Contributor Last Name filter"):
    st.session_state.button_clicked_count += 1

# Ensure 'contributor_last_name_filters' length matches 'button_clicked_count'
while len(st.session_state.contributor_last_name_filters) <= st.session_state.button_clicked_count:
    st.session_state.contributor_last_name_filters.append('All')

# Display all existing filters for Contributor Last Name
for i in range(len(st.session_state.contributor_last_name_filters)):
    current_filter = st.session_state.contributor_last_name_filters[i]
    st.session_state.contributor_last_name_filters[i] = st.sidebar.selectbox(
        f"Select Contributor Last Name {i + 1}",
        options=get_filtered_values('Contributor Last Name', {}),
        index=0,
        key=f'contributor_last_name_filter_{i}'
    )
    

# Main filter logic for other fields
filters = {
    'Entity': 'All',
    'Contributor First Name': 'All',
    'Contributor Type': 'All',
    'Committee Type': 'All',
    'Year': 'All',
    'Date': 'All',
    'Contributor City': 'All',
    'Contributor Zip': 'All',
    'Contribution': 'All',
    'Contributor Occupation': 'All',
    'Contributor Employer': 'All',
    'Transaction ID #': 'All'
}

st.sidebar.write("Additional search bars to filter the dataset on the other columns. Only 1 filter may be applied for these columns:")

# Create sidebar filters for fields other than Contributor Last Name
for column, value in filters.items():
    chosen_value = st.sidebar.selectbox(f"Select {column}", options=get_filtered_values(column, filters), key=column)
    filters[column] = chosen_value  # Store the chosen value back in the filters dictionary
    
# Filter the DataFrame based on selected filter values
filtered_df = original_df.copy()

# Apply dynamic filters for Contributor Last Name to the DataFrame
last_name_filters = [name for name in st.session_state.contributor_last_name_filters if name != 'All']
if last_name_filters:
    filtered_df = filtered_df[filtered_df['Contributor Last Name'].isin(last_name_filters)]

# Apply dynamic filters for Campaign/PAC to the DataFrame
campaign_pac_filters = [name for name in st.session_state.campaign_pac_filters if name != 'All']
if campaign_pac_filters:
    filtered_df = filtered_df[filtered_df['Campaign/PAC'].isin(campaign_pac_filters)]

# Apply dynamic filters for Campaigns/PACs-all years to the DataFrame
campaigns_all_years_filters = [name for name in st.session_state.campaigns_all_years_filters if name != 'All']
if campaigns_all_years_filters:
    filtered_df = filtered_df[filtered_df['Campaigns/PACs-all years'].isin(campaigns_all_years_filters)]
    
# Apply other selected filters to the DataFrame
for column, selected_option in filters.items():
    if selected_option != 'All':
        if column == 'Contribution':
            filtered_df = filtered_df[filtered_df[column] == int(selected_option)]
        else:
            filtered_df = filtered_df[filtered_df[column] == selected_option]

# Calculate aggregate total
aggregate_total = filtered_df['Contribution'].sum()
st.markdown(f"### Aggregate Total with Applied Filters: ${aggregate_total:,.2f}")

# Bar Chart: Amount by user-selected category
categories = [
    'Entity',
    'Campaign/PAC',
    'Campaigns/PACs-all years',
    'Contributor Last Name',
    'Contributor First Name',
    'Contributor Type',
    'Committee Type',
    'Year',
    'Date',
    'Contributor City',
    'Contributor Zip',
    'Contribution',
    'Contributor Occupation',
    'Contributor Employer',
    'Transaction ID #'
]


# Bar Chart: Amount by user-selected category
st.markdown("## Bar Chart Visualization")
st.write("The bar chart visualizes the aggregated amounts of the selected category within the filtered dataset. Hover your mouse over a bar to view its information")

selected_category_bar = st.selectbox("Select a category for the bar chart", categories)

MAX_PLOT_VALUES = st.number_input("Enter a maximum number of unique category values to display in the bar chart", min_value=1, max_value=1000, value=15, key='bar_chart_categories_input')

amount_by_category_bar = filtered_df.groupby(selected_category_bar)['Contribution'].sum().reset_index().sort_values(by='Contribution', ascending=False)
amount_by_category_bar['Contribution Amount'] = amount_by_category_bar['Contribution'].apply(lambda x: f"${x:,.2f}")

# If number of unique values is greater than MAX_PLOT_VALUES, show only top N
if len(amount_by_category_bar) > MAX_PLOT_VALUES:
    amount_by_category_bar = amount_by_category_bar.head(MAX_PLOT_VALUES)

bar_chart = alt.Chart(amount_by_category_bar).mark_bar().encode(
    y=alt.Y(f"{selected_category_bar}:O", sort='-x', title=selected_category_bar),
    x=alt.X('Contribution:Q', title='Contribution'),
    tooltip=[selected_category_bar, 'Contribution Amount']
)

st.altair_chart(bar_chart, use_container_width=True)


# Line Chart: Aggregated amount by user-selected category
st.markdown("## Line Chart Visualization")
st.write("The line chart visualizes the aggregated amount of contributions over time (by date or year) for a selected category. Note that some points may be hidden behind other points with the same contribution amount (you may verify using the bar chart). Hover your mouse over a data point to view its information and scroll with your mouse wheel to zoom in.")
selected_category_line = st.selectbox("Select a category for the line chart", categories)


aggregation_choice = st.radio("Choose an x-axis aggregation for line chart:", ['Year', 'Date'])
if aggregation_choice == 'Date':
    amount_by_category_line = filtered_df.groupby([selected_category_line, 'Timestamp', 'Date',])['Contribution'].sum().reset_index()
    amount_by_category_line['Contribution Amount'] = amount_by_category_line['Contribution'].apply(lambda x: f"${x:,.2f}")
    x_encoding = alt.X('Timestamp:T', title='Date')
    tooltip_fields = [selected_category_line, 'Date:N', 'Contribution Amount']
else:
    amount_by_category_line = filtered_df.groupby([selected_category_line, 'Year'])['Contribution'].sum().reset_index()
    amount_by_category_line['Contribution Amount'] = amount_by_category_line['Contribution'].apply(lambda x: f"${x:,.2f}")
    x_encoding = alt.X('Year:O', title='Year')
    tooltip_fields = [selected_category_line, 'Year', 'Contribution Amount']
    
MAX_PLOT_VALUES2 = st.number_input("Enter a maximum number of unique category values to display in the line chart", min_value=1, max_value=1000, value=15, key='line_chart_categories_input')

# If the number of unique categories is greater than MAX_PLOT_VALUES2, limit to top categories based on total contribution
if len(amount_by_category_line[selected_category_line].unique()) > MAX_PLOT_VALUES2:
    top_categories = amount_by_category_line.groupby(selected_category_line)['Contribution'].sum().nlargest(MAX_PLOT_VALUES2).index
    amount_by_category_line = amount_by_category_line[amount_by_category_line[selected_category_line].isin(top_categories)]

amount_by_category_line['Contribution Amount'] = amount_by_category_line['Contribution'].apply(lambda x: f"${x:,.2f}")


# Create a selection for highlighting
highlight_line = alt.selection(type='single', on='mouseover', fields=[selected_category_line], nearest=True)

# Base chart for points and lines
base_chart = alt.Chart(amount_by_category_line).encode(
    x=x_encoding,
    y=alt.Y('Contribution:Q', title='Contribution'),
    color=alt.Color(f"{selected_category_line}:N",
                    legend=None,
                    sort=alt.EncodingSortField(field="Contribution", op="sum", order="descending")),
    tooltip=tooltip_fields
)

# Mark points on the line
points_chart = base_chart.mark_point(size=100, filled=True, opacity=.7).encode(
    opacity=alt.condition(highlight_line, alt.value(1), alt.value(.7))
).add_selection(highlight_line)

# Draw the lines and modify thickness based on the selection
lines_chart = base_chart.mark_line().encode(
    size=alt.condition(highlight_line, alt.value(3), alt.value(1))
)

# Combine the points and lines charts
line_chart = (lines_chart + points_chart).interactive()

st.altair_chart(line_chart, use_container_width=True)

st.markdown("## Filtered Data")
st.write("The table below shows the original raw data after applying the selected filters. You can inspect specific rows to understand the details of each contribution, and the filtered dataset can be downloaded as a CSV file.")
st.write(filtered_df)
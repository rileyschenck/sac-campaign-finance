#GO TO POWERSHELL AND RUN COMMAND:  streamlit run SacCampaignFinance/streamlit-data-aggviz.py
import streamlit as st
import os
import pandas as pd
import altair as alt

st.set_page_config(layout="wide")

st.title("Sacramento Campaign Finance 2014 - 2023")
st.write("This application analyzes Sacramento campaign finance data from 2014 to 2023. You can filter the data using various parameters on the left, explore and visualize the aggregate data in the bar and line charts below, and download the filtered dataset at the bottom of the page.")

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


filters = {
    'Entity': 'All',
    'Campaign/PAC': 'All',
    'Campaigns/PACs-all years': 'All',
    'Contributor Last Name': 'All',
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

def get_filtered_values(column, active_filters):
    df = original_df.copy()
    for key, value in active_filters.items():
        if key != column and value != 'All':
            df = df[df[key] == (int(value) if key == 'year' else value)]
    return ['All'] + sorted(list(map(str, df[column].unique())))

st.sidebar.write("Use the search bars below to filter the dataset. You may type directly into each bar:")

for column in filters.keys():
    filters[column] = st.sidebar.selectbox(f"Select {column}", options=get_filtered_values(column, filters))


filtered_df = original_df.copy()

for key, value in filters.items():
    if value != 'All':
        if key == 'Contribution':
            value = int(value)
        filtered_df = filtered_df[filtered_df[key] == value]

aggregate_total = filtered_df['Contribution'].sum()

st.markdown(f"### Aggregate Total with Applied Filters: ${aggregate_total:,.2f}")


# Bar Chart: Amount by user-selected category
categories = [
    'Entity',
    'Campaign/PAC',
    'Campaigns/PACs-all years',
    'Contribution',
    'Year',
    'Date',
    'Contributor Last Name',
    'Contributor First Name',
    'Contributor Type',
    'Contributor City',
    'Contributor Zip',
    'Contributor Occupation',
    'Contributor Employer',
    'Committee Type',
    'Transaction ID #'
]
# Define a maximum limit for unique values to plot
MAX_PLOT_VALUES = 50

# Bar Chart: Amount by user-selected category
st.markdown("## Bar Chart Visualization")
st.write("The bar chart visualizes the aggregated amounts of the selected category within the filtered dataset. Only the top 50 unique values of a selected category are visualized.")
selected_category_bar = st.selectbox("Select a category for the bar chart", categories)
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
st.write("The line chart visualizes the aggregated amount of contributions over time (by date or year) for a selected category. Like the bar chart, only the top 50 unique values of a selected category are visualized. Note that some points may be hidden behind other points with the same contribution amount (you may verify using the bar chart).")
selected_category_line = st.selectbox("Select a category for the line chart", categories)

aggregation_choice = st.radio("Choose aggregation for line chart:", ['Date', 'Year'])
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
    
    
# If number of unique values is greater than MAX_PLOT_VALUES, show only top N
top_categories = amount_by_category_line.groupby(selected_category_line)['Contribution'].sum().nlargest(MAX_PLOT_VALUES).index
amount_by_category_line = amount_by_category_line[amount_by_category_line[selected_category_line].isin(top_categories)]
amount_by_category_line['Contribution Amount'] = amount_by_category_line['Contribution'].apply(lambda x: f"${x:,.2f}")

base_chart = alt.Chart(amount_by_category_line).encode(
    x=x_encoding,
    y=alt.Y('Contribution:Q', title='Contribution'),
    color=alt.Color(f"{selected_category_line}:N", 
                    legend=alt.Legend(title=selected_category_line),
                    sort=alt.EncodingSortField(field="Contribution", op="sum", order="descending")),
    tooltip=tooltip_fields
)

line_chart = (base_chart.mark_line() + base_chart.mark_point(size=100, filled=True, opacity=.5)).interactive()

st.altair_chart(line_chart, use_container_width=True)

st.markdown("## Filtered Data")
st.write("The table below shows the original raw data after applying the selected filters. You can inspect specific rows to understand the details of each contribution, and the filtered dataset can be downloaded as a CSV file.")
st.write(filtered_df)
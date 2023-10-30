#GO TO POWERSHELL AND RUN COMMAND:  streamlit run SacCampaignFinance/streamlit-data-aggviz.py
import streamlit as st
import os
import pandas as pd
import altair as alt

st.set_page_config(layout="wide")

st.title("Sacramento Campaign Finance 2014 - 2023")

folder_path = 'SacCampaignFinance/data/'

def read_jsons_from_folder(folder_path):
    all_files = [f for f in os.listdir(folder_path) if f.endswith('.json')]
    df_list = []
    
    for file in all_files:
        file_path = os.path.join(folder_path, file)
        df = pd.read_json(file_path)
        df_list.append(df)
    
    combined_df = pd.concat(df_list, ignore_index=True)
    return combined_df

combined_df = read_jsons_from_folder(folder_path)

combined_df['Campaigns-allYears'] = combined_df['filerName'].str[:-5] \
    .where(combined_df['filerName'].str[-4:].str.isnumeric(), combined_df['filerName'])
combined_df['agencyName'] = combined_df['agencyName'].replace("City Council", "Sacramento City")
combined_df['agencyName'] = combined_df['agencyName'].replace("Board of Supervisors", "Sacramento County")
combined_df['year'] = combined_df['year'].astype(str)


combined_df['amount'] = combined_df['amount'].astype(int)
combined_df['date'] = pd.to_datetime(combined_df['date'])
combined_df['date'] = combined_df['date'].dt.strftime('%B %d, %Y')  # 1. Add a column for the string representation of the date

original_df = combined_df[['agencyName', 'filerName', 'Campaigns-allYears', 'amount', 'year', 'date', 'contributorLastName', 'contributorFirstName', 'contributorType', 'contributorCity', 'contributorZip', 'contributorOccupation', 'contributorEmployer','committeeType','transactionId']]

column_mapping = {
    'agencyName':'Entity',
    'filerName':'Campaign/PAC',
    'Campaigns-allYears':'Campaigns/PACs-all years',
    'amount':'Contribution',
    'year':'Year',
    'date':'Date',
    'contributorLastName':'Contributor Last Name',
    'contributorFirstName':'Contributor First Name',
    'contributorType': 'Contributor Type',
    'contributorCity':'Contributor City',
    'contributorZip':'Contributor Zip',
    'contributorOccupation':'Contributor Occupation',
    'contributorEmployer':'Contributor Employer',
    'committeeType':'Committee Type',
    'transactionId':'Transaction ID #'
}

original_df.rename(columns=column_mapping, inplace=True)

# original_df['Contribution'] = original_df['Contribution'].astype(int)
# original_df['Date'] = pd.to_datetime(original_df['Date'])
# original_df['DateString'] = original_df['Date'].dt.strftime('%B %d, %Y')  # 1. Add a column for the string representation of the date


filters = {
    'Entity': 'All',
    'Campaign/PAC': 'All',
    'Campaigns/PACs-all years': 'All',
    'Contribution': 'All',
    'Year': 'All',
    'Date': 'All',
    'Contributor Last Name': 'All',
    'Contributor First Name': 'All',
    'Contributor Type': 'All',
    'Contributor City': 'All',
    'Contributor Zip': 'All',
    'Contributor Occupation': 'All',
    'Contributor Employer': 'All',
    'Committee Type': 'All',
    'Transaction ID #': 'All'
}

def get_filtered_values(column, active_filters):
    df = original_df.copy()
    for key, value in active_filters.items():
        if key != column and value != 'All':
            df = df[df[key] == (int(value) if key == 'year' else value)]
    return ['All'] + sorted(list(map(str, df[column].unique())))

for column in filters.keys():
    filters[column] = st.sidebar.selectbox(f"Select {column}", options=get_filtered_values(column, filters))

filtered_df = original_df.copy()

for key, value in filters.items():
    if value != 'All':
        if key == 'Contribution':
            value = int(value)
        filtered_df = filtered_df[filtered_df[key] == value]

aggregate_total = filtered_df['Contribution'].sum()
st.write(f"Aggregate Total Amount: ${aggregate_total:,.2f}")


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
selected_category_bar = st.selectbox("Select a category for the bar chart", categories)
amount_by_category_bar = filtered_df.groupby(selected_category_bar)['Contribution'].sum().reset_index().sort_values(by='Contribution', ascending=False)

# If number of unique values is greater than MAX_PLOT_VALUES, show only top N
if len(amount_by_category_bar) > MAX_PLOT_VALUES:
    amount_by_category_bar = amount_by_category_bar.head(MAX_PLOT_VALUES)

bar_chart = alt.Chart(amount_by_category_bar).mark_bar().encode(
    y=alt.Y(f"{selected_category_bar}:O", sort='-x', title=selected_category_bar),
    x=alt.X('Contribution:Q', title='Contribution')
)
st.altair_chart(bar_chart, use_container_width=True)


# Line Chart: Aggregated amount by user-selected category
selected_category_line = st.selectbox("Select a category for the line chart", categories)

aggregation_choice = st.radio("Choose aggregation for line chart:", ['Date', 'Year'])

if aggregation_choice == 'Date':
    date_df=filtered_df.copy()
    amount_by_category_line = date_df.groupby([selected_category_line, 'Date'])['Contribution'].sum().reset_index()
    x_encoding = alt.X('Date:O', title='Date', sort=alt.SortArray(list(date_df['Date'].unique())))  # Changed to ordinal and added sort
    tooltip_fields = [selected_category_line, alt.Tooltip('Date:N', title='Date'), 'Contribution']
else:
    year_df=filtered_df.copy()
    amount_by_category_line = year_df.groupby([selected_category_line, 'Year'])['Contribution'].sum().reset_index()
    x_encoding = alt.X('Year:O', title='Year')
    tooltip_fields = [selected_category_line, 'Year', 'Contribution']
    
    
# If number of unique values is greater than MAX_PLOT_VALUES, show only top N
top_categories = amount_by_category_line.groupby(selected_category_line)['Contribution'].sum().nlargest(MAX_PLOT_VALUES).index
amount_by_category_line = amount_by_category_line[amount_by_category_line[selected_category_line].isin(top_categories)]

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

st.write(filtered_df)
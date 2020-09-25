import pandas as pd
import numpy as np
import dash
import dash_table
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.colors as cl
from datetime import datetime as dt
import dash_bootstrap_components as dbc

external_stylesheets = [dbc.themes.BOOTSTRAP]


app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

## Data upload and pre-processing

# covid = pd.read_csv("InternationalCOVID19Cases.csv")
covid = pd.read_csv("https://mapdashbd.s3.ca-central-1.amazonaws.com/download/InternationalCovid19Cases.csv")

## Adding a new column of data
countries = covid["name_en"].unique()
daily_cases = []
daily_ma = []

for country in countries:
    daily_cases += [np.array(covid[covid["name_en"] == country]["cases"])[0]]
    daily_cases += list(np.array(covid[covid["name_en"] == country]["cases"][1:]) -
                        np.array(covid[covid["name_en"] == country]["cases"][:-1]))
covid["daily_cases"] = daily_cases

for country in countries:
    daily_ma += covid[covid['name_en'] == country]['daily_cases'].rolling(window=5).mean().to_list()

covid["daily_ma"] = daily_ma

country_options = []
for country in countries:
    country_options.append({'label':country, 'value':country})

date_int = covid["date"].unique()
markers = {}
for date in date_int:
    markers[int(date.replace("-",""))] = date
min_date = covid["date"].min()
max_date = covid["date"].max()


currentdata_df = covid[covid["date"] == max_date].sort_values("cases", ascending=False)[["name_en","cases", "deaths", "cases_100k"]]
currentdata_df.columns = ["Country", "Total Confirmed Cases", "Total Confirmed Deaths", "Cases per 100k"]
currentdata_df["Death %"] = np.round(currentdata_df["Total Confirmed Deaths"]/currentdata_df["Total Confirmed Cases"] * 100, 2)

worldwide_cases = currentdata_df["Total Confirmed Cases"].sum()
worldwide_deaths = currentdata_df["Total Confirmed Deaths"].sum()

table_df = currentdata_df
table_df["Total Confirmed Cases"] = table_df["Total Confirmed Cases"].apply(lambda x: f"{x:,d}")
table_df["Total Confirmed Deaths"] = table_df["Total Confirmed Deaths"].apply(lambda x: f"{x:,d}")


app.layout = html.Div(children=[
    html.H1(children='COVID-19 Data', style={'padding': '0px 0px 5px 10px'}),

    html.Div(children='''
        Please select the countries of interest and start and end dates of desired data:
    ''', style={'width': '49%', 'display': 'inline-block','padding': '0px 0px 5px 10px'}),
    html.H5(children=['Total Worldwide Cases: ', f"{worldwide_cases:,d}",
                        " | Total Worldwide Deaths: ", f"{worldwide_deaths:,d}"],
                      style={'width': '49%', 'display': 'inline-block'}),
    html.Div(dcc.Dropdown(
        id = "country-dropdown",
        options = country_options,
        multi = True,
        value = ["Canada"],
        style=dict(
                width='50%',
                verticalAlign="middle")
    ), style={'padding': '0px 0px 5px 10px'}),

    html.Div(dcc.DatePickerRange(
        id = "date-picker",
        min_date_allowed = dt(int(min_date[:4]), int(min_date[5:7]), int(min_date[8:])),
        max_date_allowed = dt(int(max_date[:4]), int(max_date[5:7]), int(max_date[8:])),
        start_date_placeholder_text="Start Period",
        end_date_placeholder_text="End Period",
        start_date = dt(int(min_date[:4]), int(min_date[5:7]), int(min_date[8:])),
        end_date = dt(int(max_date[:4]), int(max_date[5:7]), int(max_date[8:]))
    ), style={'display': 'inline-block','padding': '0px 0px 5px 10px'}),
    html.Div(dcc.RadioItems(
        id='radio_ma',
        options=[
            {'label': 'Daily Cases', 'value': 'daily_cases'},
            {'label': 'Averaged Daily Cases', 'value':'daily_ma'}
        ],
        value = 'daily_cases',
        inputStyle={"margin-right": "5px", "margin-left": "5px"}
    ), style={'width': '49%', 'display': 'inline-block','padding': '0px 0px 5px 10px'}),
    html.Div(dcc.Graph(
        id = 'cases-graph')),
    html.Div(dash_table.DataTable(
        id = 'total-cases-table',
        columns = [{'name':i, 'id': i} for i in currentdata_df.columns],
        data = table_df.to_dict('records'),
        sort_action = "native",
        fixed_rows={'headers': True},
        style_table = {'overflowY': 'scroll',
                     'height':550#,
                     # 'width':850
                     },
        # style_as_list_view=True,
        style_data_conditional=[
            {
                'if': {'row_index': 'odd'},
                'backgroundColor': 'rgb(248, 248, 248)'
            }
        ],
        style_header={
            'backgroundColor': 'rgb(230, 230, 230)',
            'fontWeight': 'bold'
        },
        style_cell = {
                'font_family': 'arial',
                'text_align': 'center'
        },
        css=[{'selector': '.row', 'rule': 'margin: 0'}]),
        style={
               # 'width': '49%','display':'inline-block',
               'margin-right': 'auto',
               'margin-left': 'auto',
               'padding': '20px 0px 0px 0px',
               'padding-left':'5%', 'padding-right':'5%'})

    # html.H4(children='COVID-19 Data', style={'width': '49%', 'display': 'inline-block'})
    # html.Div(children='''
    #     Please select the countries of interest and start and end dates of desired data:
    # ''', style={'width': '49%', 'display': 'inline-block'})
])


@app.callback(
    Output("cases-graph", "figure"),
    [Input("country-dropdown", "value"),
     Input("date-picker", "start_date"),
     Input("date-picker", "end_date"),
     Input("radio_ma", "value")]
)
def plot_all(country, start_date, end_date, daily):
    if daily == "daily_cases":
        daily_str = "Daily Number of New COVID-19 Cases"
    else:
        daily_str = "5-day Averaged Daily Number of New COVID-19 Cases"
    fig = make_subplots(rows=2, cols=2,
                        subplot_titles = (daily_str,
                                          "Percentage of Cases by Country",
                                          "Total Number of COVID-19 Cases",
                                          "Top 20 Countries with Highest Death Rate of COVID-19 Patients"),
                        vertical_spacing=0.1,
                        # specs = [[{"type": "pie", "rowspan": 2}, {"type": "scatter"}],
                        #          [None, {"type": "scatter"}]]
                        specs = [[{"type": "scatter"}, {"type": "pie"}],
                                 [{"type": "scatter"}, {"type": "bar"}]]

                                 )

    ## Total Case Percentage by Country
    percent_df = covid[covid["date"] == max_date].sort_values("cases")
    worldwide_cases = percent_df["cases"].sum()
    percent_df["Total Case Percentage"] = percent_df["cases"] / worldwide_cases

    num_countries = 20
    per_series = percent_df["Total Case Percentage"][-num_countries:].reset_index(drop=True)
    per_series.at[num_countries+1] = percent_df["Total Case Percentage"][:-num_countries].sum()
    count_series = percent_df["name_en"][-num_countries:]
    count_series.at[num_countries+1] = "Other"

    fig.add_trace(go.Pie(labels = count_series, values = per_series,
                         name = "", showlegend = False,
                         textinfo = "label+percent",
                         hovertemplate = "%{label}: %{percent}",
                         textposition='inside'
                         ),
                        row = 1, col = 2)

    ## Death Percentage by Country
    ordered_df = currentdata_df.sort_values("Death %", ascending = False)
    death_series = ordered_df["Death %"][:num_countries].reset_index(drop=True)
    dcount_series = ordered_df["Country"][:num_countries]

    fig.add_trace(go.Bar(x = dcount_series, y = death_series,
                         name = "", showlegend = False, marker_color = "rgb(179,0,0)"
                         ),
                        row = 2, col = 2)
    col_lst = cl.qualitative.Plotly
    col_len = len(col_lst)
    col_counter = 0
    for c in country:
        if col_counter == col_len:
            col_counter = 0
        plotdf = covid.copy()
        ## Filter by country
        plotdf = plotdf[plotdf["name_en"] == c]
        ## Filter by date
        plotdf = plotdf[(plotdf["date"] >= start_date) & (plotdf["date"] <= end_date)]
        ## Total Cases
        fig.add_trace(go.Scatter(x = plotdf["date"], y = plotdf["cases"],
                                name = c, legendgroup = c, showlegend = False,
                                line = {'color':col_lst[col_counter]}),
                        row = 2, col = 1)
        ## Daily Cases
        fig.add_trace(go.Scatter(x = plotdf["date"], y = plotdf[daily],
                                name = c, legendgroup = c,
                                line = {'color':col_lst[col_counter]}),
                        row = 1, col = 1)

        ## Updating x-axis labels
        # fig.update_xaxes(title_text = "Total Number of Cases", row = 1, col = 1)
        fig.update_xaxes(title_text = "Date", row = 1, col = 1)
        fig.update_xaxes(title_text = "Date", row = 2, col = 1)
        fig.update_xaxes(title_text = "Country", row = 2, col = 2)


        ## Updating y-axis labels
        # fig.update_yaxes(title_text = "Country", row = 1, col = 1)
        fig.update_yaxes(title_text = "Number of New Confirmed Cases (Daily)", row = 1, col = 1)
        fig.update_yaxes(title_text = "Total Number of Confirmed Cases", row = 2, col = 1)
        fig.update_yaxes(title_text = "Death Rate (%)", row = 2, col = 2)

        col_counter += 1
    fig.update_layout(autosize=False, height=900)
    fig.update_layout(legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="left",
            x=0.46))

    return fig


# def plot_movingavg(country, start_date, end_date):



if __name__ == '__main__':
    app.run_server(debug=True)

# Stuff saved for date conversion
#
# import datetime
#
# def list_to_date(lst):
#     int_lst = [int(val) for val in lst]
#     return datetime.date(int_lst[0], int_lst[1], int_lst[2])
#
# def get_days(val):
#     return val.days
#
# def str_to_int(lst):
#     return [int(val) for val in lst]
#
# def get_seconds(series):
#     ad = series['assign_date']
#     cd = series['complete_date']
#     at = series['assign_time']
#     ct = series['complete_time']
#     return (datetime.datetime(cd[0],cd[1],cd[2],ct[0],ct[1],ct[2]) -
#             datetime.datetime(ad[0],ad[1],ad[2],at[0],at[1],at[2])).total_seconds()
#
#
# temp_df = pd.DataFrame(tasks['assigned_time'].str.split(" ").tolist(), columns = ['assign_date','assign_time'])
# temp_df[['complete_date','complete_time']] = pd.DataFrame(tasks['completion_time'].str.split(" ").tolist(),
#                                                           index=temp_df.index)
#
# temp_df['assign_date'] = temp_df['assign_date'].str.split("-").apply(str_to_int)
# temp_df['complete_date'] = temp_df['complete_date'].str.split("-").apply(str_to_int)
# temp_df['assign_time'] = temp_df['assign_time'].str.split(":").apply(str_to_int)
# temp_df['complete_time'] = temp_df['complete_time'].str.split(":").apply(str_to_int)
#
# temp_df['second_complete'] = temp_df.apply(lambda x: get_seconds(x), axis=1)
#
#

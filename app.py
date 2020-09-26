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
import dash_table.FormatTemplate as FormatTemplate


external_stylesheets = [dbc.themes.BOOTSTRAP]


app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

server = app.server

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


table_df = covid[covid["date"] == max_date].sort_values("cases", ascending=False)[["name_en","cases", "deaths", "cases_100k"]]
table_df.columns = ["Country", "Total Confirmed Cases", "Total Confirmed Deaths", "Cases per 100k"]
table_df["Death %"] = table_df["Total Confirmed Deaths"]/table_df["Total Confirmed Cases"]

worldwide_cases = table_df["Total Confirmed Cases"].sum()
worldwide_deaths = table_df["Total Confirmed Deaths"].sum()



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
        columns = [
            {
            'name': 'Country',
            'id': 'Country',
            'type': 'text'
        },  {
            'name': 'Total Confirmed Cases',
            'id': 'Total Confirmed Cases',
            'type': 'numeric'
        },  {
            'name': 'Total Confirmed Deaths',
            'id': 'Total Confirmed Deaths',
            'type': 'numeric'
        },  {
            'name': 'Cases per 100k',
            'id': 'Cases per 100k',
            'type': 'numeric'
        },  {
            'name': 'Death %',
            'id': 'Death %',
            'type': 'numeric',
            'format': FormatTemplate.percentage(2)
        }],
        data = table_df.to_dict('records'),
        sort_action = "native",
        fixed_rows={'headers': True},
        style_table = {'overflowY': 'scroll',
                     'height':550#,
                     # 'width':850
                     },
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
               'margin-right': 'auto',
               'margin-left': 'auto',
               'padding': '20px 0px 0px 0px',
               'padding-left':'5%', 'padding-right':'5%'})

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
    ordered_df = table_df.sort_values("Death %", ascending = False)
    death_series = ordered_df["Death %"][:num_countries].reset_index(drop=True) * 100
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
        fig.update_xaxes(title_text = "Date", row = 1, col = 1)
        fig.update_xaxes(title_text = "Date", row = 2, col = 1)
        fig.update_xaxes(title_text = "Country", row = 2, col = 2)


        ## Updating y-axis labels
        fig.update_yaxes(title_text = "Number of New Confirmed Cases (Daily)", row = 1, col = 1)
        fig.update_yaxes(title_text = "Total Number of Confirmed Cases", row = 2, col = 1)
        fig.update_yaxes(title_text = "Death Rate (%)", row = 2, col = 2)

        col_counter += 1
    fig.update_layout(height=900)
    fig.update_layout(legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="left",
            x=0.46))

    return fig

if __name__ == '__main__':
    app.run_server(debug=True)

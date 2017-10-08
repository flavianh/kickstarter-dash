# -*- coding: utf-8 -*-

import dash
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objs as go
import dash_table_experiments as dt
import iso3166
import pandas as pd

app = dash.Dash()
app.css.append_css({
    "external_url": "https://codepen.io/chriddyp/pen/bWLwgP.css"
})

kickstarter_df = pd.read_csv('kickstarter-cleaned-subset.csv', parse_dates=True)
kickstarter_df_sub = kickstarter_df.sample(10000)

kickstarter_df['created_at'] = pd.to_datetime(kickstarter_df['created_at'])


def generate_table(dataframe, max_rows=10):
    """Generate an HTML table from a dataframe."""
    return html.Table(
        # Header
        [html.Tr([html.Th(col) for col in dataframe.columns])] +

        # Body
        [html.Tr([
            html.Td(str(dataframe.iloc[i][col])) for col in dataframe.columns
        ]) for i in range(min(len(dataframe), max_rows))]
    )


columns = ['launched_at', 'deadline', 'blurb', 'usd_pledged', 'state', 'spotlight', 'staff_pick', 'category_slug', 'backers_count', 'country']

kickstarter_country = kickstarter_df.groupby('country').count().reset_index()
# Convert country names to alpha3 standard
kickstarter_country['country'] = kickstarter_country['country'].map(lambda alpha2: iso3166.countries_by_alpha2[alpha2].alpha3)

kickstarter_df['broader_category'] = kickstarter_df['category_slug'].str.split('/').str.get(0)

data = [
    dict(
        type='choropleth',
        locations=kickstarter_country.country,
        z=kickstarter_country.id,
        text=kickstarter_country.country,
        autocolorscale=True,
        colorbar=dict(
            autotick=True,
            title='Number of projects'
        ),
        marker=dict(
            line=dict(
                color='rgb(180,180,180)',
                width=0.5
            )
        ),
    )
]

layout = dict(
    title='Project counts by country',
    geo=dict(
        showland=True,
        landcolor="#DDDDDD",
        projection=dict(
            type='Mercator'
        )
    )
)

figure = dict(data=data, layout=layout)

app.layout = html.Div(children=[
    html.H1(children='Kickstarter Dashboard', style={
        'textAlign': 'center',
    }),

    dcc.Graph(
        id='life-exp-vs-gdp',
        figure={
            'data': [
                go.Scatter(
                    x=kickstarter_df_sub[kickstarter_df_sub.state == state]['created_at'],
                    y=kickstarter_df_sub[kickstarter_df_sub.state == state]['usd_pledged'],
                    text=kickstarter_df_sub[kickstarter_df_sub.state == state]['name'],
                    mode='markers',
                    opacity=0.7,
                    marker={
                        'size': 15,
                        'line': {'width': 0.5, 'color': 'white'}
                    },
                    name=state,
                ) for state in kickstarter_df.state.unique()
            ],
            'layout': go.Layout(
                xaxis={'title': 'Date'},
                yaxis={'title': 'USD pledged', 'type': 'log'},
                margin={'l': 40, 'b': 40, 't': 10, 'r': 10},
                legend={'x': 0, 'y': 1},
                hovermode='closest'
            )
        }
    ),
    dt.DataTable(
        # Using astype(str) to show booleans
        rows=kickstarter_df[columns].sample(100).astype(str).to_dict('records'),
        columns=columns,
        editable=False,
        filterable=True,
        sortable=True,
        id='kickstarter-datatable'
    ),
    dcc.RadioItems(
        id='kickstarter-barchart-type',
        options=[{'label': i, 'value': i} for i in ['cumulative', 'normalized']],
        value='cumulative',
        labelStyle={'display': 'inline-block'}
    ),
    dcc.RadioItems(
        id='kickstarter-barchart-aggregation',
        options=[{'label': i, 'value': i} for i in ['count', 'usd_pledged']],
        value='count',
        labelStyle={'display': 'inline-block'}
    ),
    dcc.Graph(id='kickstarter-barchart'),
    html.Div(children=[
        dcc.Slider(
            id='kickstarter-barchart-year-slider',
            min=2011,
            max=2017,
            value=kickstarter_df['created_at'].dt.year.max(),
            step=None,
            marks={str(year): str(year) for year in range(2011, 2018)}
        ),
    ], style={
        'marginBottom': '50px',
    }),
    dcc.Graph(id='map', figure=figure)
])


@app.callback(
    dash.dependencies.Output('kickstarter-barchart', 'figure'),
    [
        dash.dependencies.Input('kickstarter-barchart-type', 'value'),
        dash.dependencies.Input('kickstarter-barchart-aggregation', 'value'),
        dash.dependencies.Input('kickstarter-barchart-year-slider', 'value'),
    ])
def update_bar_chart(kickstarter_barchart_type, kickstarter_barchart_aggregation, kickstarter_barchart_year_slider):
    """Update bar chart."""
    if 'usd_pledged' == kickstarter_barchart_aggregation:
        stacked_barchart_df = (
            kickstarter_df[
                (kickstarter_df['created_at'].dt.year == kickstarter_barchart_year_slider)
            ]
            .groupby(['broader_category', 'state'])[[kickstarter_barchart_aggregation]]
            .sum()
            .reset_index('state')
            .pivot(columns='state')
        )
        if kickstarter_barchart_type == 'normalized':
            stacked_barchart_df = stacked_barchart_df.div(stacked_barchart_df.sum(axis=1), axis=0)
        stacked_barchart_df.reset_index(inplace=True)
    else:
        stacked_barchart_df = (
            kickstarter_df[
                (kickstarter_df['created_at'].dt.year == kickstarter_barchart_year_slider)
            ]['state'].groupby(kickstarter_df['broader_category'])
            .value_counts(normalize=kickstarter_barchart_type == 'normalized')
            .rename(kickstarter_barchart_aggregation)
            .to_frame()
            .reset_index('state')
            .pivot(columns='state')
            .reset_index()
        )

    return {
        'data': [
            go.Bar(
                x=stacked_barchart_df['broader_category'],
                y=stacked_barchart_df[kickstarter_barchart_aggregation][state],
                name=state,
            ) for state in ['canceled', 'failed', 'successful', 'suspended']
        ],
        'layout': go.Layout(
            xaxis={'title': 'Date'},
            yaxis={'title': 'USD pledged'},
            barmode='stack',
            margin={'l': 40, 'b': 40, 't': 10, 'r': 10},
            legend={'x': 0, 'y': 1},
            hovermode='closest'
        )
    }

if __name__ == '__main__':
    app.run_server(debug=True)

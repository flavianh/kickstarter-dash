# -*- coding: utf-8 -*-

import base64
import dash
import dash_core_components as dcc
import dash_html_components as html
import functools
import os
import plotly.graph_objs as go
import plotly.figure_factory as ff
import dash_table_experiments as dt
import io
import iso3166
import numpy as np
import pandas as pd
import random
from wordcloud import WordCloud, STOPWORDS


def grey_color_func(word, font_size, position, orientation, random_state=None,
                    **kwargs):
    """Color function for wordcloud."""
    return 'hsl(0, 0%, {0}%)'.format(20)


app = dash.Dash()
app.css.append_css({
    "external_url": "https://codepen.io/chriddyp/pen/bWLwgP.css"
})

kickstarter_df = pd.read_csv('kickstarter-cleaned.csv', parse_dates=True)
kickstarter_df_sub = kickstarter_df.sample(10000)

kickstarter_df['created_at'] = pd.to_datetime(kickstarter_df['created_at'])


def get_state_trace(x, state, color, df):
    """Generate a bar trace from x, state, color and a dataframe."""
    # Count number of rows under state `name`
    trace_data = [
        (df[(~df.staff_pick)].state == state).sum(),
        (df[(df.staff_pick)].state == state).sum(),
    ]
    return go.Bar(
        x=x,
        y=trace_data,
        name=state,
        marker=dict(
            color=color
        )
    )


def generate_grouped_bar_chart_vs_spotlight_and_staff_pick(df):
    """Generate a figure with success rate box plot according to combinations of spotlight and staff pick values."""
    x = [
        'Not picked by staff',
        'Picked by staff'
    ]

    states = ['failed', 'suspended', 'canceled', 'successful']
    colors = ['#C7583F', '#D4752E', '#C7B815', '#7DFB6D']
    data = [
        get_state_trace(x, state, color, df)
        for (state, color) in zip(states, colors)
    ]

    layout = go.Layout(
        barmode='group',
        title='Number of projects in a given state relative to spotlight and staff pick'
    )
    fig = go.Figure(data=data, layout=layout)

    return fig


def generate_usd_pledged_hist_vs_spotlight_and_staff_pick(df):
    """Generate a figure with USD pledged histogram according to combinations of spotlight and staff pick values."""
    bin_size = 2000
    df_successful = df[(df.state == 'successful') & (df.usd_pledged < 100000)]
    hist_data = [
        df_successful[(~df_successful.staff_pick)].usd_pledged.values,
        df_successful[(df_successful.staff_pick)].usd_pledged.values,
    ]

    group_labels = [
        'Not picked by staff',
        'Picked by staff'
    ]

    colors = ['#03241F', '#68D35A']

    # Create distplot with curve_type set to 'normal'
    fig = ff.create_distplot(hist_data, group_labels, colors=colors,
                             bin_size=bin_size, show_rug=False)

    # Add title
    fig['layout'].update(
        title='Successful projects with under $100k pledged',
        xaxis={'title': 'Money pledged in USD'},
        yaxis={'title': 'Proportion'},
    )
    return fig


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


def get_alpha3(alpha2):
    """Get alpha3 code from alpha2 code."""
    country = iso3166.countries_by_alpha2.get(alpha2)
    if country is None:
        return 'UNKNOWN'
    return country.alpha3


kickstarter_country['country'] = kickstarter_country['country'].map(get_alpha3)

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
    dcc.Dropdown(
        id='category',
        options=[{'label': i, 'value': i} for i in kickstarter_df['broader_category'].unique()],
        value=kickstarter_df['broader_category'].unique()[0],
    ),
    dcc.Graph(
        id='life-exp-vs-gdp'
    ),
    dcc.Checklist(
        id='states',
        options=[{'label': i, 'value': i} for i in ['canceled', 'failed', 'successful', 'suspended']],
        values=['canceled', 'failed', 'successful', 'suspended'],
        labelStyle={'display': 'inline-block'}
    ),
    html.Div(
        children=[html.Img(id='wordcloud')],
        style={
            'textAlign': 'center',
        }
    ),
    dcc.Graph(
        id='generate-usd-pledged-hist-vs-spotlight-and-staff-pick',
        figure=generate_usd_pledged_hist_vs_spotlight_and_staff_pick(kickstarter_df)
    ),
    dcc.Graph(
        id='generate-success-rate-boxed-plot-vs-spotlight-and-staff-pick',
        figure=generate_grouped_bar_chart_vs_spotlight_and_staff_pick(kickstarter_df)
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
    dcc.Graph(id='map', figure=figure),
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


@app.callback(
    dash.dependencies.Output('life-exp-vs-gdp', 'figure'),
    [
        dash.dependencies.Input('category', 'value'),
    ])
@functools.lru_cache(maxsize=50)
def update_usd_pledged_vs_time(category):
    """Update the graph."""
    return {
        'data': [
            go.Scatter(
                x=kickstarter_df_sub[(kickstarter_df.broader_category == category) & (kickstarter_df_sub.state == state)]['created_at'],
                y=kickstarter_df_sub[(kickstarter_df.broader_category == category) & (kickstarter_df_sub.state == state)]['usd_pledged'],
                text=kickstarter_df_sub[(kickstarter_df.broader_category == category) & (kickstarter_df_sub.state == state)]['name'],
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


@app.callback(
    dash.dependencies.Output('wordcloud', 'src'),
    [
        dash.dependencies.Input('states', 'values'),
        dash.dependencies.Input('category', 'value'),
    ])
def update_wordcloud(states, category):
    """Update the wordcloud."""
    if states == []:
        return ''
    states = frozenset(states)
    return _update_wordcloud_from_set(states, category)


@functools.lru_cache(maxsize=50)
def _update_wordcloud_from_set(states, category):
    """Update the wordcloud."""
    text = ' '.join(kickstarter_df_sub[kickstarter_df_sub.state.isin(states) & (kickstarter_df_sub.broader_category == category)].blurb).lower()
    wordcloud_buffer = io.BytesIO()
    wordcloud_image = (
        WordCloud(stopwords=set(STOPWORDS), background_color='white', max_words=500, width=800, height=400, color_func=grey_color_func)
        .generate(text).to_image()
    )
    wordcloud_image.save(wordcloud_buffer, format="JPEG")
    encoded_wordcloud = base64.b64encode(wordcloud_buffer.getvalue()).decode('utf-8')

    return 'data:image/png;base64,{}'.format(encoded_wordcloud)


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run_server(debug=True, host='0.0.0.0', port=port)

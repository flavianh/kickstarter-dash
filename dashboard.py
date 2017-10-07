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

kickstarter_df = pd.read_csv('kickstarter-cleaned-subset.csv')
kickstarter_df_sub = kickstarter_df.sample(10000)


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
    dcc.Graph(id='map', figure=figure)
])

if __name__ == '__main__':
    app.run_server(debug=True)

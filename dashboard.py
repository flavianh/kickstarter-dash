# -*- coding: utf-8 -*-

import dash
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objs as go
import pandas as pd

app = dash.Dash()
app.css.append_css({
    "external_url": "https://codepen.io/chriddyp/pen/bWLwgP.css"
})

kickstarter_df = pd.read_csv('kickstarter-cleaned-subset.csv')

app.layout = html.Div(children=[
    html.H1(children='Kickstarter Dashboard', style={
        'textAlign': 'center',
    }),

    dcc.Graph(
        id='life-exp-vs-gdp',
        figure={
            'data': [
                go.Scatter(
                    x=kickstarter_df[kickstarter_df.state == state]['created_at'],
                    y=kickstarter_df[kickstarter_df.state == state]['usd_pledged'],
                    text=kickstarter_df[kickstarter_df.state == state]['name'],
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
    )
])

if __name__ == '__main__':
    app.run_server(debug=True)

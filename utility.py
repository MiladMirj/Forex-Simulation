import pandas as pd
from plotly.offline import plot

def update_candlestick_chart(candlesticks, fig, type):
    df = pd.DataFrame(candlesticks, columns=['time', 'open', 'close', 'high', 'low'])
    if type == 'candle': 
        fig.update_traces(x=df['time'], open=df['open'], high=df['high'], low=df['low'], close=df['close'])
        fig.update_layout(title='Candlestick Chart', xaxis_rangeslider_visible=False)
        fig.update_layout(
            xaxis=dict(
                tickformat="%H:%M:%S"# Format the x-axis to show only time
            )
        )
        plot_html = plot(fig, output_type='div', include_plotlyjs='cdn')
    else:
        fig.update_traces(x=df['time'], y=df['close'])
        fig.update_layout(title='Line Chart', xaxis_rangeslider_visible=False)
        fig.update_layout(
            xaxis=dict(
                tickformat="%H:%M:%S" # Format the x-axis to show only time
            )
        )
        plot_html = plot(fig, output_type='div', include_plotlyjs='cdn')
    return plot_html, df


def is_float(input_str):
        try:
            number = float(input_str)
            return True
        except ValueError:
            return False


def format_currency(amount, unit='$'):
        if unit=='$':
            return '${:,.2f}'.format(amount)
        else:
            return '€{:,.2f}'.format(amount)            
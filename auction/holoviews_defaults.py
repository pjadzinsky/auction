import holoviews as hv

print('from holoviews_defaults')
try:
    hv.extension('bokeh')

    hv.opts({'Curve': {'plot': {'tools': ['hover'], 'width': 1000}}})
    hv.opts({'Points': {'plot': {'tools': ['hover'], 'width': 1000}}})
    hv.opts({'Scatter': {'plot': {'tools': ['hover'], 'width': 1000}}})
    hv.opts({'Histogram': {'plot': {'tools': ['hover'], 'width': 1000}}})
    hv.opts({'HLine': {'color': 'black', 'line_width': 1, 'alpha': 0.5}})
except:
    pass

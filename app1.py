"""Script to generate a classification of multiple images and show the images and
their classification as a gallery. The current method uses Dash with python
 (and flask).
 To put in production do:
 gunicorn image_upload_gallery_classify:server -b :7070 -t 1000
"""

import base64
import os
# import sh
from flask import Flask

import dash
import dash_auth # Use only as a secure option
from dash.dependencies import Input, Output, State
import dash_core_components as dcc
import dash_html_components as html
import time


import plotly.graph_objs as go

import numpy as np
from collections import Counter

## IMPORT THE MODEL HERE========================



## =============================================


USERNAME_PASSWORD = [['team14', 't34m14']] # Use only as a secure option

# Detecting and/or making the current image path
CURRENT_FOLDER = os.path.dirname(os.path.realpath(__file__))
UPLOAD_DIRECTORY = os.path.join(CURRENT_FOLDER, 'app_uploaded_files')
# PREDICTIONS_DICT = dict()


# Defining the styles of the boxes and their labels
SPAN_STYLE = {
        'background': 'none repeat scroll 0 0 #4D57DB',
            'border': '2px solid #ffffff',
            'border-radius': '25px',
            'color': 'White',
            'font-size': '20px',
            'font-weight': 'bold',
            'padding': '5px 15px',
            'position': 'absolute',
            'left': '-5px',
            'top': '-25px'
        }

BOX_STYLE = {
        'color':'green', 'border':'2px #4D57DB solid',
        'margin':'3%', 'padding':'3%',
        'position': 'relative',
        'display': 'inline-block', 
        'margin-top': 30, 
        'margin-bottom': 20,
        'margin-right':'2%',
        'margin-left':'2%',
        'width': '90%'
        }


#Creating image folders
if not os.path.exists(UPLOAD_DIRECTORY):
    os.makedirs(UPLOAD_DIRECTORY)

# external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
external_stylesheets = [
    # Normalize the CSS
    "https://cdnjs.cloudflare.com/ajax/libs/normalize/7.0.0/normalize.min.css",
    # Fonts
    "https://fonts.googleapis.com/css?family=Open+Sans|Roboto"
    "https://maxcdn.bootstrapcdn.com/font-awesome/4.7.0/css/font-awesome.min.css",
    # For production
    "https://cdn.rawgit.com/xhlulu/0acba79000a3fd1e6f552ed82edb8a64/raw/dash_template.css",
    # Custom CSS
    "https://cdn.rawgit.com/xhlulu/dash-image-processing/1d2ec55e/custom_styles.css",
]

# Normally, Dash creates its own Flask server internally. By creating our own,
# we can create a route for downloading files directly:
server = Flask(__name__)
app = dash.Dash(__name__, server=server, external_stylesheets=external_stylesheets)

# Use only as a secure option
auth = dash_auth.BasicAuth(app, USERNAME_PASSWORD)

# If you are assigning callbacks to components that are generated by other
# Callbacks (and therefore not in the initial layout), then you can suppress
# this exception by setting
app.config['suppress_callback_exceptions']=True

#_______________________________LAYOUT__________________________________________

# MAIN LAYOUT
app.layout = html.Div([

    # Banner
    html.Div([
        html.H2(
            'Blood Cell Classification',
            id='title',style={'color':'White'}
        ),
        html.Img(
            src=app.get_asset_url("logods4all.svg"),
            # style={'backgroundColor':'Purple'}
        )
    ],
        className="banner",
        style={'color':'Black'}
    ),

    #  Image Uploader
    html.Div(className="container",
        children=[

            #Upload Images
            dcc.Upload(
            id='upload-image',
            children=html.Div([
                'Drag and Drop or ',
                html.A('Select Files'),
            ]),
            style={
                'width': '90%',
                'height': '60px',
                'lineHeight': '60px',
                'borderWidth': '1px',
                'borderStyle': 'dashed',
                'borderRadius': '25px',
                'textAlign': 'center',
                'marginBottom':'10px',
                'marginLeft':'50px',
                #'margin' : 'auto',
            },
            # Allow multiple files to be uploaded
            multiple=True,
            accept='image/*'
        ),

        html.Div(id='output-image-upload'),
        html.Div(id='tabs-content', style = {'margin':'auto'}),

        ],
            style={#'float':'right',
                   'float':'middle',
                   'width':'70%',
                   },
        ),


])


# _________________________End of Layout__________________________________
# ________________________________________________________________________


'''_________________________Image layout___________________________________'''

## -------------------Build the gallery----------------------
def parse_contents(contents, filename, prediction):
    layout = html.Div([
        html.Div(className='gallery',
                 children=[
                     html.A(
                         target='_blank',
                         href=contents,
                         # HTML images accept base64 encoded strings in the same format
                         # that is supplied by the upload
                         children=html.Img(src=contents, width=360, height=363,
                                           style={'width': '100%',
                                                  'height': 'auto'})
                     ),
                    #  html.Div(filename,
                    #           style={'padding': 5,
                    #                  'textAlign': 'center',
                    #                  'font-size': '0.8em'}
                    #           ),
                 ],
                 style={
                     'margin': 5,
                     'border': '1px solid #ccc',
                     'float': 'left',
                     'width': 150,
                     'height': 150 # 190 if include filename
                     }
                 )
    ])

    return layout


'''______________________Image Uploader______________________'''

@app.callback(Output('output-image-upload', 'children'),
              [Input('upload-image', 'contents')],
              [State('upload-image', 'filename')])

def update_output(list_of_contents, list_of_names):

    global  PREDICTIONS_DICT, LABELS

    # Delete the previous files
    if os.listdir(UPLOAD_DIRECTORY):
        removefiles()

    # Save all the images
    if list_of_contents is not None:
        for c, n in zip(list_of_contents, list_of_names):
            save_file(n, c)

        # ==============Classification process ====================
        ## HAY QUE MODIFICAR LA FUNCION PREDICTION CON UN MODELO AJUSTADO Y NO RANDOM
        PREDICTIONS_DICT = prediction(UPLOAD_DIRECTORY)
        # Make the prediction dictionary with files and predictions
        #PREDICTIONS_DICT = dict(zip(files, predictions))
        # print(PREDICTIONS_DICT.values())

        # ========================================================

        # Unique labels
        LABELS = list(set(PREDICTIONS_DICT.values()))

        # Automatic Tabs infered from the LABELS
        children = html.Div([
                    dcc.Tabs( id="tabs", value='tab-0', 
                    children=[
                        dcc.Tab(label='Chart', value='tab-0'),
                        dcc.Tab(label='Classification', value='tab-1'),
                        ]
                        )
                    ])

        return children


'''______________________Tabs______________________'''

@app.callback(Output('tabs-content', 'children'),
              [Input('tabs', 'value')])

def render_content(tab):

    
    if tab == 'tab-0':
        
        # Count the frecuencies of each predicted label
        labels, values = count_images(PREDICTIONS_DICT)          

        out = html.Div([
            html.Div([
            html.Div([
                dcc.Graph(
                    figure={
                        'data':[
                            go.Bar(x=labels, y=values,
                                   textfont=dict(size=20))    
                    ],
                'layout':go.Layout(
                   title="Bar plot of predictions"
                    )
                }          
            )],
                className="six columns",
                 ),
           html.Div([
                dcc.Graph(
                    figure={
                        'data':[
                            go.Pie(labels=labels, values=values,
                                   textfont=dict(size=20))
                    ],
                'layout':go.Layout(
                   title="Pie chart of predictions"
                    )
                }          
            )],
                className="six columns"
            ),
        ], className="row")
        ])
        
        return out

    elif tab == 'tab-1':
        child = list()
        for l in LABELS:
            
            child.append( html.Div( children = show_test(l) +
            [html.Span(l, className = 'index', style = SPAN_STYLE)],
             className = 'box', style = BOX_STYLE
             )
            )

        return child


'''______________________XXX______________________'''

#Count amount of Images
def count_images(PD):
    d = Counter(PD.values())
    labels = list(d.keys())
    values = list(d.values())
    return labels, values


def save_file(name, content):
    #Decode and store a file uploaded with Plotly Dash.
    data = content.encode('utf8').split(b';base64,')[1]
    with open(os.path.join(UPLOAD_DIRECTORY, name), 'wb') as fp:
        fp.write(base64.decodebytes(data))

#remove function
def removefiles():
    """Remove all files inside the UPLOAD_DIRECTORY"""
    for the_file in os.listdir(UPLOAD_DIRECTORY):
        file_path = os.path.join(UPLOAD_DIRECTORY, the_file)
        try:
            if os.path.isfile(file_path):
                os.unlink(file_path)
                # elif os.path.isdir(file_path): shutil.rmtree(file_path)
        except Exception as e:
            print(e)


def encode_image(image_file):
    encoded = base64.b64encode(open(image_file, 'rb').read())
    return 'data:image/png;base64,{}'.format(encoded.decode())

def show_test(clase):
    children = []
    for name,label in PREDICTIONS_DICT.items():
        if label == clase:
            # out.append(html.H4(name))
            contents = encode_image(os.path.join(UPLOAD_DIRECTORY, name))
            children.append(parse_contents(contents, name, label))
    return children

# Data Loading and prediction
@app.server.before_first_request
def load_model():
    global prediction
    print("\nLoading before first request\n")
    from production import prediction


if __name__ == '__main__':
    port = os.environ.get('dash_port')
    debug = os.environ.get('dash_debug')=="True"
    app.run_server(debug=debug, host="0.0.0.0", port=8050)
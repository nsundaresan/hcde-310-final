from flask import Flask, render_template, flash, redirect, request, url_for, send_file
from data import *
import time

import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__),"lib/python2.7/site-packages/"))

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/neighborhoods', methods=['GET', 'POST'])
def neighborhoods():
    neighborhoods = getNeighborhoods()
    selected = request.form.get("neighborhoods")
    if selected is not None:
        generateNeighborhoodPlot(str(selected))
    else:
        generateNeighborhoodPlot('Capitol Hill')
    timestamp=time.time()
    return render_template('neighborhoods.html', selected=selected, neighborhoods=neighborhoods, timestamp=timestamp)

@app.route('/byhouse', methods=['GET', 'POST'])
def byHouse():
    street = request.form.get("street-address")
    csz = request.form.get("city-state-zip")
    if (street is not None and street is not "") and (csz is not None and csz is not "") :
        myHouseInfo = getHouseInformation(street,csz)
        generateHousePlot(myHouseInfo)
    else:
        myHouseInfo = getHouseInformation('315 Howe St.', 'Seattle WA, 98109')
        generateHousePlot(myHouseInfo)
        street="315 Howe St."
        csz="Seattle WA, 98019"
    timestamp=time.time()
    return render_template('house.html', timestamp=timestamp, street=street, csz=csz)

@app.route('/about')
def about():
    return render_template('about.html')

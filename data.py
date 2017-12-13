import urllib, json, xmltodict, csv
import plotly.plotly as py
from plotly.offline import download_plotlyjs, init_notebook_mode, plot, iplot
from plotly.graph_objs import *
from api_keys import *
import numpy as np

def getHouseInformation(myaddress,mycitystatezip):
    """
    Using a user's address and city/state/zipcode, gives house information including:
    address, bath, bed, lat, long, price, and sqft.
    Parameters:
        myaddress: user's address [string]
        mycitystatezip: user's city/state/zipcode [string]
    Returns:
        dictionary(unnamed): contains all the mentioned details about a house, or the first house if
        address given is a building (apartment, townhome, condo)
    """
    try:
        url = 'https://www.zillow.com/webservice/GetDeepSearchResults.htm'
        params = {"zws-id":zillowAPIKey, "address":myaddress, "citystatezip":mycitystatezip}
        requesturl = url + "?" + urllib.parse.urlencode(params)
        requestxml = urllib.request.urlopen(requesturl)
        finaldata = xmltodict.parse(requestxml.read())
        if(type(finaldata["SearchResults:searchresults"]['response']['results']['result']) is list):
            return(extractHouseInformation(
                   finaldata["SearchResults:searchresults"]['response']['results']['result'][0]))
        else:
            return(extractHouseInformation(
                   finaldata["SearchResults:searchresults"]['response']['results']['result']))
    except:
        return('There was an error reaching the house information')


def extractHouseInformation(houseinfodict):
    """
    Taking a dictionary about a house's information, returns a condensed dictionary of
    only relevant information such as address, price, bed, bath, sqft, lat, and lon.
    Parameters:
        houseinfodict: dictionary containing ~all~ information about a house.
    Returns:
        houseInfo: dictionary containing condensed information about a house.
    """
    houseInfo = dict()
    houseInfo['address'] = houseinfodict['address']['street'] + ", " + houseinfodict['address']['city'] + \
    " " + houseinfodict['address']['state'] + ", " + houseinfodict['address']['zipcode']
    houseInfo['price'] = '$' + houseinfodict['zestimate']['amount']['#text']
    houseInfo['bed'] = houseinfodict['bedrooms']
    houseInfo['bath'] = houseinfodict['bathrooms']
    houseInfo['sqft'] = houseinfodict['finishedSqFt']
    houseInfo['lat'] = float(houseinfodict['address']['latitude'])
    houseInfo['lon'] = float(houseinfodict['address']['longitude'])
    return(houseInfo)


def getNeighborhoods():
    """
    Returns all neighborhoods for the city of Seattle.
    Parameters:
        None.
    Returns:
        list(unnamed): all the neighborhoods and their lat/lon information
    """
    try:
        url = 'http://www.zillow.com/webservice/GetRegionChildren.htm'
        params = {"zws-id":zillowAPIKey, "state":'WA', "city":'Seattle', 'childtype':'neighborhood'}
        requesturl = url + "?" + urllib.parse.urlencode(params)
        requestxml = urllib.request.urlopen(requesturl)
        responsedata = xmltodict.parse(requestxml.read())
        neighborhood_data = responsedata['RegionChildren:regionchildren']['response']['list']['region']

        final_data = dict()
        for neighborhood in neighborhood_data:
            final_data[neighborhood['name']] = {'lat': neighborhood['latitude'], 'lon': neighborhood['longitude']}

        return(final_data)
    except:
        return('There was an error reaching the neighborhoods')


def getSPDData():
    """
    Returns the information for all the crimes that occured in the last three months.
    Parameters:
        None.
    Returns:
        list(unnamed): all the crimes and their relevant information, including lat/lon
    """
    try:
        requesturl = 'https://data.seattle.gov/resource/y7pv-r3kh.json?$limit=5000&$order=date_reported%20DESC'
        request = urllib.request.Request(requesturl)
        request.add_header("X-API-Key", seattleAppToken)
        requestresponse = urllib.request.urlopen(request)
        finaldata = json.load(requestresponse)
        return(finaldata)
    except:
        return('There was an error reaching SPD data')


def getAttributeList(datalist):
    """
    Groups all lat, lon, and name information for crimes based on summarized_offense_description
    Parameters:
        datalist: list of all crimes [list]
    Returns:
        summary_dict: dictionary that contains lat, long, and name information grouped by
        summarized_offense_description
    """
    reader = csv.reader(open('offense_types.csv'))
    expanded_names = {}
    for row in reader:
        expanded_names[row[0]] = row[1]

    summary_dict = dict()
    for point in datalist:
        if 'summarized_offense_description' in point.keys():
            offense_name = point['summarized_offense_description']
            if point['offense_type'] in expanded_names.keys():
                expanded_name = expanded_names[point['offense_type']]
            else:
                expanded_name = point['offense_type']
            lat = point['latitude']
            lon = point['longitude']
            if point['summarized_offense_description'] in summary_dict.keys():
                summary_dict[offense_name]['lats'].append(lat)
                summary_dict[offense_name]['longs'].append(lon)
                summary_dict[offense_name]['names'].append(expanded_name)
            else:
                summary_dict[offense_name] = {'lats': [lat], 'longs': [lon], 'names': [expanded_name]}

    return(summary_dict)


def generateCrimePlots(crimeInfo):
    """
    Generates list of Scattermapbox objects that contains crime information for helping create plot.
    Parameters:
        crimeInfo: dictionary of all crimes grouped by summarized_offense_description
    Returns:
        scatter_list: list of Scattermapbox objects that plot points based on type of crime.
    """

    scatter_list = list()

    for crime in crimeInfo.keys():
        scatterplot = Scattermapbox(
            name = crime,
            lat = crimeInfo[crime]['lats'],
            lon = crimeInfo[crime]['longs'],
            mode = 'markers',
            marker = Marker(
                size = 5
            ),
            text = crimeInfo[crime]['names'],
            hoverinfo = 'text'
        )
        scatter_list.append(scatterplot)

    return(scatter_list)


def generateHousePlot(myHouse):
    """
    Generates plot centered around a given address.
    Parameters:
        myHouse: dictionary that contains information about a house.
    Returns:
        url: the filepath of the generated plot.
    """
    myHousePlot = Scattermapbox(
            name=myHouse['address'],
            lat=[myHouse['lat']],
            lon=[myHouse['lon']],
            mode='markers',
            marker=Marker(
                size=12,
                symbol='star'
            ),
            text="Address: %s</br></br>Bedrooms: %s</br>Bathrooms: %s</br>Price: %s</br>Sq. Ft.: %s"%(myHouse['address'],
                    myHouse['bed'], myHouse['bath'], myHouse['price'], myHouse['sqft']),
            hoverinfo='text'
        )
    crimePlots = generateCrimePlots(getAttributeList(getSPDData()))
    data_points = [myHousePlot] + crimePlots
    data = Data(data_points)
    layout = Layout(
        autosize=True,
        hovermode='closest',
        margin=Margin(
                l=0,
                r=0,
                b=0,
                t=0,
                pad=0
            ),
        legend=dict(
            bgcolor='#202020',
            font=dict(
                color='#ffffff'
            )
        ),
        paper_bgcolor='#202020',
        mapbox=dict(
            style='dark',
            accesstoken=mapbox_access_token,
            bearing=0,
            center=dict(
                lat=myHouse['lat'],
                lon=myHouse['lon']
            ),
            pitch=0,
            zoom=15
        ),
    )

    fig = dict(data=data, layout=layout)
    url = plot(fig, filename='app/static/houseplot.html', auto_open=False, show_link=False)
    return(url)


def generateNeighborhoodPlot(neighborhood):
    """
    Generates plot centered around a given neighborhood.
    Parameters:
        neighborhood: dictionary that contains information about a neighborhood.
    Returns:
        url: the filepath of the generated plot.
    """
    neighborhood_data = getNeighborhoods()
    lat_lon = neighborhood_data[neighborhood]
    data = Data(generateCrimePlots(getAttributeList(getSPDData())))
    layout = Layout(
        autosize=True,
        hovermode='closest',
        margin=Margin(
                l=0,
                r=0,
                b=0,
                t=0,
                pad=0
        ),
        legend=dict(
            bgcolor='#202020',
            font=dict(
                color='#ffffff'
            )
        ),
        paper_bgcolor='#202020',
        mapbox=dict(
            style='dark',
            accesstoken=mapbox_access_token,
            bearing=0,
            center=dict(
                lat=lat_lon['lat'],
                lon=lat_lon['lon']
            ),
            pitch=0,
            zoom=13
        ),
    )

    fig = dict(data=data, layout=layout)
    url = plot(fig, filename='app/static/neighborhoodplot.html', auto_open=False, show_link=False)
    return(url)

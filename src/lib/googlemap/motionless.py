from urllib import quote 
import re

"""
    motionless is a library that takes the pain out of generating Google Static Map URLs.

    For example code and documentation see: 
        http://github.com/ryancox/motionless

    For details about the GoogleStatic Map API see: 
        http://code.google.com/apis/maps/documentation/staticmaps/

    If you encounter problems, log an issue on github. If you have questions, drop me an
    email at ryan.a.cox@gmail.com.

"""

"""

      Copyright 2010 Ryan A Cox - ryan.a.cox@gmail.com 

   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License. 

"""



__author__ = "Ryan Cox <ryan.a.cox@gmail.com>"
__version__ = "1.0"   

class Color(object):
    COLORS = ['black', 'brown', 'green', 'purple', 'yellow', 'blue', 'gray', 'orange', 'red', 'white']
    pat = re.compile("0x[0-9A-Fa-f]{6}|[0-9A-Fa-f]{8}")
    @staticmethod
    def is_valid_color(color):
        return Color.pat.match(color) or color in Color.COLORS
         

class Marker(object):
    SIZES =  ['tiny','mid','small']
    LABELS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    def __init__(self, size, color, label):
        if size and size not in Marker.SIZES:
            raise ValueError("[%s] is not a valid marker size. Valid sizes include %s" % (size,Marker.SIZES))
        if label and (len(label) <> 1 or not label in Marker.LABELS):
            raise ValueError("[%s] is not a valid label. Valid labels are a single character 'A'..'Z' or '0'..'9'"  % label)
        if color and color not in Color.COLORS:
            raise ValueError("[%s] is not a valid color. Valid colors include %s"  % ( color, Color.COLORS ))
        self.size = size
        self.color = color
        self.label = label

class AddressMarker(Marker):
    def __init__(self, address, size=None, color=None, label=None):
        Marker.__init__(self,size,color,label)
        self.address = address

class LatLonMarker(Marker):
    def __init__(self, lat, lon, size=None, color=None, label=None):
        Marker.__init__(self,size,color,label)
        self.latitude = lat
        self.longitude = lon

class Map(object):
    MAX_URL_LEN = 2048
    MAPTYPES = ['roadmap','satellite','hybrid','terrain']
    FORMATS = ['png','png8','png32','gif','jpg','jpg-baseline']
    MAX_X = 640
    MAX_Y = 640
    def __init__(self, size_x, size_y, maptype):

        self.base_url = 'http://maps.google.com/maps/api/staticmap?'
        self.size_x = size_x 
        self.size_y = size_y 
        self.sensor = False 
        self.format = 'png'
        self.maptype = maptype 

    def __str__(self):
        return self.generate_url()                        

    def check_parameters(self):
        if self.format not in Map.FORMATS:
            raise ValueError("[%s] is not a valid file format. Valid formats include %s" % (self.format,Map.FORMATS))
    
        if self.format not in Map.FORMATS:
            raise ValueError("[%s] is not a valid map type. Valid types include %s" % (self.maptype,Map.MAPTYPES))
        
        if self.size_x > Map.MAX_X or self.size_x < 1:
            raise ValueError("[%s] is not a valid x-dimension. Must be between 1 and %s" % (self.size_x,Map.MAX_X))

        if self.size_y > Map.MAX_Y or self.size_y < 1:
            raise ValueError("[%s] is not a valid y-dimension. Must be between 1 and %s" % (self.size_x,Map.MAX_Y))

    def _get_sensor(self):
        if self.sensor:
            return 'true'
        else:
            return 'false'

    def _check_url(self, url):
        if len(url) > Map.MAX_URL_LEN:
            raise ValueError("Generated URL is %s characters in length. Maximum is %s" % (len(url),Map.MAX_URL_LEN))

class CenterMap(Map):
    ZOOM_RANGE = range(1,21)
    def __init__(self, address=None, lat=None, lon=None, zoom=17, size_x=400, size_y=400, maptype='roadmap'):
        Map.__init__(self,size_x=size_x, size_y=size_y, maptype=maptype)                    
        if address: 
            self.center = quote(address)
        elif lat and lon:
            self.center = "%s,%s" % (lat,lon)
        else:
            self.center = "1600 Amphitheatre Parkway Mountain View, CA"
        self.zoom = zoom 

    def check_parameters(self):
        super(CenterMap,self).check_parameters()
        
        if self.zoom not in CenterMap.ZOOM_RANGE:
            raise ValueError("[%s] is not a zoom setting. Must be between %s and %s" % (self.size_x,min(CenterMap.ZOOM_RANGE),max(CenterMap.ZOOM_RANGE)))

    def generate_url(self):
        self.check_parameters();
        url = "%smaptype=%s&format=%s&center=%s&zoom=%s&size=%sx%s&sensor=%s" % (
            self.base_url,
            self.maptype,
            self.format,
            self.center,
            self.zoom,
            self.size_x,
            self.size_y,
            self._get_sensor())
    
        self._check_url(url)
        return url

class VisibleMap(Map):
    def __init__(self, size_x=400, size_y=400, maptype='roadmap'):
        Map.__init__(self,size_x=size_x, size_y=size_y, maptype=maptype)                    
        self.locations = []

    def add_address(self, address):
        self.locations.append(quote(address))

    def add_latlon(self, lat, lon):
        self.locations.append("%s,%s" % (quote(lat),quote(lon)))

    def generate_url(self):
        self.check_parameters();
        url = "%smaptype=%s&format=%s&size=%sx%s&sensor=%s&visible=%s" % (
            self.base_url,
            self.maptype,
            self.format,
            self.size_x,
            self.size_y,
            self._get_sensor(),
            "|".join(self.locations))

        self._check_url(url)
        return url

class DecoratedMap(Map):
    def __init__(self, size_x=400, size_y=400,maptype='roadmap',region=False,fillcolor='green',pathweight=None,pathcolor=None,):
        Map.__init__(self,size_x=size_x, size_y=size_y,maptype=maptype)                    
        self.markers = []
        self.fillcolor = fillcolor
	self.pathweight = pathweight
	self.pathcolor = pathcolor
        self.region = region
        self.path = []
        self.contains_addresses = False

    def check_parameters(self):
        super(DecoratedMap,self).check_parameters()
        
        if self.region and len(self.path) < 2: 
            raise ValueError("At least two path elements required if region is enabled")

        if self.region and self.path[0] <> self.path[-1]: 
            raise ValueError("If region enabled, first and last path entry must be identical")

        if len(self.path) == 0 and len(self.markers) == 0:
            raise ValueError("Must specify points in path or markers")

	if not Color.is_valid_color(self.fillcolor):
            raise ValueError("%s is not a valid fill color. Must be 24 or 32 bit value or one of %s" % (self.fillcolor,Color.COLORS))

	if self.pathcolor and not Color.is_valid_color(self.pathcolor):
            raise ValueError("%s is not a valid path color. Must be 24 or 32 bit value or one of %s" % (self.pathcolor,Color.COLORS))

    def _generate_markers(self):
        styles = set()
        data = {}
        ret = []
        # build list of unique styles
        for marker in self.markers:
            styles.add((marker.size,marker.color,marker.label)) 
        # setup styles/location dict   
        for style in styles:
            data[style] = []
        # populate styles/location dict   
        for marker in self.markers:
            if isinstance(marker,AddressMarker):
                data[(marker.size,marker.color,marker.label)].append(quote(marker.address))
            if isinstance(marker,LatLonMarker):
                location = "%s,%s" % (marker.latitude, marker.longitude)
                data[(marker.size,marker.color,marker.label)].append(location)
        # build markers entries for URL 
        for style in data:
            locations = data[style]
            parts = []
            parts.append("markers=")
            if style[0]:
                parts.append("size:%s"%style[0])
            if style[1]:
                parts.append("color:%s"%style[1])
            if style[2]:
                parts.append("label:%s"%style[2]) 
            for location in locations: 
                parts.append(location)
            ret.append("|".join(parts))
        return "&".join(ret) 

    def _can_polyencode(self):
        try:
            import gpolyencode 
        except:
            return False
        return not self.contains_addresses    
    
    def _polyencode(self):
        import gpolyencode 
        encoder = gpolyencode.GPolyEncoder()
        points = []
        for point in self.path:
            tokens = point.split(',')
            points.append((float(tokens[1]),float(tokens[0])))
        return encoder.encode(points)['points']

    def add_marker(self, marker):
        if not isinstance(marker,Marker):
            raise ValueError("Must pass instance of Marker to add_marker")
        self.markers.append(marker)     

    def add_path_address(self, address):
        self.contains_addresses = True
        self.path.append(quote(address))

    def add_path_latlon(self, lat, lon):
        self.path.append("%s,%s" % (quote(lat),quote(lon)))

    def generate_url(self):
        self.check_parameters();
        url = "%smaptype=%s&format=%s&size=%sx%s&sensor=%s" % (
            self.base_url,
            self.maptype,
            self.format,
            self.size_x,
            self.size_y,
            self._get_sensor())

        if len(self.markers) > 0:
            url = "%s&%s" % ( url, self._generate_markers())

        if len(self.path) > 0:
            url = "%s&path=" % url

            if self.pathcolor:
                url = "%scolor:%s|" % ( url, self.pathcolor)

            if self.pathweight:
                url = "%sweight:%s|" % ( url, self.pathweight)

            if self.region:
                url = "%sfillcolor:%s|" % ( url, self.fillcolor)

            if self._can_polyencode():
                url = "%senc:%s" % ( url, quote(self._polyencode()))
            else:
                url = "%s%s" % ( url, "|".join(self.path))

        self._check_url(url)

        return url

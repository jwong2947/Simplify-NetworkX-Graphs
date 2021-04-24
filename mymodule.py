# -*- coding: utf-8 -*-
"""
Created on Fri Feb 12 11:52:26 2021

@author: Jonathan Wong
"""

#conda install xlsxwriter, conda install pandas, conda install networkx, conda install geopy

import networkx as nx
import matplotlib.pyplot as plt
import pandas as pd
import math
import xlsxwriter
from geopy.exc import GeocoderTimedOut 
from geopy.geocoders import Nominatim 
from itertools import combinations

def find_median(l):
    mid = len(l) // 2
    return (l[mid] + l[~mid]) / 2

def variance(data, ddof=0): # gets variance of a list of numbers
    n = len(data)
    mean = sum(data) / n
    return sum((x - mean) ** 2 for x in data) / (n - ddof)

def stdev(data): # gets standard deviation of a list of numbers
    var = variance(data)
    std_dev = math.sqrt(var)
    return std_dev

def open_File(Filename): #takes a excel file from the save_file method and recreates the same graph with all the features
    File = pd.read_excel(Filename, sheet_name = "nodes") # file name is the xlsx file eg "USedges.csv"
    node = (File["id"]).to_list() #list of node ids
    x =(File["x"]).to_list() #list of x positions
    y =(File["y"]).to_list() # list of y postions

    cityboolean = (File["is_city"]).to_list() #attributes list
    cityname = (File["city_name"]).to_list() # attributes list
    
    File2 = pd.read_excel(Filename, sheet_name = "edges") # file name is the xlsx file eg "USedges.csv"
    u = (File2["u"]).to_list() #node 1 of edge
    v =(File2["v"]).to_list() #node 2 of edge
    distance = (File2["weight"]).to_list() # attributes
    gmvalue = (File2["gmv"]).to_list() #attributes
    
    G = nx.Graph()
    for i in range(len(node)): #recreates graph nodes
        id = node[i] 
        G.add_node(id,pos=(x[i],y[i]),is_city = cityboolean[i], city_name = cityname[i])
    
    for a in range(len(u)): #adds edges to graph
        G.add_edge(u[a], v[a], weight=float(distance[a]),gmv = float(gmvalue[a]))

    return G

def save_File(G, end_file = "data.xlsx"): # takes a graph and saves its nodes and edges to a excel file 
    node = []
    x = []
    y = []
    is_city = []
    city_name = []
    for i in G.nodes(data = True): # takes all the attributes and node id and appends to a list
        node.append(i[0])
        x.append(i[1]["pos"][0])
        y.append(i[1]["pos"][1])
        is_city.append(i[1]["is_city"])
        city_name.append(i[1]["city_name"])


    u = []
    v = []
    weight = []
    gmv = []
    for i in G.edges(data= True): # takes all the edges and its attributes to put to different lists
        u.append(i[0])
        v.append(i[1])
        weight.append(i[2]["weight"])
        gmv.append(i[2]["gmv"])

    #print(dataframe)
    #df = pd.DataFrame([node,pos,is_city,city_name]) 
    df = pd.DataFrame(list(zip(node, x,y,is_city,city_name)), #dataframe matrix of the data for nodes
               columns =['id', 'x',"y","is_city","city_name"])

    df2 = pd.DataFrame(list(zip(u, v,weight,gmv)), #dataframe matrix for the graph matrix
               columns =['u', 'v',"weight","gmv"])


    writer = pd.ExcelWriter(end_file, engine='xlsxwriter')

# Convert the dataframe to an XlsxWriter Excel object.
    df.to_excel(writer, sheet_name='nodes')
    df2.to_excel(writer, sheet_name='edges')


# Close the Pandas Excel writer and output the Excel file.
    writer.save()
    

def draw_gravity_model(G): # draws the graph with the gravity model values as the color of edges, darker means higher value
    edges,weights = zip(*nx.get_edge_attributes(G,'gmv').items())
    l = []
    
    m = sorted(weights) # sorts the list
    Q1 = 0
    Q3 = 0  
    IQR = 0 #interquartile 
    if len(m) % 2 == 0: #even number list
        h = int(len(m) / 2)
        Q1 = find_median(m[:h])
        Q3 = find_median(m[h:])
        IQR = Q3 - Q1
    else: # odd number list
        h1 = int(len(m) / 2)
        h2 = int((len(m) / 2) + 1)
        Q1 = find_median(m[:h1])
        Q3 = find_median(m[h2:])
        IQR = Q3 - Q1
    #print((Q1,Q3,IQR))
    n = [x for x in m if (x > Q1 - (1.5*IQR) and x < Q3 + (1.5*IQR))] # gets list without outliers
    maximum = max(n)
    
    for i in weights:
        if i > Q3 + (1.5*IQR): # highlights outliers in red
            l.append("red")         
        else: 
            if i == 0: # highlights values without a value of 0 blue
                l.append("blue")
            elif i < (maximum/3) and i > 0:
                l.append("green")
            elif i >= maximum/3 and i < maximum/3*2:
                l.append("yellow")
            elif i >= maximum/3*2:
                l.append("orange")

            
    #print(maximum)
    l = tuple(l) # converts to tuple so it can be used in nx.draw
    #print(sorted(weights))
    #print(l)
    pos = nx.get_node_attributes(G, 'pos')
    nx.draw(G, pos, node_size = 0, node_color='b', edgelist=edges, edge_color=l, width=5.0)
        
def input_gravity_model(G, Filename): # takes a xlsx file with from and to cities as well as their populations and calcuates the gravity model value between them using hte shortest path distance
    File = pd.read_excel(Filename) # file name is the xlsx file eg "USedges.csv"
    city = (File["city"]).to_list()
    country =(File["country"]).to_list()
    pop = (File["population"]).to_list()
    key = dict(zip(city, pop))
    
    distinct_pairs = list(combinations(city, 2)) # gets all possible pairs, order does not matter
    list1 =[]
    
    for i in distinct_pairs:
        
        c1 = [j for j in G.nodes if G.nodes[j]["city_name"] == i[0]] # gets first city id num
        c2 = [x for x in G.nodes if G.nodes[x]["city_name"] == i[1]] # gets 2nd city id num
            
        if nx.has_path(G,c1[0],c2[0]): 
            #print(c1,c2)
            length = nx.shortest_path_length(G,c1[0],c2[0], weight = "weight") #distance between both places
                
            pop1 = key[i[0]] #population of place 1
            pop2 = key[i[1]] # population of place 2
            
            gmv = pop1*pop2 / (length**2) # gravity model value, can change easily if needed
                
            path = nx.shortest_path(G,c1[0],c2[0], weight = "weight") # list of the nodes from one city to another
            list1.append((gmv,path))  
       
    
    
    for i in list1:
        for j in range(len(i[1])-1): # loops between all adjacent pairs in the shortest paths, adds values onto to all the edges in the path
            u = i[1][j]
            v = i[1][j+1]
            d = float(G[u][v]["gmv"])
            G[u][v]["gmv"] = float(d + i[0])    
    

    return None

def find_clusters(G,n,r): # finds clusters within a graph if it a node has a certain amount of nodes within a radius
    all_nodes = []
    target_nodes = []
    for i in list(G.nodes):
        g = nx.ego_graph(G,i,radius = r, undirected = True, distance = "weight") # gets the subgraph within the radius
        if len(list(g.nodes)) > n and i not in target_nodes and i not in all_nodes:
            target_nodes.append(i)
            
            for j in list(g.nodes):
                if j not in all_nodes:
                    all_nodes.append(j)
    return target_nodes


def open_file_from_gis(filename): # function makes a graph from a csv of edges, each file has 5 columns: x coordinate of start node, y coordinate of start node, x coordinate of end node, y coordinate of end node and distance of edge 
    File = pd.read_csv(filename) # file name is the csv file eg "USedges.csv"
    x_start = (File["x1"]).to_list()
    y_start = (File["y1"]).to_list()
    x_end = (File["x2"]).to_list()
    y_end = (File["y2"]).to_list()
    length = (File["length"]).to_list()
    G = nx.Graph()
    
    nodes = []
    edges = []

    for i in range(len(x_start)): # loop makes gets the x,y coordinates of each node pair of the edges and adds it to a list
        node_cord = (x_start[i],y_start[i])
        node_cord2 = (x_end[i],y_end[i])
        if node_cord not in nodes:
            nodes.append(node_cord)
        if node_cord2 not in nodes:
            nodes.append(node_cord2)
            
    for i in range(len(x_start)): # adds the edges to a edgelist to be added to networkx graph, uses index to name each node
        u = (x_start[i],y_start[i])
        v = (x_end[i],y_end[i])
        index1 = nodes.index(u)
        index2 = nodes.index(v)
        edges.append((index1,index2,length[i]))
    
    for i in range(len(nodes)): # adds node
        G.add_node(i,pos=(tuple(nodes[i])),is_city = False, city_name = "")
    
    for i in edges: # adds edges
        G.add_edge(i[0],i[1],weight = i[2],gmv = 0)
        
        
    return G




def print_stats(G): #prints stats
    num_nodes = len(list(G.nodes))
    degree_list = [x[1] for x in G.degree]
    mean_degree = sum(degree_list) / num_nodes
    max_degree = max(degree_list)
    num_arcs = len(list(G.edges))
    total_arc_length = []
    for i in list(G.edges):
        total_arc_length.append(G[i[0]][i[1]]["weight"])
    avg_arc_length = sum(total_arc_length) / len(total_arc_length)
    max_arc = max(total_arc_length)
    min_arc = min(total_arc_length)
    std_dev = stdev(total_arc_length)
    
    print("Number of Nodes in the Graph is " + str(num_nodes))
    print("Mean Degree is " + str(mean_degree))
    print("Max degree of all Nodes is " + str(max_degree))
    print("Total amount of arcs is " + str(num_arcs))
    print("Average Arc Length is " + str(avg_arc_length))
    print("Max Arc Length is " + str(max_arc))
    print("Min Arc Length is " + str(min_arc))
    print("Standard Deviation is " + str(std_dev))
    
    

def check_cities(Filename,G): # draws the original graph and then the nodes of the cities you want to check on top to check if all the nodes lie on the graph
    File = pd.read_excel(Filename) # file name is the xlsx file eg "USedges.csv"
    lat = (File["lat"]).to_list()
    long = (File["long"]).to_list()
    #lat2 = (File[""]).to_list()
    #long2 = (File[""]).to_list()
    city = (File["city"]).to_list()
    #city2 =(File[""]).to_list()

    node_list = []
    for (x,y,c) in zip(long,lat,city): # takes the 3 lists and makes a tuple list of the 3 numbers
        if (x,y,c) not in node_list:
            node_list.append((x,y,c))
    
    
    g = nx.Graph()
    for i in range(len(node_list)): # adds to the graph
        g.add_node(node_list[i][2],pos=(node_list[i][0],node_list[i][1]))
      
    #draws the original graph and then the new graph on top to see if the all the cities lie on the graph
    nx.draw(G, nx.get_node_attributes(G, 'pos'), node_size=50, with_labels=False, node_color='r', font_size=0, node_shape='o')
    nx.draw(g, nx.get_node_attributes(g,"pos"),node_size=50,with_labels = True, node_color='b', font_size = 20,node_shape='o')
        

def input_cities(G,Filename): # checks long and lat points of the cities and finds the closest one on the graph to it. Defines a new feature called city_name
    File = pd.read_excel(Filename) # file name is the xlsx file eg "USedges.csv"
    lat = (File["lat"]).to_list()
    long = (File["long"]).to_list()
    #lat2 = (File[""]).to_list()
    #long2 = (File[""]).to_list()
    cities = (File["city"]).to_list()
    #city2 =(File[""]).to_list()

    city = []
    city_list = {}
    
    for (n,x,y) in zip(cities,long,lat):
        if (n,x,y) not in city:
            city.append((n,x,y))
  
    #for (n,x,y) in zip(name,lat2,long2):
        #if (n,x,y) not in city:
            #city.append((n,x,y))
    
    #print(city)
    
    for i in city:
        x,y = i[1],i[2] # latitude and longitude of the city
        lowest = 1000000000 
        c = city[0][0] # base case , sets first one as the closest node
        g = nx.get_node_attributes(G,'pos')
        for j in g:
            x1,y1 = g[j]
            d = math.sqrt((x-x1)**2 + (y-y1)**2) # finds distance between city and each node on the graph location
            if d <= lowest and j not in city_list: # want to find the point with the lowest distance and set it to it 
                c = j
                lowest = d
        city_list[c] = i[0]
    for i in city_list: # changes the name of the node to the city name and updates the node attribute as a city
        G.nodes[i]["is_city"] = True
        G.nodes[i]["city_name"] = city_list[i]

def remove_degrees_2(G): # function checks for all nodes of degree 2 and removes them
    
    g = G.copy()
    
    test_list = [k for k in g.nodes() if (g.degree(k) == 2 and g.nodes[k]["is_city"] == False)] # generates a list of all nodes with a degree of 2
    
    for i in test_list:
        list1 = list(sum(g.edges(i), ())) # gets the edges in a form of a list 
        n1, n2 = [x for x in list1 if x != i] # gets the two nodes beside the node of degree 2
        length = g[n1][i]["weight"] + g[n2][i]["weight"] # gets the 2 distances of the 2 edges and adds them together
        
        
        #speednew = ( g[n1][i]["speed"] +  g[n2][i]["speed"] ) / 2
        if g.has_edge(n1,n2) == False: # does not draw over existing edges, preserve existing paths
            g.add_edge(n1,n2,weight = length, gmv = 0)
            g.remove_node(i)
                    
    return g
    

def remove_Cluster(G,target_node,r):
    g = nx.ego_graph(G,target_node,radius = r, undirected = True, distance = "weight") # gets the subgraph within the radius

    node_list = list(g.nodes) # gets list of nodes around the supernode within the radius
    cities = [x for x in node_list if G.nodes[x]["is_city"] == True] # gets a list within the nodes that are cities
    target_list = [] # list of nodes that have 1 edge connecting to a node outside the radius
    keep_list = [] # list of nodes that we want to keep inside the radius
    remove_list = [] # list of nodes within the radius that will be removed
    check_list = [] # list of nodes inside the radius that have 2 edges connecting to 2 diff nodes outside the radius
    check_list2 = []
    
    keep_list = keep_list + cities # want to keep cities
    if target_node not in keep_list:
        keep_list.append(target_node)# adds center node to the keep list
    check_nodes = [x for x in node_list if x not in keep_list] # gets nodes that are not city nodes or the target node
    for i in check_nodes: # loops through list of nodes to check
        e = list(G.edges(i))
        num_outside_nodes = len([x[1] for x in e if x[1] not in node_list])    
        if num_outside_nodes > 2:
            keep_list.append(i)
        elif num_outside_nodes == 2:
            check_list.append(i)
        elif num_outside_nodes == 1:
            target_list.append(i)
        elif num_outside_nodes == 0:
            remove_list.append(i) 
        
    for i in check_list:
        outside_nodes = [x for x in (list(sum(list(G.edges(i)), ()))) if x not in node_list] # returns the nodes connected to the specific node that are not in the list of nodes within the radius of the target node
        path = nx.shortest_path(G, source = outside_nodes[0] , target = outside_nodes[1], weight = "weight") # finds the shortest path between the two nodes outside the radius
        if set(path) != set([outside_nodes[0],outside_nodes[1],i]): #checks to see if the shortest path between the two outside nodes are the 2 and the specific node
            for n in outside_nodes: # loops through each outside node
                path_to_center = nx.shortest_path(G, source = i, target = target_node, weight = "weight") # finds the shortest path between the two nodes outside the radius
                closest_keep = [p for p in path_to_center if p in keep_list] # gets the list of nodes in the pathway that does                
                for j in closest_keep:
                    if not(G.has_edge(j,n)):
                        new_dist = G[i][n]["weight"] + nx.shortest_path_length(G, source = i, target = j, weight = "weight") # finds the shortest path between the two nodes outside the radius
                        G.add_edge(n,j,weight = new_dist, gmv = 0)
                        break
        else:
            keep_list.append(i)
            check_list2.append(i)
            
    for i in target_list:
        node = [x for x in (list(sum(list(G.edges(i)), ()))) if x not in node_list] # returns the nodes connected to the specific node that are not in the list of nodes within the radius of the target node
        n = node[0]
        path_to_center = nx.shortest_path(G, source = i, target = target_node, weight = "weight")
        closest_keep = [p for p in path_to_center if p in keep_list] # gets the list of nodes in the pathway that does
        for j in closest_keep:
            if not(G.has_edge(j,n)):
                new_dist = G[i][n]["weight"] + nx.shortest_path_length(G, source = i, target = j, weight = "weight") # finds the shortest path between the two nodes outside the radius
                G.add_edge(n,j,weight = new_dist, gmv = 0)
                break
        
    for i in keep_list: # for nodes inside the radius but not directly connected to the center node, ensures there is a path to it
        path = nx.shortest_path(G, i, target_node, weight = "weight")
        if not(all(item in keep_list for item in path)):
            length = nx.shortest_path_length(G, i , target_node, weight = "weight")
            G.add_edge(i,target_node, weight = length, gmv = 0)
        
    for i in check_list2:
        check_list.remove(i)
    
    G.remove_nodes_from(target_list)
    G.remove_nodes_from(remove_list)     
    G.remove_nodes_from(check_list)      
    
    
def find_remove_clusters(G, city_radius, node_radius,node_threshold ):
    city_list = [x[0] for x in list(G.nodes(data = True)) if G.nodes[x[0]]["is_city"] == True] # gets a list of the city nodes 

    for i in city_list: 
        remove_Cluster(G,i,city_radius) # removes clusters using cities as supernodes
    check = find_clusters(G,node_threshold,node_radius)
    for i in check:
        remove_Cluster(G,i,node_radius) # checks else where and removes clusters outside city range
 
def findGeocode(city): 
       
    # try and catch is used to overcome 
    # the exception thrown by geolocator 
    # using geocodertimedout   
    try: 
          
        # Specify the user_agent as your 
        # app name it should not be none 
        geolocator = Nominatim(user_agent="your_app_name") 
          
        return geolocator.geocode(city) 
      
    except GeocoderTimedOut: 
          
        return findGeocode(city)      
 
def get_locations(filename, end_file = "getlocations.xlsx"):
    File = pd.read_excel(filename, sheet_name = 0) # file name is the csv file eg "USedges.csv"
    CityList = list(File["city"])
    CountryList = list(File["country"])
    Population = list(File["population"])

    
    long = [] 
    lat = [] 


    for i,j in zip(CityList,CountryList): 
          
        if findGeocode(i) != None: 
               
            loc = findGeocode(i + " " + j) 
              
            # coordinates returned from  
            # function is stored into 
            # two separate list 
            lat.append(loc.latitude) 
            long.append(loc.longitude) 
           
        # if coordinate for a city not 
        # found, insert "NaN" indicating  
        # missing value  
        else: 
            lat.append("nan") 
            long.append("nan") 
                
       
        
    
    df = pd.DataFrame(list(zip(CityList, CountryList,Population, lat, long)), 
               columns =["city", 'country',"population",'lat','long']) 


    writer = pd.ExcelWriter(end_file, engine='xlsxwriter')

# Convert the dataframe to an XlsxWriter Excel object.
    df.to_excel(writer, sheet_name='Sheet1')

# Close the Pandas Excel writer and output the Excel file.
    writer.save()




























 

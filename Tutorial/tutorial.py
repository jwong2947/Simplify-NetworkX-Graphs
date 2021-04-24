# -*- coding: utf-8 -*-
"""
Created on Mon Apr  5 16:07:11 2021

@author: Jonathan Wong
"""

import mymodule as m
import networkx as nx
import matplotlib.pyplot as plt
import pandas as pd


fsize = (25,18) # resolution for drawing the graph

#step 1 : import graph

G = m.open_file_from_gis("USedges.csv")
plt.figure(figsize=fsize) # use this everytime you want to draw a new graph that doesnt overlap with the previous one
nx.draw(G, nx.get_node_attributes(G, 'pos'), node_size=100, with_labels=True, node_color='r', font_size=0, node_shape='o')

#step 2 : import the cities into the graph

plt.figure(figsize=fsize)
m.input_cities(G,"US Cities Location.xlsx") # the function that adds the cities to the graph
m.check_cities("US Cities Location.xlsx",G) # makes a seperate graph that draw the 2 overlapping each other to check if all cities are on the same graph, if cities are not on the graph, you must go to excel file with the cities and either change or remove it
m.print_stats(G) # prints stats
print("--------------------------")



#step 3 : Simpifly by removing degree 2 nodes
plt.figure(figsize=fsize)

city_list = [x[0] for x in list(G.nodes(data = True)) if G.nodes[x[0]]["is_city"] == True] # gets a list of the city nodes 
F = m.remove_degrees_2(G) # removes degree 2 nodes
nx.draw(F, nx.get_node_attributes(F, 'pos'), node_size=100, with_labels=True, node_color='r', font_size=0, node_shape='o')
nx.draw_networkx_nodes(F, nx.get_node_attributes(F,"pos"),nodelist = city_list,node_size=100,node_color='b', node_shape='o') # draws the cities to show where they are
m.print_stats(F)
print("--------------------------")


#step 4 : remove clusters of nodes
plt.figure(figsize=fsize)
m.find_remove_clusters(F,100000,50000,5)
    
nx.draw(F, nx.get_node_attributes(F, 'pos'), node_size=100, with_labels=True, node_color='r', font_size=0, node_shape='o')
nx.draw_networkx_nodes(F, nx.get_node_attributes(F,"pos"),nodelist = city_list,node_size=100,node_color='b', node_shape='o')
m.print_stats(F)
print("--------------------------")


#step 5 : input the gravity model
plt.figure(figsize=fsize)

m.input_gravity_model(F, "US Cities Location.xlsx") # inputs the gravity model into the graph
m.draw_gravity_model(F) # draws the graph with the gravity model


#saves file for future use
m.save_File(F, "US data.xlsx")

plt.show() #shows plots

# to access file

# g = m.open_File("US data. xlsx)
# can perform any functions easily, faster load time

# if need to get latitude and longitude of cities in a country
# do 
# get_locations("US Cities.xlsx, end_file = "getlocations.xlsx")




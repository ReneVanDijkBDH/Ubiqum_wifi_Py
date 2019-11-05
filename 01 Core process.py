# -*- coding: utf-8 -*-
"""
Created on Mon Nov  4 09:53:15 2019

@author: renev
"""
import pandas as pd 
import numpy as np
from random import sample
from sklearn.model_selection import train_test_split


#########################################################################
## Author:    René van Dijk
## Creation:  4-10-2019
## Purpose:   This functions re-scales the RSSI-values in dbm to a better
##            usefull scale
##            current dbm           converted value
##               0 dbm (best)       105
##               :                  :
##            -104 dbm (poor)       1
##             100 dmb (no signal)  0
#########################################################################
def RescaleRSSI(DataBuilding):
    LoopCol = len(DataBuilding.columns)-1
    while LoopCol >= 0:
        if DataBuilding.columns[LoopCol][0:3]=="WAP":
            DataBuilding.iloc[:,LoopCol] = np.where(DataBuilding.iloc[:,LoopCol] == 100,
                             0,
                             DataBuilding.iloc[:,LoopCol] + 105)
        LoopCol = LoopCol -1
    return DataBuilding

#########################################################################
## Author:    René van Dijk
## Creation:  10-10-2019
## Purpose:   convert dataframe to have all the WAP-signals vertically in 1 column.
##            There current dataframe has 2 different parts:
##            1) fixed attributes (user, phone etc) which should be in every record
##            2) 520 WAP's which should be converted from horizontal to vertical
#########################################################################
def ConvertToVerticalData(HData):
    # Fix attributes that should be in every record
    # All except WAP-columns
    FixedAttributes = pd.DataFrame(HData, columns=('ObservationID','LONGITUDE','LATITUDE','FLOOR','BUILDINGID',
                                    'SPACEID','RELATIVEPOSITION','USERID','PHONEID','TIMESTAMP'))

    #loop through all columns of the dataset
    LoopCol =0

    while LoopCol< len(HData.columns)-1: 
        #if columname start with WAP... then add to vertical dataframe
        if HData.columns[LoopCol][0:3]=="WAP":
            print(HData.columns[LoopCol])
            tempData = FixedAttributes
            tempData['WAP'] = HData.columns[LoopCol]
            tempData['WAPSignal'] = HData.iloc[:,LoopCol]
      
            #remove all records without signal
            tempData = tempData[tempData['WAPSignal']>0]
     
            #add to total dataset
            if LoopCol==0:
                VData = tempData
            else:
                VData = pd.concat([VData,tempData])
        
        LoopCol=LoopCol+1
    return(VData)

#########################################################################
## Author:    René van Dijk
## Creation:  10-10-2019
## Purpose:   create a list of all WAP's 
##            for every WAP calculate it's location
##            remove dirty data for this (users 6 & 14, high signals)
#########################################################################
    
def CreateWAPList(VData):
    #VData <- readRDS('../Data/clean_data/trainingVert.rds')
    
    #remove signals which are dirty
    VData = VData[(VData.USERID !=6) & (VData.USERID !=14) & (VData.WAPSignal<80) & (VData.WAPSignal >0) ]
    
    #create list of all WAP's
    WAPList = VData.groupby('WAP').agg(
            count = pd.NamedAgg(column='WAPSignal', aggfunc='count'),
            max   = pd.NamedAgg(column='WAPSignal', aggfunc = max))  
    WAPList.reset_index(inplace=True)

    # group by longitude and WAP 
    VLong = VData.groupby(['WAP','LONGITUDE']).agg(
            avg = pd.NamedAgg(column='WAPSignal', aggfunc='mean'),
            mx  = pd.NamedAgg(column='WAPSignal', aggfunc='max'))
    VLong.reset_index(inplace=True)
    
    #additional calculations required for exponential weigheted average
    VLong['avg']        = np.exp(VLong['avg'])
    VLong['mx']         = np.exp(VLong['mx'])
    VLong['avglong']    = VLong['avg'] * VLong['LONGITUDE']
    VLong['mxlong']     = VLong['mx']  * VLong['LONGITUDE'] 
    
    # Weighted average of Longitude per WAP
    VLongWAP = VLong.groupby(['WAP']).agg(
            avgsum      = pd.NamedAgg(column='avg',     aggfunc='sum'),
            avglongsum  = pd.NamedAgg(column='avglong', aggfunc='sum'),
            mxsum       = pd.NamedAgg(column='mx',      aggfunc='sum'),
            mxlongsum   = pd.NamedAgg(column='mxlong',  aggfunc='sum'))
    VLongWAP.reset_index(inplace=True)        
    VLongWAP['Long_Max'] = VLongWAP['mxlongsum']  / VLongWAP['mxsum']
    VLongWAP['Long_Avg'] = VLongWAP['avglongsum'] / VLongWAP['avgsum']    
    
    # add resulting weighted averages to WAPList
    WAPList = pd.merge(WAPList, VLongWAP[['WAP','Long_Max','Long_Avg']], left_on='WAP', right_on='WAP', how='left')
    
     # group by latitude and WAP 
    VLat = VData.groupby(['WAP','LATITUDE']).agg(
            avg = pd.NamedAgg(column='WAPSignal', aggfunc='mean'),
            mx  = pd.NamedAgg(column='WAPSignal', aggfunc='max'))
    VLat.reset_index(inplace=True)
    
    #additional calculations required for exponential weigheted average
    VLat['avg']        = np.exp(VLat['avg'])
    VLat['mx']         = np.exp(VLat['mx'])
    VLat['avglat']    = VLat['avg'] * VLat['LATITUDE']
    VLat['mxlat']     = VLat['mx']  * VLat['LATITUDE'] 
    
    # Weighted average of Longitude per WAP
    VLatWAP = VLat.groupby(['WAP']).agg(
            avgsum      = pd.NamedAgg(column='avg',     aggfunc='sum'),
            avglatsum  = pd.NamedAgg(column='avglat',   aggfunc='sum'),
            mxsum       = pd.NamedAgg(column='mx',      aggfunc='sum'),
            mxlatsum   = pd.NamedAgg(column='mxlat',    aggfunc='sum'))
    VLatWAP.reset_index(inplace=True)        
    VLatWAP['Lat_Max'] = VLatWAP['mxlatsum']  / VLatWAP['mxsum']
    VLatWAP['Lat_Avg'] = VLatWAP['avglatsum'] / VLatWAP['avgsum']    
    
    # add resulting weighted averages to WAPList
    WAPList = pd.merge(WAPList, VLatWAP[['WAP','Lat_Max','Lat_Avg']], left_on='WAP', right_on='WAP', how='left')

    return(WAPList)


#########################################################################
## Start Code
#########################################################################

#import data    
DataAllBuildings = pd.read_csv('../Data/trainingData.csv')

# add unique row ID for reference
DataAllBuildings['ObservationID'] = DataAllBuildings.index

# rescale signal values
DataAllBuildings = RescaleRSSI(DataAllBuildings)

#define dataset for modelling
DataModel = DataAllBuildings

#create training and test set
Observations = DataAllBuildings.index
training, testing, obs_train, obs_test = train_test_split(DataModel, Observations, test_size=0.25, random_state=455)

# Vertical data-set of Training 
trainingVert = ConvertToVerticalData(training)
#trainingVert.to_csv('../Data/clean_data/trainingVert.csv')

#Create WAPList
WAPList = CreateWAPList(trainingVert)

print('End of core process')
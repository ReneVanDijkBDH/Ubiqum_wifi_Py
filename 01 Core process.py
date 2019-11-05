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
    WAPList = VData.groupby('WAP').agg(
            count = pd.NamedAgg(column='WAPSignal', aggfunc='count'),
            max   = pd.NamedAgg(column='WAPSignal', aggfunc = max))  
    WAPList.reset_index(inplace=True)

    # group by longitude and WAP 
    VLong = VData.groupby(['WAP','LONGITUDE']).agg(
            avg = pd.NamedAgg(column='WAPSignal', aggfunc='mean'),
            mx  = pd.NamedAgg(column='WAPSignal', aggfunc='max'))
    VLong.reset_index(inplace=True)
        
            ,'max']}).rename(
            columns={'mean':'avg','max' : 'mx'})
    Vlong['avg'] = np.exp(VLong['avg'])
            
            summarise(avg= exp(mean(WAPSignal)), 
                      mx = exp(max(WAPSignal))) 

# group by longitude and WAP 
VLong <- VData %>%  
            filter(WAPSignal>0 & WAPSignal<80 & USERID!=14 & USERID!=6 ) %>%
            group_by(WAP, LONGITUDE) %>% 
            summarise(avg= exp(mean(WAPSignal)), 
                      mx = exp(max(WAPSignal))) %>%
            ungroup()

# Weighted average 
WAPList <- WAPList %>% left_join((VLong %>% 
  group_by(WAP) %>% 
  summarise(Long_Max = sum(mx*LONGITUDE)/sum(mx),
            Long_Avg = sum(avg*LONGITUDE)/sum(avg)) %>%
  ungroup()), "WAP")

# group by latitude and WAP 
VLat <- VData %>%  
  filter(WAPSignal>0 & WAPSignal<80 &USERID!=14 &USERID!=6) %>%
  group_by(WAP, LATITUDE) %>% 
  summarise(avg= exp(mean(WAPSignal)), 
            mx = exp(max(WAPSignal))) %>%
  ungroup()

# Weighted average 
WAPList <- WAPList %>% left_join((VLat %>% 
                                    group_by(WAP) %>% 
                                    summarise(Lat_Max = sum(mx*LATITUDE)/sum(mx),
                                              Lat_Avg = sum(avg*LATITUDE)/sum(avg)) %>%
                                    ungroup()), "WAP")
return(WAPList)
}


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

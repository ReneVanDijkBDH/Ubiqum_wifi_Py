# -*- coding: utf-8 -*-
"""
Created on Mon Nov  4 09:53:15 2019

@author: renev
"""
import pandas as pd 
import numpy as np
#from random import sample
from sklearn.model_selection import train_test_split
import matplotlib.pyplot as plt

#########################################################################
## Author:    René van Dijk
## Creation:  4-11-2019
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
## Creation:  04-11-2019
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
## Creation:  05-11-2019
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
## Author:    René van Dijk
## Creation:  06-11-2019
## Purpose:   return top 10 ranked signals per observation 
#########################################################################
def VertTop10(Vert):
    
    #remove high and no signals 
    Vert = Vert[(Vert.WAPSignal<80) & (Vert.WAPSignal >0) ]
    
    ObsIDs = Vert.groupby(['ObservationID']).agg(
            aant = pd.NamedAgg(column='ObservationID', aggfunc='count'))
    ObsIDs.reset_index(inplace=True) 

    loopID = 0
    while loopID < len(ObsIDs):
        print(loopID)
        ObsID= ObsIDs.iloc[loopID]['ObservationID']
        tempObs = Vert[Vert['ObservationID']==ObsID].nlargest(10,'WAPSignal').reset_index()
        tempObs['ranking'] = tempObs.index + 1
        
        if loopID==0:
            VertTop10 = tempObs
        else:
            VertTop10 = pd.concat([VertTop10,tempObs])
        loopID=loopID+1
    #VertTop10 <- VertTop10 %>% filter(ranking<=10)
    return(VertTop10)

#########################################################################
## Author:    René van Dijk
## Creation:  06-11-2019
## Purpose:   calculate longitude, Latitude and building 
##            per observation the WAP's with highest signals are given (VDataTop10)
##            the location of the WAP's is provided by the WAPList
##            a weighted average is used to calcultate longitude and latitude
#########################################################################

def PredictLongLatBuilding(VDataTop10,WAPList):

    # add information about WAP's to observations
    VDataTop10 = pd.merge(VDataTop10, WAPList, left_on='WAP', right_on='WAP', how='left')
    
    # remove observations where WAP is not found in WAPList (VLong_Max is null)
    VDataTop10 = VDataTop10[~VDataTop10.Long_Max.isnull()]
    
    #VDataTop10$SignalDif <- with(VDataTop10, maxSignal - WAPSignal)
    
    # filter out WAP's with too broad range to use them
    WAPExclude = ['WAP248', 'WAP508', 'WAP212', 'WAP018', 'WAP362', 
                  'WAP305', 'WAP413', 'WAP172', 'WAP449']
    VDataTop10 = VDataTop10[~VDataTop10.WAP.isin(WAPExclude)]
    
    # use only top n ranked WAP's
    VDataTop10 = VDataTop10[VDataTop10.ranking<=3]
    
    # addtional columns to support calculation of weighted averages
    VDataTop10['W_Long_Max'] = VDataTop10.WAPSignal * VDataTop10.Long_Max
    VDataTop10['W_Lat_Max']  = VDataTop10.WAPSignal * VDataTop10.Lat_Max
    VDataTop10['W_Long_Avg'] = VDataTop10.WAPSignal * VDataTop10.Long_Avg
    VDataTop10['W_Lat_Avg']  = VDataTop10.WAPSignal * VDataTop10.Lat_Avg
    
    # group per observation and calculate weigthed averages
    PredictObs = VDataTop10.groupby(['ObservationID', 'LONGITUDE', 'LATITUDE', 'BUILDINGID', 'FLOOR']).agg(
            S_Long_Max  = pd.NamedAgg(column='W_Long_Max',  aggfunc='sum'),
            S_Lat_Max   = pd.NamedAgg(column='W_Lat_Max',   aggfunc='sum'),
            S_Long_Avg  = pd.NamedAgg(column='W_Long_Avg',  aggfunc='sum'),
            S_Lat_Avg   = pd.NamedAgg(column='W_Lat_Avg',   aggfunc='sum'),
            S_WAPSignal = pd.NamedAgg(column='WAPSignal', aggfunc='sum'))
    PredictObs.reset_index(inplace=True) 
    PredictObs['PredictLong'] = PredictObs.S_Long_Max / PredictObs.S_WAPSignal
    PredictObs['PredictLat']  = PredictObs.S_Lat_Max  / PredictObs.S_WAPSignal
    PredictObs['Long_Avg']    = PredictObs.S_Long_Avg / PredictObs.S_WAPSignal
    PredictObs['Lat_Avg']     = PredictObs.S_Lat_Avg  / PredictObs.S_WAPSignal
    
    # calculate errors in longitude and latitude
    PredictObs['LongError'] = PredictObs.LONGITUDE - PredictObs.PredictLong
    PredictObs['LatError']  = PredictObs.LATITUDE -  PredictObs.PredictLat 

    # calculate building. based on location (defined by a line)
    PredictObs['PredictBuilding'] =np.where(PredictObs.PredictLat > 4876350 + PredictObs.PredictLong*1.506,
                                            0,
                                            np.where(PredictObs.PredictLat >4876000 + PredictObs.PredictLong* 1.506,
                                                     1,
                                                     2))
    # calculate error in building
    PredictObs['BuildingError'] = np.where(PredictObs.BUILDINGID==PredictObs.PredictBuilding,0,1)
    return(PredictObs)


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

# Vertical data-set of Training and top 10 ranked highest stignals
testingVert = ConvertToVerticalData(testing)
testingVertTop10 = VertTop10(testingVert)

testingResults = PredictLongLatBuilding(testingVertTop10,WAPList)

print('End of core process')


plt.plot(WAPList['Long_Max'], WAPList['Lat_Max'], 'ro',[-7503.32,-7237.72],[4864700,4865100],'b-',
         [-7735.72,-7470.12],[4864700,4865100],'b-')
plt.axis([-7700, -7300, 4864700, 4865100])
plt.show()


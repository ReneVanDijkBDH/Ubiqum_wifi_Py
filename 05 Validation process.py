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
## Start Code
#########################################################################

#import data    
DataValidation = pd.read_csv('../Data/validationData.csv')

# add unique row ID for reference
DataValidation['ObservationID'] = DataValidation.index

# rescale signal values
DataValidation = RescaleRSSI(DataValidation)

# Vertical data-set of Validation and top 10 ranked highest stignals
validationVert = ConvertToVerticalData(DataValidation)
validationVertTop10 = VertTop10(validationVert)

# calculate longitude, latitude and building per observation
validationResults = PredictLongLatBuilding(validationVertTop10,WAPList)

# list errors in building
validationResults[validationResults.BuildingError!=0]

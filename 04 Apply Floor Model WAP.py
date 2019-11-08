def ApplyFloorModelWAP(TestFloorVert, WAPList):

    # select top X WAP's for identifying f
    TopN = 5
    TestFloorVert['Weights'] = TestFloorVert.WAPSignal
    TestFloorVert = VertTopN(TestFloorVert, TopN)

    # distinct list WAP & Building
    TestTopWAP = TestFloorVert[TestFloorVert.WAPSignal>0].groupby('WAP').agg(
            TimesTest = pd.NamedAgg(column='WAPSignal', aggfunc='count'))  
    TestTopWAP.reset_index(inplace=True)
    
    #load different floor models
    #FloorModelKNN <- readRDS('../Data/clean_data/FloorModelWAPKNN.rds')
    #FloorModelRF <- readRDS('../Data/clean_data/FloorModelWAPRF.rds')

    # loop throug distinct list 
    loopWAP = 1
    while loopWAP <= len(TestTopWAP):
        WAPName = TestTopWAP.iloc[loopWAP-1,0] 
        WAPNr   = int(WAPName[3:6])
        print(WAPName)
        
        # select relevant records
        tempset = TestFloorVert[TestFloorVert.WAP==WAPName][['ObservationID','FLOOR','BUILDINGID', 
                              'LONGITUDE', 'LATITUDE', 'WAPSignal','Quadrant']]
        tempset = tempset.reset_index()
        tempset_Y = tempset[['FLOOR']]
        tempset_X = tempset[['LONGITUDE', 'LATITUDE', 'WAPSignal','Quadrant']]
          
        # get model
        tempmodel = ModelList[WAPNr-1]

        #tempmodelKNN <- FloorModelKNN[[WAPNr]]
        #tempmodelRF <- FloorModelRF[[WAPNr]]
        #KNNAccuracy<-tempmodelKNN$results$Accuracy[match(tempmodelKNN$bestTune$k,tempmodelKNN$results$k)]
        #RFAccuracy<-tempmodelRF$results$Accuracy[match(tempmodelRF$bestTune$mtry,tempmodelRF$results$mtry)]
        #if(is.null(KNNAccuracy) & is.null(RFAccuracy)) {
        #   tempmodel <- NA
        #} else if(is.null(KNNAccuracy)) {
        #    tempmodel<- tempmodelRF
        #} else if(is.null(RFAccuracy)) {
        #    tempmodel <- tempmodelKNN
        #} else if(KNNAccuracy>RFAccuracy) {
        #    tempmodel <- tempmodelKNN
        #} else {
        #    tempmodel <- tempmodelRF
        #}
  
        # predict floor
        if tempmodel !=0:
            FloorPredict = tempmodel.predict(tempset_X)
            FloorPredict = pd.DataFrame(data=FloorPredict)
            FloorPredict = FloorPredict.rename(columns = {0:"PredictFloor"})
            
            # add prediction to dataset
            tempset = pd.merge(tempset,pd.DataFrame(data=FloorPredict), left_index=True, right_index=True)
            
            if loopWAP==1:
                tempAllVert = pd.DataFrame(tempset)
            else: 
                tempAllVert = pd.concat([tempAllVert, pd.DataFrame(tempset)])
        loopWAP = loopWAP + 1 

    # add supporting columns
    tempAllVert['F0'] = np.where(tempAllVert.PredictFloor==0,1,0)
    tempAllVert['F1'] = np.where(tempAllVert.PredictFloor==1,1,0)
    tempAllVert['F2'] = np.where(tempAllVert.PredictFloor==2,1,0)
    tempAllVert['F3'] = np.where(tempAllVert.PredictFloor==3,1,0)
    tempAllVert['F4'] = np.where(tempAllVert.PredictFloor==4,1,0)
    
    # count how many time a floor results per observation
    tempAllObs = tempAllVert.groupby(['ObservationID','FLOOR']).agg(
            F0 = pd.NamedAgg(column='F0', aggfunc='sum'),
            F1 = pd.NamedAgg(column='F1', aggfunc='sum'),
            F2 = pd.NamedAgg(column='F2', aggfunc='sum'),
            F3 = pd.NamedAgg(column='F3', aggfunc='sum'),
            F4 = pd.NamedAgg(column='F4', aggfunc='sum'))  
    tempAllObs.reset_index(inplace=True)
    
    #find maximum number of counts per observation
    tempAllObs['maxFloorCount'] = tempAllObs[['F0','F1','F2','F3','F4']].max(axis=1)
    
    #find which floor has maximum count
    tempAllObs['Max1'] = np.where(tempAllObs.F0==tempAllObs.maxFloorCount,0,
                                          np.where(tempAllObs.F1==tempAllObs.maxFloorCount,1,
                                                 np.where(tempAllObs.F2==tempAllObs.maxFloorCount,2,
                                                        np.where(tempAllObs.F3==tempAllObs.maxFloorCount,3,4))))
    #find if an other column also has maximum count
    tempAllObs['Max2'] = np.where((tempAllObs.F1==tempAllObs.maxFloorCount) & (tempAllObs.Max1 < 1),1,
                                        np.where((tempAllObs.F2==tempAllObs.maxFloorCount) & (tempAllObs.Max1 < 2),2,
                                                np.where((tempAllObs.F3==tempAllObs.maxFloorCount) & (tempAllObs.Max1 < 3),3,
                                                       np.where((tempAllObs.F4==tempAllObs.maxFloorCount) & (tempAllObs.Max1<4),4,
                                                              -1))))
    #if both are the same only 1 max is found (-1)
    tempAllObs['MaxDif'] = np.where(tempAllObs.Max2== -1,0,tempAllObs.Max2 - tempAllObs.Max1)


    tempAllObs['PredictedFloor'] = -1
    tempAllObs.loc[(tempAllObs.MaxDif==0),'PredictedFloor'] = tempAllObs.Max1
    tempAllObs.loc[(tempAllObs.MaxDif==1) & (tempAllObs.Max2==1),'PredictedFloor'] = 1
    tempAllObs.loc[(tempAllObs.MaxDif==1) & (tempAllObs.Max2==2) & (tempAllObs.F0 > 0),'PredictedFloor'] = 1
    tempAllObs.loc[(tempAllObs.MaxDif==1) & (tempAllObs.Max2==2) & (tempAllObs.F0 == 0),'PredictedFloor'] = 2
    tempAllObs.loc[(tempAllObs.MaxDif==1) & (tempAllObs.Max2==3) & (tempAllObs.F4 > 0),'PredictedFloor'] = 3
    tempAllObs.loc[(tempAllObs.MaxDif==1) & (tempAllObs.Max2==3) & (tempAllObs.F4 == 0),'PredictedFloor'] = 2
    tempAllObs.loc[(tempAllObs.MaxDif==1) & (tempAllObs.Max2==4),'PredictedFloor'] = 3   
    tempAllObs.loc[(tempAllObs.MaxDif==2) & (tempAllObs.Max2==2) & (tempAllObs.F1 > 0),'PredictedFloor'] = 1
    tempAllObs.loc[(tempAllObs.MaxDif==2) & (tempAllObs.Max2==2) & (tempAllObs.F1 == 0),'PredictedFloor'] = 2    
    tempAllObs.loc[(tempAllObs.MaxDif==2) & (tempAllObs.Max2==3) & (tempAllObs.F0 > 0),'PredictedFloor'] = 1
    tempAllObs.loc[(tempAllObs.MaxDif==2) & (tempAllObs.Max2==3) & (tempAllObs.F0 == 0) & (tempAllObs.F2 > 0),'PredictedFloor'] = 2
    tempAllObs.loc[(tempAllObs.MaxDif==2) & (tempAllObs.Max2==3) & (tempAllObs.F0 == 0) & (tempAllObs.F2 == 0),'PredictedFloor'] = 3
    tempAllObs.loc[(tempAllObs.MaxDif==2) & (tempAllObs.Max2==4) & (tempAllObs.F3 > 0),'PredictedFloor'] = 3
    tempAllObs.loc[(tempAllObs.MaxDif==2) & (tempAllObs.Max2==4) & (tempAllObs.F3 == 0),'PredictedFloor'] = 2      
    tempAllObs.loc[(tempAllObs.MaxDif==3) & (tempAllObs.Max2==3) & (tempAllObs.F1 > 0),'PredictedFloor'] = 0
    tempAllObs.loc[(tempAllObs.MaxDif==3) & (tempAllObs.Max2==3) & (tempAllObs.F1 == 0),'PredictedFloor'] = 3
    tempAllObs.loc[(tempAllObs.MaxDif==3) & (tempAllObs.Max2==4) & (tempAllObs.F3 > 0),'PredictedFloor'] = 4
    tempAllObs.loc[(tempAllObs.MaxDif==3) & (tempAllObs.Max2==4) & (tempAllObs.F3 == 0),'PredictedFloor'] = 1    
    tempAllObs.loc[(tempAllObs.MaxDif==4),'PredictedFloor'] = tempAllObs.Max2

    tempAllObs['FloorError'] = np.where(tempAllObs.FLOOR==tempAllObs.PredictedFloor,0,1)
return(tempAllObs)
}

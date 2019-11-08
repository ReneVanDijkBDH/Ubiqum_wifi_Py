def CreateFloorModelWAP(VDataExt, ModelList,  ModelType):
    from sklearn.neighbors import KNeighborsClassifier
    
    # filter out data of abnormal users
    VDataExt = VDataExt[(VDataExt.USERID!=6)&(VDataExt.USERID!=14)]
    # filter out (too) hign and no signals
    VDataExt = VDataExt[(VDataExt.WAPSignal!=0)&(VDataExt.WAPSignal<80)]
    
    
    #set modelling parameters
    if ModelType=="KNN":
        MinTrainObs = 10
        #trctrl = trainControl(method="repeatedcv",repeats = 1) 
        #} else if (ModelType=="SVM") {
        #MinTrainObs <- 20
        #trctrl <- trainControl(method = "repeatedcv", number=10, repeats=3)
        #grid <- expand.grid(C = c(0.1, 1, 2.5, 5))
        #} else if (ModelType=="RF") {
        #MinTrainObs <- 20
        #trctrl <- trainControl(method="repeatedcv",repeats = 1) 
        #ModelList<-readRDS('../Data/clean_data/FloorModelWAPRF.rds')
        #}

    # loop through all WAP's and create a model
    WAPNr = 1
    while WAPNr <= 520:
        # define column-name of WAP
        if WAPNr < 10: 
            WAPCol = "WAP00" + str(WAPNr)
        elif WAPNr<100:
            WAPCol = "WAP0" + str(WAPNr)
        else:
            WAPCol = "WAP" + str(WAPNr)

        print(WAPCol)
  
        #select data for specific WAP
        WAPData = VDataExt[VDataExt.WAP==WAPCol][['ObservationID','FLOOR','BUILDINGID', 
                              'LONGITUDE', 'LATITUDE', 'WAPSignal','Quadrant']]
        WAPData_Y = WAPData[['FLOOR']]
        WAPData_X = WAPData[['LONGITUDE', 'LATITUDE', 'WAPSignal','Quadrant']]

        #WAPData$FLOOR     <- factor(WAPData$FLOOR)
    
        #create model when enough records in selected data
        ModelFloor = 0
        if len(WAPData) > MinTrainObs:
            #set.seed(456)
            if ModelType=="KNN":
                # Create KNN classifier
                ModelFloor = KNeighborsClassifier(n_neighbors = 3)
                # Fit the classifier to the data
                ModelFloor.fit(WAPData_X,WAPData_Y)
        #ModelFloor <- train(FLOOR ~ . - ObservationID  , 
        #                    data = WAPData, 
        #                    method = "knn", 
        #                    trControl = trctrl, 
        #                    preProcess = c("center","scale"), 
        #                    tuneGrid = expand.grid(k = c(3,5,7,9)),
        #                    tuneLength = 10)
        # ModelFloor$results$Accuracy[match(ModelFloor$bestTune$k,ModelFloor$results$k)]
        #} else if (ModelType=="SVM") {    
        #  ModelFloor <- train(FLOOR ~ . - ObservationID ,  
        #                      data = WAPData, 
        #                      method = "svmLinear",
        ##                      trControl=trctrl,
        #                      preProcess = c("center", "scale"),
        #                      #tuneGrid = grid,
        #                      tuneLength = 10)
        #} else if (ModelType=="RF") {
        #  ModelFloor <- train(FLOOR ~ . - ObservationID  , 
        #                      data = WAPData, 
        #                      method = "rf", 
        #                      trControl = trctrl, 
        #                      preProcess = c("center","scale"), 
        #                      tuneLength = 10)
        #}
        #store resulting model in ModelList
            ModelList[WAPNr-1] = ModelFloor
          #if(ModelType=="RF"){
          #        saveRDS(ModelList,'../Data/clean_data/FloorModelWAPRF.rds')
          #        }
    
        WAPNr = WAPNr +1
    return(ModelList)

###############
WAPData = trainingVert[trainingVert.WAP=='WAP111'][['ObservationID','FLOOR','BUILDINGID', 'LONGITUDE', 'LATITUDE', 'WAPSignal']]

WAPData_Y = WAPData[['FLOOR']]

WAPData_X = WAPData[['LONGITUDE', 'LATITUDE', 'WAPSignal']]

# Create KNN classifier
knn = KNeighborsClassifier(n_neighbors = 3)
# Fit the classifier to the data
knn.fit(WAPData_X,WAPData_Y)


knn.score(WAPData_X, WAPData_Y)

knn.predict(X_test)[0:5]

#check accuracy of our model on the test data
knn.score(X_test, y_test)


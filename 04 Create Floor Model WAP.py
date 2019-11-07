

from sklearn.neighbors import KNeighborsClassifier



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


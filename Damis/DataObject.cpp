///////////////////////////////////////////////////////////
//  DataObject.cpp
//  Implementation of the Class DataObject
//  Created on:      07-Lie-2013 20:07:29
//  Original author: Povilas
///////////////////////////////////////////////////////////

#include "DataObject.h"


DataObject::DataObject(){

    classLabel = -1;
}

DataObject::~DataObject(){

}


/**
 * Constructor that constructs an object and sets object feature count
 */
DataObject::DataObject(int feature_count){

    classLabel = -1;
    featureCount = feature_count;
}

DataObject::DataObject(std::vector<double> vector){
    features = vector;
    featureCount = features.size();
}

/**
 * Constructor that sets feature count and class label
 */
DataObject::DataObject(int feature_count, int class_label){
    
    featureCount = feature_count;
    classLabel = class_label;
}


int DataObject::getClassLabel(){

	return classLabel;
}

/**
 * Returns feature count
 */
int DataObject::getFeatureCount(){
    //return features.size();
    return featureCount;
}


void DataObject::setClassLabel(int class_Label){
    classLabel = class_Label;
}

bool DataObject::IsIdentical(DataObject obj)
{
    bool ats = false;
    int k = 0;
    int n = obj.getFeatureCount();
    for (int i = 0; i < n; i++)
        if (this->features.at(i) == obj.features.at(i))
            k++;
    if (k == n)
        ats = true;
    
    return ats;    
}

void DataObject::setNumOfFeatures(int n)
{
    features.reserve(n);
}

double DataObject::getFeatureAt(int index)
{
    return features.at(index);
}

void DataObject::updateFeature(int featureIndex, double newValue)
{
    features[featureIndex] = newValue;
}

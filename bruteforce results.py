import concurrent.futures
import time
import numpy as np
import csv


def main():
    timeStart = time.time() 

    #ETA 4 h
    pRange = range(0, 101)
    iRange = range(0, 41)
    dRange = range(0, 51)
    iLengthRange = range(2, 6, 1)
    dLengthRange = range(2, 6, 1)   
    combinations = []
    
    for p in pRange:
        for i in iRange:
            for d in dRange:
                for iL in iLengthRange:
                    for dL in dLengthRange:
                        combinations.append({"p": p / 100, "i": i / 100, "d": d / 100, "iL": iL, "dL": dL})
                        
    print(f"{len(combinations)} combinations, ETC is {(len(combinations) * 0.0007) / 60} min")
    
    with concurrent.futures.ProcessPoolExecutor() as executor:
        results = [executor.submit(simulate, comb["p"], comb["i"], comb["d"], comb["iL"], comb["dL"]) for comb in combinations]
        
        
    results.sort(key=lambda x: x.result()["medianDelta"], reverse=False)
    
    with open("results.csv", "w", newline="") as csvfile:
        fieldnames = ["p", "i", "d", "iL", "dL", "medianDelta", "middle", "max", "min"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        for result in results:
            writer.writerow(result.result())
    
    timeEnd = time.time()
    
    print(f"Time: {round(timeEnd - timeStart,2)} s")             


#FUNCTIONS --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
def simulate(p, i, d, iLength, dLength):
    simulationParameters = {#General parameters
    "simulationLength" : 201 ,
    "startValue" : 20 ,
    "targetValue" : 230 ,
    
    "deviation": 1, "deviationReference": 20, #deviation is a factor


    #Controller parameters
    "activeControllers" : "pid".lower(),
    
    "pFactor" : p ,
    "iFactor" : i , "iLength" : iLength,
    "dFactor" : d , "dLength" : dLength ,
    
    "delay": 1, #how long the controller takes to impact the system
    "latency" : 2 , #how long the controller takes to react to changes in the system
    
    
    #System parameters
    "maxRateOfChange" : 10,  #factor that determines how fast the system is able to be changed with/without a controller
    "belowZero" : False, #if the controller can go below zero
    

    #Additional stresses
    "deviationStart": 30,
    "deviationStyle": "constant", #point or constant
    "deviationValue" : -5,
    "deviationLength": 5,
    
    #Analytics
    "anaLength": 10, #Percentage of the simulation length that will be used to calculate the median                           
    }
                        
    #Creates a "dataVector" in which all simulation data will be stored.
    dataVector = createDataVector(simulationParameters)
    #Calculates the simulation data
    dataVector = calculateSimulation(simulationParameters, dataVector)

    getAnalytics(simulationParameters, dataVector)

    return {"p": p, "i": i, "d": d, "iL": iLength, "dL": dLength, "medianDelta": abs(dataVector["analytics"]["median corrected"] - simulationParameters["targetValue"]), "middle":dataVector["analytics"]["middle corrected"] ,"max": dataVector["analytics"]["max corrected total"], "min": dataVector["analytics"]["min corrected total"]}

#Creates the dataVector dict which holds all calculated values
def createDataVector(sp):   
    varlist = [
        "uncorrected system value",
        "delta_controlled",
        "delta_uncontrolled",
        "corrected system value",
        "controller total",
        "effective controller total",
        "pController",
        "iController",
        "dController",
        "system drift",
        "impact on system",
        "analytics",
    ]

    dataVector = {}

    for var in varlist:
        dataVector[var] = [0 for _ in range(sp["simulationLength"] + sp["latency"] + sp["delay"])]

    #Sets the values for the first Row of the DataVector to 1 for all values after latency.
    #The first Row are multipliers, so for the duration of the latency the calculated values will be set to 0 and all following values will be multiplied by 1.
    #for i in range(sp["simulationLength"] + sp["latency"]):
    dataVector["uncorrected system value"][0] = sp["startValue"]
    dataVector["corrected system value"][0] = sp["startValue"]

    return dataVector

        
#Calculates the simulation        
def calculateSimulation(sp, dataVector):
    #sp is the SimulationParameters Dict
    #dataVector is the dataVector in which all data will be stored

    #Iterates over all timesteps in the simulation.
    for current_Timestep in range(sp["simulationLength"]):

        #dataVector["un/corrected system value"][current_Timestep] is the current value of the system
        current_Value_Controlled = dataVector["corrected system value"][current_Timestep]
        current_Value_Uncontrolled = dataVector["uncorrected system value"][current_Timestep]
            
            
        #Calculates the current Delta and stores it
        dataVector["delta_controlled"][current_Timestep] = sp["targetValue"] - current_Value_Controlled
        dataVector["delta_uncontrolled"][current_Timestep] = sp["targetValue"] - current_Value_Uncontrolled
        

        #Calculates the systems deviation (natural drift towards the baseline value)
        deviation_controlled = calculateDeviation(sp, current_Value_Controlled)
        deviation_uncontrolled = calculateDeviation(sp, current_Value_Uncontrolled)
        
                
        #Adds the deviation to the next simulation step
        dataVector["corrected system value"][current_Timestep + 1] += dataVector["corrected system value"][current_Timestep] + deviation_uncontrolled
        dataVector["uncorrected system value"][current_Timestep + 1] += dataVector["uncorrected system value"][current_Timestep] + deviation_uncontrolled        
        
        
        #Calculates the controllers and stores the values in the dataVector
        pValue, iValue, dValue = calculateControllers(sp, dataVector["delta_controlled"], current_Timestep - sp["latency"])
        
        dataVector["pController"][current_Timestep] = pValue
        dataVector["iController"][current_Timestep] = iValue
        dataVector["dController"][current_Timestep] = dValue
        
        dataVector["controller total"][current_Timestep] = pValue + iValue + dValue
        
        
        #Since the maximum rate of change is limited by factors like the power of a heating element, the controller can't change the system faster than the maximum rate of change
        if sp["belowZero"] == True:
            dataVector["effective controller total"][current_Timestep] = min(dataVector["controller total"][current_Timestep], sp["maxRateOfChange"])
        elif sp["belowZero"] == False:
            dataVector["effective controller total"][current_Timestep] = max(min(dataVector["controller total"][current_Timestep], sp["maxRateOfChange"]),0)
        


        #Calculates the movement of the system without a controller
        #For the first values (for timesteps in "latency") and if the value is below the target, the system will move towards the target value at full speed
        #Waits for "latency" and "delay" because the uncontrolled system has no delay. It is assumed that since switching is between boolean values the system will react instantly.
        if current_Timestep not in range(sp["latency"]):
            
            if dataVector["uncorrected system value"][current_Timestep - sp["latency"]] < sp["targetValue"]:
                dataVector["uncorrected system value"][current_Timestep + sp["delay"]] += sp["maxRateOfChange"]
                
            dataVector["corrected system value"][current_Timestep + sp["delay"]] += dataVector["effective controller total"][current_Timestep]
                        
        
        
        if sp["deviationStyle"] == "point" and current_Timestep == sp["deviationStart"]:
            dataVector["corrected system value"][current_Timestep + 1] += sp["deviationValue"]
            dataVector["uncorrected system value"][current_Timestep + 1] += sp["deviationValue"]
        elif sp["deviationStyle"] == "constant" and current_Timestep in range(sp["deviationStart"],sp["deviationStart"]+sp["deviationLength"]):
            dataVector["corrected system value"][current_Timestep + 1] += sp["deviationValue"]
            dataVector["uncorrected system value"][current_Timestep + 1] += sp["deviationValue"]
        
        
        dataVector["system drift"][current_Timestep] = deviation_controlled


        
    for timestep in range(sp["simulationLength"]):
        dataVector["impact on system"][timestep + sp["delay"]] += dataVector["effective controller total"][timestep]
    
    
    
    #Shortens the dataVector to the length of the simulation. This is necessary because the dataVector is longer than the simulation length to account for latency and delay.
    truncatedVector = {}
    for vector in dataVector:
        truncatedVector[vector] = dataVector[vector][:sp["simulationLength"]]
    return truncatedVector


#Calculates the drift towards baseline for a given value
def calculateDeviation(sp, current_Value):
    #Calculates where the current value lies between the Base and target value. Multiplies that with the deviation factor.
    value_Base = sp["deviationReference"]
    value_Target = sp["targetValue"]
    factor = sp["deviation"]
    deviation = -1 * factor * (current_Value - value_Base) / (value_Target - value_Base)
    return deviation


#Calculates the controller values
def calculateControllers(sp, dataVector, current_Timestep):

    current_Value = dataVector[current_Timestep]

    #calculates Value of the pController at the current_Timestep
    if "p" in sp["activeControllers"]:
        pValue = pController(current_Value, sp["pFactor"])
    else:
        pValue = 0
        
        
    #calculates Value of the iController at the current_Timestep
    #sets iController Value to 0 if impossible
    if "i" in sp["activeControllers"]:
        try:
            iFact = sp["iFactor"]
            iValue = iController(dataVector[current_Timestep - sp["iLength"]:current_Timestep], iFact)
        except:
            print(f"iController failed at {current_Timestep}")
            iValue = 0
    else:
        iValue = 0


    #calculates Value of the dController at the current_Timestep
    #sets dController Value to 0 if impossible
    if "d" in sp["activeControllers"]:
        dCalc = dataVector[current_Timestep - sp["dLength"] + 1]
    
        if dCalc == 0:
            dValue = 0
        else:
            dValue = dController(current_Value, dCalc, sp["dLength"], sp["dFactor"])
    else:
        dValue = 0
  
    #print(f"pValue: {pValue}, iValue: {iValue}, dValue: {dValue}")
    return pValue, iValue, dValue


#P component
def pController(current_Value, pFactor):
    return pFactor * current_Value

#I component
def iController(integrationArray, iFactor):
    return iFactor * np.trapz(integrationArray)

#D component
def dController(current_Value, past_Value, dLength, dFactor):
    return dFactor * (current_Value - past_Value) / dLength


#Gets analytics values
def getAnalytics(sp, dataVector):
    #Calculates analytics to display in the graph and for automated analysis
    timeWindow = round(sp["simulationLength"] / 100 * sp["anaLength"])
    dataVector["analytics"] = {}
    dataVector["analytics"]["median corrected"] = np.median(dataVector["corrected system value"][-timeWindow:])
    dataVector["analytics"]["median uncorrected"] = np.median(dataVector["uncorrected system value"][-timeWindow:])
    dataVector["analytics"]["max corrected end"] = max(dataVector["corrected system value"][-timeWindow:])
    dataVector["analytics"]["min corrected end"] = min(dataVector["corrected system value"][-timeWindow:])
    dataVector["analytics"]["max uncorrected end"] = max(dataVector["uncorrected system value"][-timeWindow:])
    dataVector["analytics"]["min uncorrected end"] = min(dataVector["uncorrected system value"][-timeWindow:])
    dataVector["analytics"]["middle corrected"] = dataVector["analytics"]["max corrected end"] - dataVector["analytics"]["min corrected end"]
    dataVector["analytics"]["middle uncorrected"] = dataVector["analytics"]["max uncorrected end"] - dataVector["analytics"]["min uncorrected end"]
    dataVector["analytics"]["max corrected total"] = max(dataVector["corrected system value"])
    dataVector["analytics"]["min corrected total"] = min(dataVector["corrected system value"])
    dataVector["analytics"]["max uncorrected total"] = max(dataVector["uncorrected system value"])
    dataVector["analytics"]["min uncorrected total"] = min(dataVector["uncorrected system value"])
        
        

if __name__ == "__main__":
    main()
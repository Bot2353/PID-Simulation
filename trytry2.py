import numpy as np
import matplotlib.pyplot as plt

simulationParameters = {"pFactor" : 0.3 , "pIndividualOffset" : 2,
                        "iFactor" : 0.03 , "iLength" : 2, "iIndividualOffset" : 0,
                        "dFactor" : 0.3 , "dLength" : 2 ,"dIndividualOffset" : 0,
                        "latency" : 1 ,
                        "useIndividualOffsets": False,
                        "simulationLength" : 201 ,
                        "startValue" : 50 ,
                        "targetValue" : 100 ,
                        "deviation": 1, "deviationReference": 0,
                        "medianLength": 20,
                        "printDataRows": True
                        }
activeControllers = "pid"


def main():
    #Creates a "dataVector" in which all simulation data will be stored.
    dataVector = createDataVector(simulationParameters)
    
    #Calculates the simulation data
    dataVector = calculateSimulation(simulationParameters, dataVector)
    
    "uncorrected system value",
    "NO delta",
    "NO corrected system value",
    "NO controller total",
    "NO pController",
    "NO iController",
    "NO dController",
    "NO system drift",
    "NO impact on system",
    "WO delta",
    "WO corrected system value",
    "WO controller total",
    "WO pController",
    "WO iController",
    "WO dController",
    "WO system drift",
    "WO impact on system"
        
    plotGraphs(simulationParameters ,dataVector)
    
    printData(simulationParameters["printDataRows"], dataVector)


def printData(bool, dataVector):
    if bool:
        for i in dataVector:
            print(f"{i}            - {dataVector[i]}")



def plotGraphs(sp, dataVector):
    lineWidth = 0.75
    fig = plt.figure(figsize= (16,10), dpi= 120, layout="tight", linewidth= lineWidth,facecolor=(0.8,0.8,0.8),)
    fig.suptitle("p/i/d-controller simulation results", fontsize=24)
    
    #If "useIndividualOffsets" is not selected these vector IDs will be used to display the graphs
    graphSelector = {
        "delta": "NO delta",
        "corrected":"NO corrected system value",
        "total":"NO controller total",
        "total-latency":"NO impact on system", 
        "p":"NO pController", 
        "i":"NO iController", 
        "d":"NO dController"
        }
    #If "useIndividualOffsets" is selected these vector IDs will be used to display the graphs instead
    if sp["useIndividualOffsets"]:        
        graphSelector["delta"] = "WO delta"
        graphSelector["corrected"] = "WO corrected system value"
        graphSelector["total"] =  "WO controller total"
        graphSelector["total-latency"] = "WO impact on system"
        graphSelector["p"] = "WO pController"
        graphSelector["i"] = "WO iController"
        graphSelector["d"] = "WO dController"
               
    #Plot is 5 deep and 8 wide
    plotGrid = (5,8)
    length = range(sp["simulationLength"])
    medianLen = medianLength(sp["simulationLength"],sp["medianLength"])
    
    #System behaviour
    ax1 = plt.subplot2grid(plotGrid,(0,0),colspan= 4, rowspan = 3)
    #DELTA
    ax2 = plt.subplot2grid(plotGrid,(3,0),colspan= 4, rowspan = 2)    
    
    #PID Value graph
    ax3 = plt.subplot2grid(plotGrid,(0,4),colspan=4, rowspan = 2)
    ax4 = plt.subplot2grid(plotGrid,(2,4),colspan=2)
    ax5 = plt.subplot2grid(plotGrid,(3,4),colspan=2)
    ax6 = plt.subplot2grid(plotGrid,(4,4),colspan=2)
    
    #Deviation graph
    ax7 = plt.subplot2grid(plotGrid,(2,6),colspan=2)

    ax1.set_title("System values over time")
    ax1.plot(length, dataVector[graphSelector["corrected"]], label= "controlled system value", color="green")   
    ax1.plot(length, dataVector["uncorrected system value"], label= "uncontrolled system value", color="orange")
    
    ax1.axhline(y= sp["targetValue"], color='green', linestyle=('dashed'), linewidth= lineWidth, label="controller target")
    ax1.axhline(y= sp["deviationReference"], color='red', linestyle=('dashed'), linewidth= lineWidth, label = "system baseline")  
    ax1.axhline(y= np.median(dataVector[graphSelector["corrected"]][medianLen:]), color="purple", linestyle=('dashed'), linewidth= lineWidth, label=f"median of the last {-medianLen}\ncontrolled system values")
    
    
    ax2.set_title("Delta between controlled system value and target value over time")
    ax2.axhline(y= 0, color="green", linestyle=('dashed'), linewidth= lineWidth, label="0 - target")
    ax2.axhline(y= np.median(dataVector[graphSelector["delta"]][medianLen:]), color="purple", linestyle=('dashed'), linewidth= lineWidth, label=f"median of the last {-medianLen}\ndelta values")
    ax2.plot(length, dataVector["NO delta"])
    
    
    ax3.set_title("Total controller output and effective impact over time")
    ax3.plot(length, dataVector[graphSelector["total"]], label = f"Total controller impulse \n({activeControllers.upper()} components)")
    ax3.plot(length, dataVector[graphSelector["total-latency"]], label = "Controller value \nminus system deviation")
    
    
    ax4.set_title("P-Controller output over time")
    ax4.plot(length, dataVector[graphSelector["p"]])
    
    
    ax5.set_title("I-Controller output over time")
    ax5.plot(length, dataVector[graphSelector["i"]])
    
    
    ax6.set_title("D-Controller output over time")
    ax6.plot(length, dataVector[graphSelector["d"]])
        
        
    ax7.set_title("System drift")
    ax7.axhline(y= 0, color='red', linestyle=('dashed'), linewidth= lineWidth)
    ax7.plot(length, dataVector["NO system drift"])
    
    
    for i in [ax1, ax2, ax3, ax4, ax5, ax6, ax7]:
        i.set_xlabel("Simulation timesteps")
        i.set_facecolor("white")
    
    
    ax1.legend()
    ax2.legend()
    ax3.legend()
    
    plt.show()



def medianLength(simLength, medianLength):
    return - round(simLength / 100 * medianLength)



def calculateSimulation(sp, dataVector):
    #sp is the SimulationParameters Dict
    #dataVector is the dataVector in which all data will be stored
    
    #Iterates over enough timesteps to do the simulation.
    #Skipping the last "latency" numbers of the list. This is because the last values won't be part of the graph anyways.
    #Everything marked with a "2" is related to the "useIndividualOffset" feature. It basically calculates everything a second time in parallel.
    for current_Timestep in range(sp["simulationLength"]):
            
        #calculation_Timestep = current_Timestep + sp["latency"]
        
        #dataVector["NO corrected system value"][current_Timestep] is the current value of the system
        current_Value = dataVector["NO corrected system value"][current_Timestep]
        #dataVector["NO corrected system value"][calculation_Timestep] is the value that is being calculated because of latency
        
        #Calculates the current Delta and enters it
        dataVector["NO delta"][current_Timestep] = sp["targetValue"] - current_Value
        dataVector["WO delta"][current_Timestep] = sp["targetValue"] - dataVector["WO corrected system value"][current_Timestep]
        
        #Calculates the systems deviation
        deviation = calculateDeviation(sp, current_Value)
        deviation2 = calculateDeviation(sp, dataVector["WO corrected system value"][current_Timestep])
                
        #Calculates the movement of the system without a controller
        dataVector["uncorrected system value"][current_Timestep + 1] = dataVector["uncorrected system value"][current_Timestep] + calculateDeviation(sp, dataVector["uncorrected system value"][current_Timestep])
        
        #The controller can't act for the first timesteps because of latency. Only the deviation has an impact
        if dataVector["NO corrected system value"][current_Timestep] == sp["startValue"] or current_Timestep in range(sp["latency"]):
            dataVector["NO corrected system value"][current_Timestep + 1] = dataVector["NO corrected system value"][current_Timestep] + deviation
            dataVector["WO corrected system value"][current_Timestep + 1] = dataVector["WO corrected system value"][current_Timestep] + deviation2
        else:
        #Afterwards the controllers effect is added. But it is offset by latency
            dataVector["NO corrected system value"][current_Timestep + 1] = dataVector["NO corrected system value"][current_Timestep] + deviation + dataVector["NO controller total"][current_Timestep - sp["latency"]]    
            dataVector["WO corrected system value"][current_Timestep + 1] = dataVector["WO corrected system value"][current_Timestep] + deviation2 + dataVector["WO controller total"][current_Timestep - sp["latency"]]    
        #Calculates the values of the different controllers
        pValue, iValue, dValue = calculateControllers(sp, dataVector["NO delta"], current_Timestep)
        pValue2, iValue2, dValue2 = calculateControllers(sp, dataVector["WO delta"], current_Timestep)
        
        
        #Enters the calculated controller Values into the dataVector
        #Add Values to Vector 9 respecting the individual offsets for each controller
        totalControllerValue = 0
        for letter in activeControllers.lower():
            if letter == "p":
                totalControllerValue += pValue
                dataVector["WO controller total"][current_Timestep + sp["pIndividualOffset"]] += pValue2
            elif letter == "i":
                totalControllerValue += iValue
                dataVector["WO controller total"][current_Timestep + sp["iIndividualOffset"]] += iValue2
            elif letter == "d":
                totalControllerValue += dValue
                dataVector["WO controller total"][current_Timestep + sp["dIndividualOffset"]] += dValue2
            
            
        dataVector["NO controller total"][current_Timestep] = totalControllerValue
        dataVector["NO pController"][current_Timestep] = pValue
        dataVector["NO iController"][current_Timestep] = iValue
        dataVector["NO dController"][current_Timestep] = dValue
        dataVector["NO system drift"][current_Timestep] = deviation


        dataVector["WO pController"][current_Timestep] = pValue2
        dataVector["WO iController"][current_Timestep] = iValue2
        dataVector["WO dController"][current_Timestep] = dValue2
        dataVector["WO system drift"][current_Timestep] = deviation2
         
        #Adds the (should be negative) total controller value to the previous value on the calculation_Timestep
        #dataVector["NO corrected system value"][calculation_Timestep] = totalControllerValue
    
    #Calculates the effective influence of the controllers on the system by adding the system deviation to it.
    #Takes the latency of the controllers into account
    for timesteps in range(sp["latency"],sp["simulationLength"]+sp["latency"]):
        #Latency - 1 here because python lists start at iterator 0
        dataVector["NO impact on system"][timesteps] = dataVector["NO system drift"][timesteps] + dataVector["NO controller total"][timesteps - sp["latency"]- 1]
        dataVector["WO impact on system"][timesteps] = dataVector["NO system drift"][timesteps] + dataVector["WO controller total"][timesteps - sp["latency"]- 1]
        
    truncatedVector = {}
    for vector in dataVector:
        truncatedVector[vector] = dataVector[vector][:sp["simulationLength"]]
    return truncatedVector



def createDataVector(sp):
    #sp is the SimulationParameters Dict
    #NO = no offset
    #WO = with offset

    varlist = [
        "uncorrected system value",
        "NO delta",
        "NO corrected system value",
        "NO controller total",
        "NO pController",
        "NO iController",
        "NO dController",
        "NO system drift",
        "NO impact on system",
        "WO delta",
        "WO corrected system value",
        "WO controller total",
        "WO pController",
        "WO iController",
        "WO dController",
        "WO system drift",
        "WO impact on system"
    ]
    
    dataVector = {}
    
    for var in varlist:
        dataVector[var] = [0 for _ in range(sp["simulationLength"] + sp["latency"])]
    
    #Sets the values for the first Row of the DataVector to 1 for all values after latency.
    #The first Row are multipliers, so for the duration of the latency the calculated values will be set to 0 and all following values will be multiplied by 1.
    #for i in range(sp["simulationLength"] + sp["latency"]):
    dataVector["uncorrected system value"][0] = sp["startValue"]
    dataVector["NO corrected system value"][0] = sp["startValue"]
    dataVector["WO corrected system value"][0]= sp["startValue"]
    
    return dataVector 



def calculateDeviation(sp, current_Value):
    #Calculates where the current value lies between the Base and target value. Multiplies that with the deviation factor.
    value_Base = sp["deviationReference"]
    value_Target = sp["targetValue"]
    factor = sp["deviation"]
    deviation = -1 * factor * (current_Value - value_Base) / (value_Target - value_Base)
    return deviation



def calculateControllers(sp, dataVector, current_Timestep):

    current_Value = dataVector[current_Timestep]
    
    #calculates Value of the pController at the current_Timestep
    pFact = sp["pFactor"]
    pValue = pController(current_Value, pFact)
    
    #calculates Value of the iController at the current_Timestep
    #sets iController Value to 0 if impossible
    try:
        iFact = sp["iFactor"]
        iValue = iController(dataVector[current_Timestep - sp["iLength"]:current_Timestep], iFact)
    except:
        print(f"iController failed at {current_Timestep}")
        iValue = 0
    
    #calculates Value of the dController at the current_Timestep
    #sets dController Value to 0 if impossible
    
    
    dCalc = dataVector[current_Timestep - sp["dLength"] + 1]
    if dCalc == 0:
        dValue = 0
    else:
        dLen = sp["dLength"]
        dFact = sp["dFactor"]
        dValue = dController(current_Value, dCalc, dLen, dFact)
    
        
    return pValue, iValue, dValue



def pController(current_Value, pFactor):
    return pFactor * current_Value

def iController(integrationArray, iFactor):
    return iFactor * np.trapz(integrationArray)

def dController(current_Value, past_Value, dLength, dFactor):
    return -1 * dFactor * (current_Value - past_Value) / dLength


if __name__ == "__main__":
    main()
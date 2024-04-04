import numpy as np
import matplotlib.pyplot as plt

simulationParameters = {"pFactor" : 0.2 , "pIndividualOffset" : 1,
                        "iFactor" : 0.03 , "iLength" : 2, "iIndividualOffset" : 3,
                        "dFactor" : 0.3 , "dLength" : 2 ,"dIndividualOffset" : 1,
                        "latency" : 3 ,
                        "useIndividualOffsets": False,
                        "simulationLength" : 101 ,
                        "startValue" : 10 ,
                        "targetValue" : 100 ,
                        "deviation": 1, "deviationReference": 0,
                        "deviationLocation" : None , "deviationLowerLimit" : 1 , "deviationUpperLimit" : 2 ,
                        "vectorDimensions" : 17,
                        "medianLength": 20
                        }
activeControllers = "pid"


"""
The DataVector is structured as follows:
Row 0 - DELTA
Row 1 - Uncorrected Deviation of the controller
Row 2 - Corrected Deviaiton of the controller
Row 3 - Total Controller Impulse
Row 4 - pController part of the Impulse
Row 5 - iController part of the Impulse
Row 6 - dController part of the Impulse
Row 7 - systemDeviation
Row 8 - Total Controller Impulse minus systemDeviation at the time of impact
Row 9 - Total Controller Impulse respecting individual latencies
Row 10 - Row2 equivalent using Row9 data
Row 11 - Total Controller Impulse respecting individual latencies minus systemDeviation at the time of impact
"""


def main():
    #Creates a "dataVector" in which all simulation data will be stored.
    dataVector = createDataVector(simulationParameters)
    
    #Calculates the simulation data
    dataVector = calculateSimulation(simulationParameters, dataVector)
    
    """
    print(f"Row 0 - DELTA                   - {dataVector[0]}")
    print(f"Row 1 - Uncorrected Deviation   - {dataVector[1]}")
    print(f"Row 2 - Corrected Deviaiton     - {dataVector[2]}")
    print(f"Row 3 - Total Controller Impulse- {dataVector[3]}")
    print(f"Row 4 - pController             - {dataVector[4]}")
    print(f"Row 5 - iController             - {dataVector[5]}")
    print(f"Row 6 - dController             - {dataVector[6]}")
    print(f"Row 7 - systemDeviation         - {dataVector[7]}")
    """

    plotGraphs(simulationParameters ,dataVector)
    
    return 100


def plotGraphs(sp, dataVector):
    lineWidth = 0.75
    fig = plt.figure(figsize= (16,10), dpi= 120, layout="tight", linewidth= lineWidth,facecolor=(0.8,0.8,0.8),)
    fig.suptitle("p/i/d-controller simulation results", fontsize=24)
    
    #If "useIndividualOffsets" is not selected these vector IDs will be used to display the graphs
    graphSelector = {
        "delta":0,
        "corrected":2,
        "total":3,
        "total-latency":8, 
        "p":4, 
        "i":5, 
        "d":6
        }
    #If "useIndividualOffsets" is selected these vector IDs will be used to display the graphs instead
    if sp["useIndividualOffsets"]:        
        graphSelector["delta"] = 12
        graphSelector["corrected"] = 10
        graphSelector["total"] = 9
        graphSelector["total-latency"] = 11
        graphSelector["p"] = 13
        graphSelector["i"] = 14
        graphSelector["d"] = 15
               
    #Plot is 5 deep and 8 wide
    plotGrid = (5,8)
    length = range(len(dataVector[0]))
    
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
    ax1.plot(length, dataVector[ graphSelector["corrected"]], label= "controlled system value", color="green")   
    ax1.plot(length, dataVector[1], label= "uncontrolled system value", color="orange")
    
    ax1.axhline(y= sp["targetValue"], color='green', linestyle=('dashed'), linewidth= lineWidth, label="Controller target")
    ax1.axhline(y= sp["deviationReference"], color='red', linestyle=('dashed'), linewidth= lineWidth, label = "System baseline")
    ax1.axhline(y= np.median(dataVector[graphSelector["corrected"]][:round(len(dataVector[ graphSelector["corrected"]]/100 * sp["medianLength"])):]), color="purple", linestyle=('dashed'), linewidth= lineWidth, label=f'Median of the last {medianLength(sp["medianLength"], dataVector[graphSelector["corrected"]])} values')
    
    
    ax2.set_title("Delta between controlled system value and target value over time")
    ax2.axhline(y= 0, color="green", linestyle=('dashed'), linewidth= lineWidth, label="0 - target")
    ax2.axhline(y= np.median(dataVector[graphSelector["delta"]][:round(len(dataVector[graphSelector["delta"]]/100 * sp["medianLength"])):]), color="purple", linestyle=('dashed'), linewidth= lineWidth, label=f'Median of the last {medianLength(sp["medianLength"], dataVector[graphSelector["delta"]])} values')
    ax2.plot(length, dataVector[0])
    
    
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
    ax7.plot(length, dataVector[7])
    
    
    for i in [ax1, ax2, ax3, ax4, ax5, ax6, ax7]:
        i.set_xlabel("Simulation timesteps")
        i.set_facecolor("white")
    
    
    ax1.legend()
    ax2.legend()
    ax3.legend()
    
    plt.show()



def medianLength(medianLength, array):
    return round(len(array) /100 * medianLength)



def calculateSimulation(sp, dataVector):
    #sp is the SimulationParameters Dict
    #dataVector is the dataVector in which all data will be stored
    
    #Iterates over enough timesteps to do the simulation.
    #Skipping the last "latency" numbers of the list. This is because the last values won't be part of the graph anyways.
    #Everything marked with a "2" is related to the "useIndividualOffset" feature. It basically calculates everything a second time in parallel.
    for current_Timestep in range(sp["simulationLength"]):
            
        #calculation_Timestep = current_Timestep + sp["latency"]
        
        #dataVector[2][current_Timestep] is the current value of the system
        current_Value = dataVector[2][current_Timestep]
        #dataVector[2][calculation_Timestep] is the value that is being calculated because of latency
        
        #Calculates the current Delta and enters it
        dataVector[0][current_Timestep] = sp["targetValue"] - current_Value
        dataVector[12][current_Timestep] = sp["targetValue"] - dataVector[10][current_Timestep]
        
        #Calculates the systems deviation
        deviation = calculateDeviation(sp, current_Value)
        deviation2 = calculateDeviation(sp, dataVector[10][current_Timestep])
                
        #Calculates the movement of the system without a controller
        dataVector[1][current_Timestep + 1] = dataVector[1][current_Timestep] + calculateDeviation(sp, dataVector[1][current_Timestep])
        
        #The controller can't act for the first timesteps because of latency. Only the deviation has an impact
        if dataVector[2][current_Timestep] == sp["startValue"] or current_Timestep in range(sp["latency"]):
            dataVector[2][current_Timestep + 1] = dataVector[2][current_Timestep] + deviation
            dataVector[10][current_Timestep + 1] = dataVector[10][current_Timestep] + deviation2
        else:
        #Afterwards the controllers effect is added. But it is offset by latency
            dataVector[2][current_Timestep + 1] = dataVector[2][current_Timestep] + deviation + dataVector[3][current_Timestep - sp["latency"]]    
            dataVector[10][current_Timestep + 1] = dataVector[10][current_Timestep] + deviation2 + dataVector[9][current_Timestep - sp["latency"]]    
        #Calculates the values of the different controllers
        pValue, iValue, dValue = calculateControllers(sp, dataVector[0], current_Timestep)
        pValue2, iValue2, dValue2 = calculateControllers(sp, dataVector[12], current_Timestep)
        
        
        #Enters the calculated controller Values into the dataVector
        #Add Values to Vector 9 respecting the individual offsets for each controller
        totalControllerValue = 0
        for letter in activeControllers.lower():
            if letter == "p":
                totalControllerValue += pValue
                dataVector[9][current_Timestep + sp["pIndividualOffset"]] += pValue2
            elif letter == "i":
                totalControllerValue += iValue
                dataVector[9][current_Timestep + sp["iIndividualOffset"]] += iValue2
            elif letter == "d":
                totalControllerValue += dValue
                dataVector[9][current_Timestep + sp["dIndividualOffset"]] += dValue2
            
            
        dataVector[3][current_Timestep] = totalControllerValue
        dataVector[4][current_Timestep] = pValue
        dataVector[5][current_Timestep] = iValue
        dataVector[6][current_Timestep] = dValue
        dataVector[7][current_Timestep] = deviation


        dataVector[13][current_Timestep] = pValue2
        dataVector[14][current_Timestep] = iValue2
        dataVector[15][current_Timestep] = dValue2
        dataVector[16][current_Timestep] = deviation2
         
        #Adds the (should be negative) total controller value to the previous value on the calculation_Timestep
        #dataVector[2][calculation_Timestep] = totalControllerValue
    
    #Calculates the effective influence of the controllers on the system by adding the system deviation to it.
    #Takes the latency of the controllers into account
    for timesteps in range(sp["latency"],sp["simulationLength"]+sp["latency"]):
        #Latency - 1 here because python lists start at iterator 0
        dataVector[8][timesteps] = dataVector[7][timesteps] + dataVector[3][timesteps - sp["latency"]- 1]
        dataVector[11][timesteps] = dataVector[7][timesteps] + dataVector[9][timesteps - sp["latency"]- 1]
    return dataVector[0:sp["vectorDimensions"],0:sp["simulationLength"]]



def createDataVector(sp):
    #sp is the SimulationParameters Dict
    
    #Creates a vector containing 7 Rows
    dataVector = np.zeros((sp["vectorDimensions"], sp["simulationLength"] + sp["latency"]))
    
    #Sets the values for the first Row of the DataVector to 1 for all values after latency.
    #The first Row are multipliers, so for the duration of the latency the calculated values will be set to 0 and all following values will be multiplied by 1.
    #for i in range(sp["simulationLength"] + sp["latency"]):
    dataVector[1][0] = sp["startValue"]
    dataVector[2][0] = sp["startValue"]
    dataVector[10][0]= sp["startValue"]
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
    try:
        dCalc = dataVector[current_Timestep - sp["dLength"]]
        dLen = sp["dLength"]
        dFact = sp["dFactor"]
        dValue = dController(current_Value, dCalc, dLen, dFact)
    except:
        print(f"dController failed at {current_Timestep}")
        dValue = 0
        
    return pValue, iValue, dValue



def pController(current_Value, pFactor):
    return pFactor * current_Value

def iController(integrationArray, iFactor):
    return iFactor * np.trapz(integrationArray)

def dController(current_Value, past_Value, dLength, dFactor):
    return -1 * dFactor * (current_Value - past_Value) / dLength


if __name__ == "__main__":
    main()
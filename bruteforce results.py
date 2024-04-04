import numpy as np
import matplotlib.pyplot as plt
import time
import csv


def main(abc):
    simulationParameters = {"activeControllers" : "pid".lower(),
                        #"pFactor" : 0.3 ,
                        #"iFactor" : 0.1 , "iLength" : 2,
                        #"dFactor" : 0.1 , "dLength" : 2 ,
                        #"delay": 1,
                        #"latency" : 2 ,
                        "simulationLength" : 201 ,
                        "startValue" : 50 ,
                        "targetValue" : 100 ,
                        "deviation": 1, "deviationReference": 20,
                        "medianLength": 30,
                        "printDataRows": False
                        }
    simulationParameters.update(abc)
    
    #Creates a "dataVector" in which all simulation data will be stored.
    dataVector = createDataVector(simulationParameters)
    #Calculates the simulation data
    dataVector = calculateSimulation(simulationParameters, dataVector)
    """
    DATA VECTORS
    "uncorrected system value",
    "NO delta",
    "NO corrected system value",
    "NO controller total",
    "NO pController",
    "NO iController",
    "NO dController",
    "NO system drift",
    "NO impact on system",
    """

    #printData(simulationParameters["printDataRows"], dataVector)

    #printOverview(simulationParameters, dataVector)
    
    #for i in range(len(dataVector["NO impact on system"])):
     #   print(f'Impact on System: {dataVector["NO impact on system"][i]:20}, System deviation: {dataVector["NO system drift"][i]}')
     
    
    #plotGraphs(simulationParameters ,dataVector)

    return np.median(dataVector["NO corrected system value"][medianLength(simulationParameters["simulationLength"],simulationParameters["medianLength"]):])


#FUNCTIONS --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
def printOverview(sp, dataVector):
    median = np.median(dataVector["NO corrected system value"][medianLength(sp["simulationLength"],sp["medianLength"]):])

    print("\n")
    print(f'Das durch den {sp["activeControllers"].upper()}-Regler geregelte System hatte auf den letzten {-medianLength(sp["simulationLength"],sp["medianLength"])} Zeitschritten einen Median von {median}.')
    print(f'Damit liegt er nach {sp["simulationLength"] - 1} Zeitschritten ca. {round(sp["targetValue"] - median, 3)} abseits des Zielwerts von {sp["targetValue"]}.')
    return 0



def printData(bool, dataVector):
    if bool:
        for i in dataVector:
            print(f"{i}            - {dataVector[i]}")



def plotGraphs(sp, dataVector):
    lineWidth = 0.75
    fig = plt.figure(figsize= (12,8), dpi= 120, layout="tight", linewidth= lineWidth,facecolor=(0.8,0.8,0.8),)
    #fig = plt.figure(figsize= (16,10), dpi= 120, layout="tight", linewidth= lineWidth,facecolor=(0.8,0.8,0.8),)
    fig.suptitle(f"{sp['activeControllers'].upper()}-controller simulation results", fontsize=24)

    #If "useIndividualOffsets" is not selected these vector IDs will be used to display the graphs

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
    ax1.plot(length, dataVector["NO corrected system value"], label= "controlled system value", color="green")
    ax1.plot(length, dataVector["uncorrected system value"], label= "uncontrolled system value", color="orange")

    ax1.axhline(y= sp["targetValue"], color='green', linestyle=('dashed'), linewidth= lineWidth, label="controller target")
    ax1.axhline(y= sp["deviationReference"], color='red', linestyle=('dashed'), linewidth= lineWidth, label = "system baseline")
    ax1.axhline(y= np.median(dataVector["NO corrected system value"][medianLen:]), color="purple", linestyle=('dashed'), linewidth= lineWidth, label=f"median of the last {-medianLen}\ncontrolled system values")


    ax2.set_title("Delta between controlled system value and target value over time")
    ax2.axhline(y= 0, color="green", linestyle=('dashed'), linewidth= lineWidth, label="0 - target")
    ax2.axhline(y= np.median(dataVector["NO delta"][medianLen:]), color="purple", linestyle=('dashed'), linewidth= lineWidth, label=f"median of the last {-medianLen}\ndelta values")
    ax2.step(length, dataVector["NO delta"], where="post")


    ax3.set_title("Total controller output and effective impact over time")
    ax3.step(length, dataVector["NO controller total"],where="post", label = f"Total controller impulse \n({sp['activeControllers'].upper()} components)")
    ax3.step(length, dataVector["NO impact on system"],where="post", label = "Controller value \nminus system deviation")


    ax4.set_title("P-Controller output over time")
    ax4.step(length, dataVector["NO pController"], where="post")


    ax5.set_title("I-Controller output over time")
    ax5.step(length, dataVector["NO iController"], where="post")


    ax6.set_title("D-Controller output over time")
    ax6.step(length, dataVector["NO dController"], where="post")


    ax7.set_title("System drift")
    ax7.axhline(y= 0, color='red', linestyle=('dashed'), linewidth= lineWidth)
    ax7.plot(length, dataVector["NO system drift"])


    for i in [ax1, ax2, ax3, ax4, ax5, ax6, ax7]:
        i.set_xlabel("Simulation timesteps")
        i.set_facecolor("white")
        #i.set_xlim(-3, sp["simulationLength"])


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

        #Calculates the systems deviation
        deviation = calculateDeviation(sp, current_Value)

        #Calculates the movement of the system without a controller
        dataVector["uncorrected system value"][current_Timestep + 1] = dataVector["uncorrected system value"][current_Timestep] + calculateDeviation(sp, dataVector["uncorrected system value"][current_Timestep])

        #The controller can't act for the first timesteps because of latency. Only the deviation has an impact
        if dataVector["NO corrected system value"][current_Timestep] == sp["startValue"] or current_Timestep in range(sp["latency"]):
            dataVector["NO corrected system value"][current_Timestep + 1] = dataVector["NO corrected system value"][current_Timestep] + deviation
        else:
        #Afterwards the controllers effect is added. But it is offset by latency
            dataVector["NO corrected system value"][current_Timestep + 1] = dataVector["NO corrected system value"][current_Timestep] + deviation + dataVector["NO controller total"][current_Timestep - sp["latency"]]
        #Calculates the values of the different controllers
        pValue, iValue, dValue = calculateControllers(sp, dataVector["NO delta"], current_Timestep - sp["delay"])


        #Enters the calculated controller Values into the dataVector
        #Add Values to Vector 9 respecting the individual offsets for each controller
        
        dataVector["NO controller total"][current_Timestep] = pValue + iValue + dValue
        dataVector["NO pController"][current_Timestep] = pValue
        dataVector["NO iController"][current_Timestep] = iValue
        dataVector["NO dController"][current_Timestep] = dValue
        dataVector["NO system drift"][current_Timestep] = deviation

        #Adds the (should be negative) total controller value to the previous value on the calculation_Timestep
        #dataVector["NO corrected system value"][calculation_Timestep] = totalControllerValue

    #Calculates the effective influence of the controllers on the system by adding the system deviation to it.
    #Takes the latency of the controllers into account
    for timestep in range(sp["simulationLength"] - sp["latency"] - sp["delay"]):
        if timestep < sp["latency"] + sp["delay"]:
            dataVector["NO impact on system"][timestep] = dataVector["NO system drift"][timestep]
            
        dataVector["NO impact on system"][timestep + sp["latency"] + sp["delay"]] = dataVector["NO controller total"][timestep + sp["latency"]] + dataVector["NO system drift"][timestep]

    truncatedVector = {}
    for vector in dataVector:
        truncatedVector[vector] = dataVector[vector][:sp["simulationLength"]]
    return truncatedVector



def createDataVector(sp):
    #sp is the SimulationParameters Dict
    #NO = no offset

    varlist = [
        "uncorrected system value",
        "NO delta",
        "NO corrected system value",
        "NO controller total",
        "NO pController",
        "NO iController",
        "NO dController",
        "NO system drift",
        "NO impact on system"
    ]

    dataVector = {}

    for var in varlist:
        dataVector[var] = [0 for _ in range(sp["simulationLength"] + sp["latency"])]

    #Sets the values for the first Row of the DataVector to 1 for all values after latency.
    #The first Row are multipliers, so for the duration of the latency the calculated values will be set to 0 and all following values will be multiplied by 1.
    #for i in range(sp["simulationLength"] + sp["latency"]):
    dataVector["uncorrected system value"][0] = sp["startValue"]
    dataVector["NO corrected system value"][0] = sp["startValue"]

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



def pController(current_Value, pFactor):
    return pFactor * current_Value

def iController(integrationArray, iFactor):
    return iFactor * np.trapz(integrationArray)

def dController(current_Value, past_Value, dLength, dFactor):
    return -1 * dFactor * (current_Value - past_Value) / dLength


if __name__ == "__main__":
    results = {}
    counter = 0
    for dela in range(0,1):
        for lat in range(1,2):
            for ile in range(2,3):
                for dle in range(2,3):
                    for pfa in range(0, 51, 1):
                        pfa2 = pfa / 100
                        for ifa in range(0, 51, 1):
                            ifa2 = ifa / 100
                            for dfa in range(0, 51, 1):
                                dfa2 = dfa / 100
                                counter += 1
                                print(f"{counter} / {51 * 51, 51 * 2 * 2 * 2 * 2}")
                                simulationParameters = {"pFactor" : pfa2 ,
                                                        "iFactor" : ifa2 , "iLength" : ile,
                                                        "dFactor" : dfa2 , "dLength" : dle ,
                                                        "delay": dela,
                                                        "latency" : lat ,
                                                        }
                                median = main(simulationParameters)
                                if abs(100 - median) < 1:
                                    results[counter] = {"delay": dela, "latency": lat, "iLength": ile, "dLength": dle, "pFactor": pfa2, "iFactor": ifa2, "dFactor": dfa2, "median": abs(100 - median)}
    
    with open('results.csv', 'w', newline='') as csvfile:
        fieldnames = ['pFactor', 'iFactor', 'dFactor','delay', 'latency','iLength', 'dLength', 'median']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()                            
        for i in results:
            writer.writerow({'delay': results[i]["delay"], 'latency': results[i]["latency"], 'iLength': results[i]["iLength"], 'dLength': results[i]["dLength"], 'pFactor': results[i]["pFactor"], 'iFactor': results[i]["iFactor"], 'dFactor': results[i]["dFactor"], 'median': results[i]["median"]})
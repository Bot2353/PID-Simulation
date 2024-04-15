import numpy as np
import matplotlib.pyplot as plt


def main():
    simulationParameters = {#General parameters
                            "simulationLength" : 201 ,
                            "startValue" : 20 ,
                            "targetValue" : 230 ,
                            
                            "deviation": 1, "deviationReference": 80, #deviation is a factor

                            #Units
                            "timeUnit": "10 s",
                            "unitName": "Temperature",
                            "unit": "°C",
        
                            #Controller parameters
                            "activeControllers" : "p".lower(),
                            
                            "pFactor" : 0.5 ,
                            "iFactor" : 0.02 , "iLength" : 5,
                            "dFactor" : 1 , "dLength" : 2 ,
                            
                            "delay": 1, #how long the controller takes to impact the system
                            "latency" : 2 , #how long the controller takes to react to changes in the system
                            
                            
                            #System parameters
                            "maxRateOfChange" : 10,  #factor that determines how fast the system is able to be changed with/without a controller
                            "belowZero" : False, #if the controller can go below zero
                            

                            #Additional stresses
                            "deviationStart": 30,
                            "deviationStyle": "constant", #point or constant
                            "deviationValue" : 0,
                            "deviationLength": 5,
                            
                            #Analytics
                            "anaLength": 10, #Percentage of the simulation length that will be used to calculate the median
                            "printDataRows": False
                            
                            }
    
    #Creates a "dataVector" in which all simulation data will be stored.
    dataVector = createDataVector(simulationParameters)
    #Calculates the simulation data
    dataVector = calculateSimulation(simulationParameters, dataVector)
    """
    DATA VECTORS
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
    """

    printData(simulationParameters["printDataRows"], dataVector)
    getAnalytics(simulationParameters, dataVector)
    plotGraphs(simulationParameters ,dataVector)


#FUNCTIONS --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
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
            dataVector["effective controller total"][current_Timestep] = max(min(dataVector["controller total"][current_Timestep], sp["maxRateOfChange"]), -1 * sp["maxRateOfChange"])
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
    if value_Base != 0:
        deviation = -1 * factor * (current_Value - value_Base) / (value_Target - value_Base)
    else:
        deviation = 0
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
        

#Plots graphs
def plotGraphs(sp, dataVector):
    controllerName = sp["activeControllers"].upper()
    lineWidth = 0.75
    fig = plt.figure(figsize= (12,8), dpi= 120, layout="tight", linewidth= lineWidth,facecolor=(0.8,0.8,0.8),)
    fig.suptitle(f"{controllerName}-controller simulation results", fontsize=24)

    #Plot is 5 deep and 8 wide
    plotGrid = (5,8)
    length = range(sp["simulationLength"])
    
    #System behaviour graph
    ax1 = plt.subplot2grid(plotGrid,(0,0),colspan= 4, rowspan = 3)
    
    #Delta graph
    ax2 = plt.subplot2grid(plotGrid,(3,0),colspan= 4, rowspan = 2)


    #PID Value graphs
    
    #Total controller output and effective impact
    ax3 = plt.subplot2grid(plotGrid,(0,4),colspan=4, rowspan = 2)
    #P-Controller output
    ax4 = plt.subplot2grid(plotGrid,(2,4),colspan=2)
    #I-Controller output
    ax5 = plt.subplot2grid(plotGrid,(3,4),colspan=2)
    #D-Controller output
    ax6 = plt.subplot2grid(plotGrid,(4,4),colspan=2)

    #Deviation graph
    ax7 = plt.subplot2grid(plotGrid,(2,6),colspan=2)
    
    ax1.set_title("System values over time")
    ax1.plot(length, dataVector["corrected system value"], label= f"system using {controllerName}-controller", color="blue")
    ax1.plot(length, dataVector["uncorrected system value"], label= "system without a controller", color="orange")

    ax1.axhline(y= sp["targetValue"], color='purple', linestyle=('dashed'), linewidth= lineWidth, label="target value")
    ax1.axhline(y= sp["deviationReference"], color='black', linestyle=('dashed'), linewidth= lineWidth, label = "system baseline (natural state)")
    ax1.axhline(y= dataVector["analytics"]["median corrected"], color="blue", linestyle=('dashed'), linewidth= lineWidth, label=f"median controlled = {round(dataVector['analytics']['median corrected'],3)}")
    ax1.axhline(y= dataVector["analytics"]["median uncorrected"], color="orange", linestyle=('dashed'), linewidth= lineWidth, label=f"median uncontrolled = {round(dataVector['analytics']['median uncorrected'],3)}")

    #Delta graph
    ax2.set_title("Delta between the system's values and target value over time")
    ax2.axhline(y= 0, color="black", linestyle=('dashed'), linewidth= lineWidth, label=f"ideal delta of 0")
    #Inverting the delta for better readability
    delta_controlled_forGraph = [-1 * i for i in dataVector["delta_controlled"]]
    delta_uncontrolled_forGraph = [-1 * i for i in dataVector["delta_uncontrolled"]]
    
    ax2.step(length, delta_controlled_forGraph, where="post", linewidth= lineWidth, color="blue", label="delta of system using controller")
    ax2.step(length, delta_uncontrolled_forGraph, where="post", linewidth= lineWidth, color="orange", label="delta of system without controller")

    #Total controller output graph
    ax3.set_title("Total controller output and effective impact over time")
    ax3.step(length, dataVector["effective controller total"],where="post", linewidth= lineWidth, color="blue", label = f"Effective controller impact \n({sp['activeControllers'].upper()} component/s")
    ax3.step(length, dataVector["controller total"],where="post", color="lightblue", linestyle=('dotted'), label = f"Total controller impulse \n({sp['activeControllers'].upper()} component/s)")
    ax3.axhline(y= sp["maxRateOfChange"], color="red", linestyle=('dashed'), linewidth= lineWidth, label=f"maximal rate of change \n= {sp['maxRateOfChange']} {sp['unit']} / {sp['timeUnit']}")
    if sp["belowZero"] == False:
        ax3.axhline(y= 0, color="red", linestyle=('dashed'), linewidth= lineWidth, label=f"minimal rate of change = 0")
    elif sp["belowZero"] == True:
        ax3.axhline(y= -1 * sp["maxRateOfChange"], color="red", linestyle=('dashed'), linewidth= lineWidth, label=f"minimal rate of change \n= -{sp['maxRateOfChange']} {sp['unit']} / {sp['timeUnit']}")
    ax3.plot(length, dataVector["impact on system"], linewidth= lineWidth, color = "purple", label = f"Resulting real impact\nrespecting timing and deviation")

    #Controller output graphs
    #P-Controller output
    ax4.set_title("P-Controller output over time")
    ax4.step(length, dataVector["pController"], where="post", linewidth= lineWidth, color="blue")

    #I-Controller output
    ax5.set_title("I-Controller output over time")
    ax5.step(length, dataVector["iController"], where="post", linewidth= lineWidth, color="blue")

    #D-Controller output
    ax6.set_title("D-Controller output over time")
    ax6.step(length, dataVector["dController"], where="post", linewidth= lineWidth, color="blue")

    #Deviation graph (shows the natural drift of the system towards the baseline value)
    ax7.set_title(f"System drift \n(towards baseline)")
    ax7.axhline(y= 0, color='red', linestyle=('dashed'), linewidth= lineWidth)
    ax7.plot(length, dataVector["system drift"],  linewidth= lineWidth, color="black")

    #Adjusting labels to show units
    for i in [ax1, ax2, ax3, ax4, ax5, ax6, ax7]:
        i.set_xlabel(f"Simulation timesteps [{sp['timeUnit']}]")
        if i == ax1:
            i.set_ylabel(f"{sp['unitName']} [{sp['unit']}]")
        elif i == ax2:
            i.set_ylabel(f"{sp['unitName']} difference [{sp['unit']}]")
        elif i == ax3:
            i.set_ylabel(f"{sp['unitName']} change per {sp['timeUnit']} [{sp['unit']}]")
        
        elif i == ax7:
            i.set_ylabel(f"{sp['unitName']} \ndeviation [{sp['unit']}]")
        i.set_facecolor("white")

    #Scale legend font for readability on FHD screens
    fontscl = 6
    ax1.legend(fontsize = fontscl)
    ax2.legend(fontsize = fontscl)
    ax3.legend(fontsize = fontscl)

    plt.show()


#Prints data for manual analysis and plausibility checks
def printData(bool, dataVector):
    if bool:
        for i in dataVector:
            print(f"{i}            - {dataVector[i]}")



if __name__ == "__main__":
    main()
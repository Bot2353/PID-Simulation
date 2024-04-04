import numpy as np
import matplotlib.pyplot as plt

simulationParameters = {"pFactor" : 20 ,
                        "iFactor" : 0.4 , "iLength" : 10 ,
                        "dFactor" : 100 , "dLength" : 2 ,
                        "latency" : 5 ,
                        "simulationLength" : 30 ,
                        "sensitivity" : 50 ,
                        "startValue" : 0 ,
                        "targetValue" : 100 ,
                        "deviation": 0.05, "deviationStyle": "c", "deviationReference": 0,
                        "deviationLocation" : None , "deviationLowerLimit" : 1 , "deviationUpperLimit" : 2 ,
                        }
activeControllers = "d"

#dv0 = uncontrolled deviation
#dv1 = controlled deviation
#dv2 = p controller
#dv3 = i controller
#dv4 = d controller
#dv5 = deviation
#dv6 = delta

def main():
    fixInputs(simulationParameters)    
    dataVector = createVector(simulationParameters["simulationLength"], simulationParameters["latency"], simulationParameters["startValue"], max(simulationParameters["iLength"],simulationParameters["dLength"]))
    dataVector = pidController(dataVector, simulationParameters, activeControllers)
    plotGraphs(dataVector, simulationParameters["targetValue"])
        
def pidController(dV, simPara, active):
    maxControllerLength = max(simPara["iLength"],simPara["dLength"])
    for i in range(maxControllerLength, simPara["simulationLength"] + maxControllerLength):
        ind = i+simPara["latency"]
        dV[6][ind] = simPara["targetValue"] - dV[1][i]
        dV[5][i] = deviation(simPara["deviationStyle"], simPara["deviation"], simPara["deviationReference"] - dV[1][i-1])
        #print(dV[5][i])
        if abs(simPara["targetValue"] - dV[1][i-1]) > simPara["sensitivity"]:
            if "p" in active.lower(): dV[2][ind] = pController(dV[6][ind], simPara["pFactor"])
            #if "i" in active.lower(): dV[3][ind] = iController(simPara["iFactor"], dV[6][i - simPara["iLength"]:i])
            if "i" in active.lower(): dV[3][ind] = iController(simPara["iFactor"], dV[6][:i])
            if "d" in active.lower(): dV[4][ind] = dController(simPara["dFactor"], dV[5][i - simPara["dLength"]:i])
            try:
                None
                #print(dV[1][i - 2:i], simPara["dFactor"] * np.diff(dV[1][i - 2:i])[0])
                #print(dV[6][i - simPara["iLength"]:i], simPara["iFactor"] * np.trapz(dV[6][i - simPara["iLength"]:i]))
            except:
                None
        else:
            dV[2][ind] = 0
            dV[3][ind] = 0
            dV[4][ind] = 0
        #print(dV[2][ind]+dV[3][ind]+dV[4][ind])
        dV[0][i+1] = dV[0][i] + dV[5][i]
        dV[1][ind] = dV[1][ind-1] + dV[2][ind] +dV[3][ind] +dV[4][ind] + dV[5][i]
    #print(dV[4])
    return dV[:, maxControllerLength : simPara["simulationLength"] + maxControllerLength]
    
def deviation(deviationStyle, deviation, deltaReference):
    #deviation = deviation
    if deviationStyle.startswith("l"):
        return deltaReference * deviation
    else:
        return deviation
   
def plotGraphs(dV, targetValue):
    t = range(len(dV[0]))
    yUncontrolledDeviation = dV[0]
    yControlledDeviation = dV[1]
    yDelta = dV[6]
    fig = plt.figure()
    ax = fig.add_subplot(1,1,1)
    #ax.plot(t, yUncontrolledDeviation)
    ax.plot(t, yControlledDeviation)
    #ax.plot(t, yDelta)
    ax.axhline(targetValue)
    plt.show()
    
    
def pController(delta, pFactor):
    return  (delta) * pFactor
        
        
def iController(iFactor, controlledDeviation):
    try:
        return iFactor * np.sum(controlledDeviation)
    except:
        print("iif")
        return 0


def dController(dFactor, controlledDeviation):
    #print(f"{controlledDeviation}")
    try:
        return dFactor * (controlledDeviation[-1]-controlledDeviation[0])
    except:
        print("oof")
        return 0
    
    
def createVector(length, latency, startValue, maxLength):
    dataVector = np.zeros((7, length + latency + maxLength))
    #dataVector[5] = constDiv
    for i in range(latency + maxLength):
        dataVector[0][i] = startValue
        dataVector[1][i] = startValue
        #dataVector[5][i] = 0
    #print(dataVector[6])
    return dataVector


def fixInputs(simPara):
    simPara["simulationLength"] += 1
    simPara["pFactor"] = 10 ** -2 * simPara["pFactor"]
    simPara["iFactor"] = 10 ** -2 * simPara["iFactor"]
    simPara["dFactor"] = 10 ** -2 * simPara["dFactor"]
    #simPara["deviation"] =  -1 * simPara["deviation"]
    #simPara["iLength"] = -1 * simPara["iLength"]
    simPara["sensitivity"] = 10 ** (-simPara["sensitivity"])
    simPara["deviationLocation"] = 1
    simPara["latency"] += 1
    

if __name__ == "__main__":
    main()
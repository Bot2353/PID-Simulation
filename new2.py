import numpy as np
import matplotlib.pyplot as plt

simulationParameters = {"pFactor" : 0.2 ,
                        "iFactor" : 0.4 , "iLength" : 3 ,
                        "dFactor" : 1 , "dLength" : 2 ,
                        "latency" : 5 ,
                        "simulationLength" : 30 ,
                        "sensitivity" : 50 ,
                        "startValue" : 1 ,
                        "targetValue" : 100 ,
                        "deviationFactor": 2, "deviationReference": 0,
                        "deviationLocation" : None , "deviationLowerLimit" : 1 , "deviationUpperLimit" : 2 ,
                        }
activeControllers = "pid"

#dv0 = uncontrolled deviation
#dv1 = controlled deviation
#dv2 = p controller
#dv3 = i controller
#dv4 = d controller
#dv5 = deviation
#dv6 = delta

def main():
    #Corrects user input values for ease of use.
    fixInputs()
    
    #Creates an empty Vector to store the simulation data in
    dataVector = createVector()
    dataVector = simulate(dataVector)
    print(dataVector)
        

def simulate(dataVector):
    deviation_Uncontrolled  = dataVector[0]
    deviation_Controlled    = dataVector[1]
    pController             = dataVector[2]
    iController             = dataVector[3]
    dController             = dataVector[4]
    system_Deviation        = dataVector[5]
    Delta                   = dataVector[6]
    
    
    
    for i in range(simulationParameters["simulationLength"]):
        #Sets current value to the last value in "dataVector[1]"
        value_Current = deviation_Controlled[-1]
        
        #Calculates and appends the current Delta to "dataVector[6]"
        np.append(Delta, delta(value_Current))
        delta_Current = Delta[-1]
        
        np.append(system_Deviation ,deviation(value_Current))
        deviation_Current = system_Deviation[-1]
        
        np.append(deviation_Uncontrolled, value_Current + deviation_Current)

    return dataVector


def delta(value_Current):
    target = simulationParameters["targetValue"]
    return target - value_Current

    
def deviation(value_Current):
    #Calculates where the current value lies between the Base and target value. Multiplies that with the deviation factor.
    value_Base = simulationParameters["deviationReference"]
    value_Target = simulationParameters["targetValue"]
    factor_Deviation = simulationParameters["deviationFactor"]
    
    ratio = (value_Current - value_Base) / (value_Target-value_Base)
    
    return - ratio * factor_Deviation

    
    
def pidController():
    for i in activeControllers:
        print(i)
    
def pController():
    
    return  (delta) * pFactor
        
        
def iController():
    try:
        return iFactor * np.sum(controlledDeviation)
    except:
        print("iif")
        return 0


def dController():

    try:
        return dFactor * (controlledDeviation[-1]-controlledDeviation[0])
    except:
        print("oof")
        return 0
    
    
def createVector():
    length_LongestController    = max(simulationParameters["iLength"], simulationParameters["dLength"])
    lenght_Simulation           = simulationParameters["simulationLength"]
    length_Latency              = simulationParameters["latency"]
    value_Start                 = simulationParameters["startValue"]
    
    """
    Creates 7-dimensional Vector. Each dimension corresponds to one tracked value. 
    The length is equal to the simulation length plus latency plus the longest controller.
    """
    #dataVector = np.zeros((7, lenght_Simulation + length_Latency + length_LongestController))
    
    dataVector = np.zeros((7, 1))
    dataVector[0][0] = value_Start
    dataVector[1][0] = value_Start
    #Sets the first values for both controlled and uncontrolled deviation to the start value, since the controllers 
    #for i in range(length_Latency + length_LongestController):
    #    dataVector[0][i] = value_Start
    #    dataVector[1][i] = value_Start
        
    return dataVector


def fixInputs():
    simulationParameters["simulationLength"] += 1    


if __name__ == "__main__":
    main()
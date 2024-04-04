import random
import matplotlib.pyplot as plt
import sys
import csv
import numpy as np
import os


def main():
    #Variablen
    Dauer               = 300                       #Dauer der Simulation in Zeitschritten
    Sollwert            = 0                         #Zielwert auf den geregelt werden soll
    abweichungsLimits   = 10                        #Maximale Abweichung die ein Abweichungselement haben darf
    GraphPlusMinus      = abweichungsLimits // 5                               
    abweichungsMenge    = 1
    pFaktor             = 0.2
    iFaktor             = 1
    iLänge              = 3
    dFaktor             = 0.9
    dLänge              = 2
    dMinimum            = 0.00001
    minAbweichungsLänge = round(Dauer/10)
    maxAbweichungsLänge = minAbweichungsLänge * 2   
    RegelVerzögerung    = 5                        #Muss mindestens 1 sein, keine Verzögerung wäre unmöglich
    Rundungsfaktor      = 3
    Aktiv               = "d"
    DualPlot            = True
    
    
    #Zahlenfixen
    Dauer += 1
    if Dauer < maxAbweichungsLänge + 1:
        maxAbweichungsLänge = Dauer - 1
    
    aktiveRegler = list(Aktiv.upper())
    for i in aktiveRegler:
        print(f"{i}-Regler aktiv")
        
    
    #Versucht das erste Argument als Quelle für eine AbweichungsImpuls Datei zu nehmen. Generiert sonst eine zufällige AbweichungsImpuls Liste.
    #Sucht nur im CWD, also in dem Ordner in dem sich auch die .py Datei selbst befindet
    try:
        with open(f"{os.getcwd()}/{sys.argv[1]}") as f:
            strliste = list(csv.reader(f,skipinitialspace=True))[0]
            AbweichungsImpuls = [int(i) for i in strliste]
            Dauer = len(AbweichungsImpuls)
            if input("Möchten Sie einen Sollwert festlegen? (y/n): ") == "y":
                Sollwert = int(input("Bitte geben Sie den Sollwert an: ").strip())
            else:
                Sollwert = AbweichungsImpuls[0]
            abweichungsLimits = max([max(AbweichungsImpuls),abs(min(AbweichungsImpuls))])
            print(abweichungsLimits)
            print(f'Abweichungskurve aus Datei {sys.argv[1]} geladen')
            f.close()
    except:
        AbweichungsImpuls = Abweichung(Dauer,abweichungsLimits,abweichungsMenge, Sollwert,minAbweichungsLänge, maxAbweichungsLänge, Rundungsfaktor)
           
    #Generiert die Abweichungskurve aus der AbweichungsImpuls Liste.
    AbweichungsKurve = Abweichungskurve(Sollwert, Dauer , AbweichungsImpuls)
    

    #Generiert RegelImpuls
    GeregelteAbweichung = [AbweichungsKurve[0]]
    GesamtRegelImpuls = [0 for i in range(RegelVerzögerung)]
    pListe = [0 for i in range(RegelVerzögerung)]
    iListe = [0 for i in range(RegelVerzögerung)]
    dListe = [0 for i in range(RegelVerzögerung)]
    
    #RegelImpulse
    
    for i in range(Dauer):
        gesamtRegelImpuls = 0
        if "P" in aktiveRegler:
            pv = pRegler(Sollwert, GeregelteAbweichung[i], pFaktor)
            pListe.append(round(pv, Rundungsfaktor))
            gesamtRegelImpuls += pv 
        if "I" in aktiveRegler:
            iv = iRegler(GeregelteAbweichung, iFaktor, iLänge)
            iListe.append(round(iv, Rundungsfaktor))
            gesamtRegelImpuls += iv
        if "D" in aktiveRegler:
            #print(f"Geregelte Abweichung: {GeregelteAbweichung[i]}")
            dv = dRegler(GeregelteAbweichung, dFaktor, dMinimum, dLänge)
            dListe.append(round(dv, Rundungsfaktor))
            gesamtRegelImpuls += dv
        GesamtRegelImpuls.append(round(gesamtRegelImpuls, Rundungsfaktor))
        
        GeregelteAbweichung.append(GeregelteAbweichung[i] + AbweichungsImpuls[i] + GesamtRegelImpuls[i]) #Erstellt die geregelte Abweichungskurve aus dem letzten Wert + Wert der im nächsten Schritt abgewichen wird + dem Regelimpuls
        
    GeregelteAbweichung.pop(0)
     
    
    werte = GeregelteAbweichung + GesamtRegelImpuls + AbweichungsImpuls
    yMax = max(werte) + GraphPlusMinus
    yMin = min(werte) - GraphPlusMinus
        
    
    #Plottet den Graphen
    if DualPlot == False:
        fig, (ax1) = plt.subplots(1, 1)
        plotSelector = ax1
    else:
        fig, (ax1,ax2) = plt.subplots(2, 1, sharex=True)
        plotSelector = ax2
        ax1.set_ylabel("Abweichung vom Sollwert")
        ax2.set_ylabel("Abweichungs- und Regelimpuls")
        
            
    ax1.axis([0,Dauer,yMin,yMax]) 
    
    ax1.set_xlabel("Zeit")
    
    ax1.axhline(y=Sollwert, color='black', linestyle=('dashed'))
    ax1.axhline(y=Sollwert-abweichungsLimits, color='red', linestyle=('dashed'))
    ax1.axhline(y=Sollwert+abweichungsLimits, color='red', linestyle=('dashed'))
    
    ax1.plot(list(range(Dauer)),AbweichungsKurve, color="y", label="Ungeregelte Abweichung")
    ax1.plot(list(range(Dauer)),GeregelteAbweichung[:Dauer], color="g", label="Geregelte Abweichung")
    
    
    
    plotSelector.set_xlabel("Zeit")
    
    plotSelector.axhline(y=Sollwert, color='black', linestyle=('dashed'))
    
    plotSelector.plot(list(range(Dauer)),AbweichungsImpuls, color="r", label="Abweichungsimpuls")
    plotSelector.plot(list(range(Dauer)),GesamtRegelImpuls[:Dauer], color="b", label="Gesamtregelimpuls") 
    
    
    fig.suptitle(f"{''.join(aktiveRegler)}-Regelkurve")
    ax1.legend()
    plotSelector.legend()
    plt.show()
    
    


def pRegler(Sollwert, Wert, Kp): #Nimmt Sollwert und aktuellen Wert
    return (Sollwert - Wert) * Kp

def iRegler(GeregelteAbweichung, Ki, iLänge):
    try:
        return (-1 * np.trapz(GeregelteAbweichung[-iLänge:]) * Ki) / (len(GeregelteAbweichung))
    except:
        print("oof")
        return 0

def dRegler(GeregelteAbweichung, Kd, dMinimum, dLänge):
    try:
        val = (-1 * np.diff(GeregelteAbweichung[-dLänge:]) * Kd)[-1]
        if abs(val) <= dMinimum:
            return 0
        else:
            return val
    except:
        return 0



def Abweichung(Dauer,abweichungsLimits,abweichungsMenge, Sollwert,minAbweichungsLänge, maxAbweichungsLänge, rundungsFaktor):
    AbweichungsImpuls = [0 for i in range(Dauer)]
    
    abweichungsStarts = sorted([random.choice(range(Dauer - maxAbweichungsLänge)) for i in range(abweichungsMenge)])
    
        
    for i in range(len(abweichungsStarts)):
        abweichungsRange    = list(range(abweichungsStarts[i],abweichungsStarts[i]+random.randint(minAbweichungsLänge,maxAbweichungsLänge)))
        Abweichungswert     = random.randint(Sollwert - abweichungsLimits, Sollwert + abweichungsLimits)
        while Abweichungswert == 0:
            Abweichungswert     = random.randint(Sollwert - abweichungsLimits, Sollwert + abweichungsLimits)

        random.choice([konstantAbweichung,linearAbweichung,exponentialAbweichung])(AbweichungsImpuls, abweichungsRange, Abweichungswert, rundungsFaktor)
    return AbweichungsImpuls


def Abweichungskurve(Sollwert, Dauer, AbweichungsImpuls):
    Abweichungskurve = [Sollwert]
    for i in range(Dauer):
        Abweichungskurve.append(Abweichungskurve[i] + AbweichungsImpuls[i])
    return Abweichungskurve[1:]



def konstantAbweichung(AbweichungsImpuls, abweichungsRange, Abweichungswert, rundungsFaktor):
    print(f"Konstante Abweichung von {Abweichungswert} an {abweichungsRange[0]}")
    AbweichungsImpuls[abweichungsRange[0]] = Abweichungswert
    
def linearAbweichung(AbweichungsImpuls, abweichungsRange, Abweichungswert,rundungsFaktor):
    Steigung = round(Abweichungswert / len(abweichungsRange),rundungsFaktor)
    print(f"Linear wachsende Abweichung von {round(Steigung, rundungsFaktor)} zwischen {abweichungsRange[0]} und {abweichungsRange[-1]}")
    for i in abweichungsRange:
        AbweichungsImpuls[i] = round(Steigung,rundungsFaktor)
    
def exponentialAbweichung(AbweichungsImpuls, abweichungsRange, Abweichungswert, rundungsFaktor):
    #print(f"Abweichungswert: {Abweichungswert}\nAbweichungsrange: {len(abweichungsRange)}")
    Exponent = np.power(abs(Abweichungswert), 1 / len(abweichungsRange))
    print(f"Exponentiell wachsende Abweichung von {Exponent} zwischen {abweichungsRange[0]} und {abweichungsRange[-1]}")
    
    abweichungsRange.insert(0,0)
   
    for y, val in enumerate(abweichungsRange[1:]):  
        #print(Exponent, len(abweichungsRange[:y])+1)
        AbweichungsImpuls[val] = Exponent ** (len(abweichungsRange[:y])+1)
        if Abweichungswert < 0:
            AbweichungsImpuls[val] = AbweichungsImpuls[val] * -1


if __name__ == "__main__":
    main()
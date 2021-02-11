import pyatspi

#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

if __name__ == '__main__':

    desktop = pyatspi.Registry.getDesktop(0)
    for application in desktop:
        if application.name == "ipm-p1.py" or application.name == "ipm-p1":
            target = application

    targetWindow=None
    if application:
        print(application)
        for frame in application:
            print(frame)
            if frame.name == "IPM-p1":
                targetWindow = frame


    if targetWindow:
        print(targetWindow)
        for menu in targetWindow:
            print(menu)
    
    panel = targetWindow[0]
    filler = targetWindow[1]
    
    print("top bar panel")
    print("panel has")
    for o in panel:
        print("\t"+str(o))
        for u in o:
            print("\t\t"+str(u))
        
    print("main section")
    main_panel = None
    print("filler has:")
    for o in filler:
        print("\t"+str(o))
        for u in o:
            print("\t\t"+str(u))
            main_panel = u 
    
    scroll1 = main_panel[1]
    scroll2 = main_panel[2]
    for x in main_panel:
        print("\t\t\t"+str(x))
    
    print("exercises")
    table1 = scroll1[0]
    for e in scroll1:
        print(e)
        for x in e:
            print("\t"+str(x))

    achilles=None 
    print("workouts")
    table2 = scroll2[0]
    for e in scroll2:
        print(e)
        for x in e:
            print("\t"+str(x.name))
            if x.name == "Achilles":
                achilles = x
    if achilles:
        print("got achilles:")
        print(achilles)
           

    def f(e):
        if e.source == achilles:
            print("tabla de ejercicios:")
            table1 = scroll1[0]
            count=-5
            exercises_names=[]
            for e in table1:
                if (count % 4) == 2 and count > 0:
                    exercises_names.append(e.name)
                    print("\t"+str(count)+" --> "+str(e.name).strip("\n"))
                count+=1
            if len(exercises_names) == 26:
                print("Test Ok")
            else:
                print("Test Error")
            print("26 expected, got "+str(len(exercises_names)))

    pyatspi.Registry.registerEventListener(f, "object:state-changed:focused")
    pyatspi.Registry.start()

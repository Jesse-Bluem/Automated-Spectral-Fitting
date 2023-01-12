# -*- coding: utf-8 -*-
"""
Created on Tue Nov 17 19:25:30 2020

@author: Jesse's AE Build
"""

import xspec as xs
import sys
import csv
from datetime import datetime
#from numpy import array
#import matplotlib.pyplot as plt

#This code requires a .txt config file to run. which is supplied on the command line.

#Example config file:
#***Config File for xspectations.py***
#***Note, add tab between every entry/slot on a line***
#
#***Data file locations and settings***
#***Parameters are a CSV, first row is XSPEC parameter labels, other rows data***
#***Row 1 is spectral target label for the row, each row is a new spectra/target***
#***This step must come first in config*** 
#***Spectra directory is location of spectra with files using same names as in in CSV***
#***Filename format expected is target+data label+extension (ext/data label set later)***
#data	parameters	Book1.csv
#data	spectra directory	
#data	outfile directory	
#
#***N data sets and their respective labels, this is the order they will be loaded***
#***These should match the difference in the file names between the data sets***
#datasets	3	14,38,54
#
#***spectra file extension, the "." is expected***
#extension	.pi
#
#***Generic settings***
#setting	energy range	0.4-7.0
#setting	plot type	data delchi
#
#***XSPEC specific settings - use proper XSPEC syntax***
#***for Plot.addCommand, do Plot.addCommand\tvalue rather than Plot.addcommand('value')***
#***\t = tab***
#setting	Fit.statMethod	chi
#setting	Fit.statTest	chi
#setting Fit.method	leven 10 0.01
#setting Xset.abund	wilm
#setting	Xset.xsect	vern
#setting	Plot.device	/xs
#setting	Plot.xAxis	keV
#setting	Plot.xLog	True
#setting	Plot.yLog	True
#setting	Plot.splashPage	False
#setting	Plot.add	True
#setting	Plot.addCommand	time off
#setting	Plot.addCommand	label top
#setting Fit.nIterations	10000
#setting	Fit.query	yes
#
#***XSPEC model, slot 2 is model name, 3 is model itself, XSPEC syntax from here out in config***
#***These will be assigned to pyXSPEC in the order provided***
#model	src	gaussian + gaussian + apec + TBabs(apec + power)
#model	bkg	power
#
#***rmf/arf for each model/dataset combo, use same order as defined in XSPEC model section***
#***number starts at 0. Use None if not using an arf and/or rmf***
#rmf	14	0	Halosat_avgenoise_20190423.rmf
#arf	14	0	Halosat_20190211.arf
#rmf	14	1	Halosat_diag_20190423.rmf
#arf	14	1	None
#rmf	38	0	Halosat_avgenoise_20190423.rmf
#arf	38	0	Halosat_20190211.arf
#rmf	38	1	Halosat_diag_20190423.rmf
#arf	38	1	None
#rmf	54	0	Halosat_avgenoise_20190423.rmf
#arf	54	0	Halosat_20190211.arf
#rmf	54	1	Halosat_diag_20190423.rmf
#arf	54	1	None
#
#***Global parameters that are true for all data sets, use the -1 syntax to freeze***
#***-1 to freeze is same entry/slot number as parameter value, not tabbed between***
#***Slot/entry 3 IDs which model the parameter is assigned to***
#parameter	global	src	gaussian.LineE	0.5634 -1
#parameter	global	src	gaussian.Sigma	0.0010 -1
#parameter	global	src	gaussian_2.LineE	0.6531 -1
#parameter	global	src	gaussian_2.Sigma	0.0010 -1
#parameter	global	src	apec.kT	0.0970 -1
#parameter	global	src	apec_5.Abundanc	0.3000 -1
#parameter	global	src	powerlaw.PhoIndex	1.4500 -1
#parameter	global	src	powerlaw.norm	0.3800 -1
#
#***Data set specific global parameters, slot 2 # is load order as defined in datasets***
#***Note, you must provide starting values for any set components you do not want linked***
#parameter	2	bkg	powerlaw.norm	0.5
#parameter	3	bkg	powerlaw.norm	0.6

#*********************************************************************************************

#Parameters are set in a CSV file. Example:
#CSV file column label format is TYPE MODEL PARAMETER, where...
#TYPE = global if the parameter is true for all data sets in the observation, otherwise a number from 1 to N identifying which of N data sets it belongs to.
#MODEL = model label supplied to XSPEC that the parameter belongs to
#PARAMETER = pyXSPEC nomenclature for a parameter label
#target,global src gaussian.norm,global src gaussian_2.norm,global src apec.norm,global src TBabs.nH,1 bkg powerlaw.PhoIndex,2 bkg powerlaw.PhoIndex,3 bkg powerlaw.PhoIndex
#297_,0.0276 -1,0.0025 -1,0.1169 -1,0.0605 -1,0.8531 -1,0.8209 -1,0.8459 -1
#302_,0.0376 -1,0.0035 -1,0.1369 -1,0.0305 -1,0.8331 -1,0.8309 -1,0.8359 -1  

#*********************************************************************************************

def parsefile(filenam):
    f=open(filenam) #config file that sets model and params and such
    g=f.readlines() 
    for l in g:
        if l[0:3] != '***': #instructional lines, ignore
            if l != '\n': #do not punish emtpy lines
                b=(l.split('\t')) #tab is default break between label and value in config file
                print(b)
                vals=b[-1].split('\n')[0] #the extracted value, with any terminal new line removed, is always last thing on a line
                key1=b[0]
                if key1 == 'data':
                    if b[1] == 'parameters':
                        paradict=csver(vals) #This creates paradict where params live.
                    if b[1] == 'spectra directory':
                        comdict['specdirect']=vals
                    if b[1] == 'outfile directory':
                        comdict['outdirect']=vals #This creates paradict where params live.
                if key1 == 'parameter':
                    key2=b[1]
                    key4=b[3]
                    for tgt in paradict:
                        if key2 not in paradict[tgt]:
                            paradict[tgt][key2]={}
                        paradict[tgt][key2][key4]={}
                        paradict[tgt][key2][key4]['val']=vals #label from config becomes dict key
                        paradict[tgt][key2][key4]['mod']=b[2]
                if key1 == 'model':
                    key2=b[1] #model label
                    moddict[key2]=vals #actual model
                    global addict
                    if addict == 0:
                        athing=len(vals.split('+'))
                        addict=athing
                if key1 == 'extension': #spectra file extension
                    setdict['extension']=vals
                if key1 == 'setting':
                    key2=b[1]
                    if key2=='Plot.addCommand':
                        setdict['PAC'].append(vals)
                    else:
                        setdict[key2]=vals
                if key1 == 'rmf': #save rmf info
                    b[-1]=vals
                    setdict['rmf'].append(b)
                if key1 == 'arf': #save arf info
                    b[-1]=vals
                    setdict['arf'].append(b)                 
                if key1 == "datasets":
                    ds=int(b[1])
                    comdict['Ndata']=ds #record numnber of expected data sets
                    names=vals.split(',')
                    comdict['datasets']={} #data labels here
                    comdict['datasets']['names']=names
                    for x in range(ds):
                        comdict['datasets'][names[x]]=x+1 #add each data label
    f.close()
    return paradict
                
def loaddata(FN): #load the data for 1 target, filename FN
    FN=comdict['specdirect']+FN
    xs.AllData.clear()
    fullcomstr = '' #full data loading string for later, build in loop
    for L in range(comdict['Ndata']):#iterate over data sets
        numb=str(L+1) #number used to load in xspec
        comstr=numb+':'+numb+' '+FN+comdict['datasets']['names'][L]+setdict['extension']+' '
        fullcomstr += comstr
    xs.AllData(fullcomstr)
    for th in setdict['rmf']:
        datlab=th[1] #this is a data label from config. 2 is model number
        if th[3] != 'None':
            xs.AllData(comdict['datasets'][datlab]).multiresponse[int(th[2])] = th[3]
    for th in setdict['arf']:
        datlab=th[1] #this is a data label from config. 2 is model number
        if th[3] != 'None':
            xs.AllData(comdict['datasets'][datlab]).multiresponse[int(th[2])].arf = th[3]
    
    #xs.AllData("1:1 297_14.pi 2:2 297_38.pi 3:3 297_54.pi")
    #xs.AllData("1:1 hs029701_s14.pi 2:2 hs029701_s38.pi 3:3 hs029701_s54.pi")
    #xs.AllData(1).multiresponse[0] = 'Halosat_avgenoise_20190423.rmf'
    #xs.AllData(1).multiresponse[0].arf = 'Halosat_20190211.arf'
    #xs.AllData(1).multiresponse[1] = 'Halosat_diag_20190423.rmf'
    #xs.AllData(2).multiresponse[0] = 'Halosat_avgenoise_20190423.rmf'
    #xs.AllData(2).multiresponse[0].arf = 'Halosat_20190211.arf'
    #xs.AllData(2).multiresponse[1] = 'Halosat_diag_20190423.rmf'
    #xs.AllData(3).multiresponse[0] = 'Halosat_avgenoise_20190423.rmf'
    #xs.AllData(3).multiresponse[0].arf = 'Halosat_20190211.arf'
    #xs.AllData(3).multiresponse[1] = 'Halosat_diag_20190423.rmf'
    #xs.AllData.show()

def setsettings():
    for ki in setdict:
        out=setdict[ki]
        if out == 'True':
            out=True
        if out == 'False':
            out=False
        if ki == "energy range": #set min/max energy
            outro=out.split('-')
            setlo='0.0-'+outro[0]
            sethi=outro[1]+'-**'
            xs.AllData.ignore(setlo)
            xs.AllData.ignore(sethi)
        elif ki == "plot type": #store plot command for later
            comdict['plottype']=out
        elif ki == "PAC":
            for com in out:
                print(com)
                xs.Plot.addCommand(com)
        elif ki == "rmf" or ki == "arf":
            contin=1
        else:
            x="xs."+ki #is this broken? - yes. it is.
            exec("%s = %r" % (x,out)) #do other settings.
    #xs.Plot.add=True
        
def csver(infil):
    outl=[]
    with open(infil, newline='') as csvfile:
         reader = csv.reader(csvfile, delimiter=',', quotechar='|')
         for row in reader:
             if row != '':
                 if row != '\n':
                     outl.append(row) #We've converted CSV to a list of lists. Remove blanks
    titlecard=outl[0] #headers for columns, extract these
    outl.pop(0) #kill headers in orig list
    csvdict={}
       
    for row in outl: #each row is parameters for 1 target spectra
        tgt=row[0] #specific target name for spectra
        csvdict[tgt]={} #generates a dict entry for each row in csv [each target/spex]
        for xn in range(len(titlecard)):
            if xn>0:
                ent=titlecard[xn].split(' ')
                csvdict[tgt][ent[0]]={} #creates subdicts for global and data set specific parameters
        #The dictionary architecture is set, now populate   
        for X in range(len(row)): #iterate over parameters
            if X > 0: #target name already collected
                outage=titlecard[X].split(' ') #split data set and XSPEC parameter
                csvdict[tgt][outage[0]][outage[2]]={}
                csvdict[tgt][outage[0]][outage[2]]['val']=row[X] #row here is the XSPEC param value and possible -1 for freeze
                csvdict[tgt][outage[0]][outage[2]]['mod']=outage[1]
    return csvdict
            
def domodel():
    resort=[]
    for ki in moddict:
        resort.append(ki)
    for x in range(len(resort)):
        xs.AllModels += (moddict[resort[x]], resort[x], x+1) #sets each model, includes label
        
    #xs.AllModels += ("gauss + gauss + apec + TBabs(apec + power)", 'src', 1)
    #xs.Model('pow', 'bkg', 2)

def setmodel(tgtki): #takes in current target being run
    for kii in paradict[tgtki]: #kii is global + specific localized params that get set.
        if kii == 'global':
            for ki in paradict[tgtki]['global']:
                #dict key 'ki' is model parameter
                valu=paradict[tgtki]['global'][ki]['val'].split(' ') #value to set it to, split off the freeze "-1"
                labl=paradict[tgtki]['global'][ki]['mod'] #model label for current parameter
                x="xs.AllModels(1, '"+labl+"')."+ki #command to set model param
                exec("%s = %s" % (x,valu[0])) #sets, but won't freeze for some reason
                if len(valu)>1: #extra things in param list exist
                    if valu[1]=="-1": #is the thing the -1 command to freeze?
                        exec("%s = %r" % (x+'.frozen',True)) #freezes supplied model component.
        else:
            for ki in paradict[tgtki][kii]:
                #dict key 'ki' is model parameter.
                valu=paradict[tgtki][kii][ki]['val'].split(' ') #value to set it to, split off the freeze "-1"
                labl=paradict[tgtki][kii][ki]['mod']
                x="xs.AllModels("+kii+", '"+labl+"')."+ki #command to set model param
                exec("%s = %s" % (x,valu[0])) #sets, but won't freeze for some reason
                if len(valu)>1: #extra things in param list exist
                    if valu[1]=="-1": #is the thing the -1 command to freeze?
                        exec("%s = %r" % (x+'.frozen',True)) #freezes supplied model component.            
    #print(dir(xs.AllModels(1, 'src'))) #print out things stored in obj - gets vars.

def fitnshit(key): #does what it says on the tin
    xs.Fit.perform()
    xs.AllModels(1, 'src').apec_3.kT.frozen = False
    #xs.AllModels(1, 'src').apec_5.kT.frozen = False
#    xs.Fit.steppar("src:6 0.14 0.2 50")# src:12 0.55 0.85 50")
#    dats1=(xs.Fit.stepparResults('src:6'))
#    #dats2=(xs.Fit.stepparResults('src:12'))
#    dats3=xs.Fit.stepparResults('delstat')
#    M=min(dats3)
#    NID=dats3.index(M)
#    f=open(comdict['outdirect']+key+'step.txt','w+')
#    f.write(key)
#    f.write('\n')
#    f.write(str(M))
#    f.write('\n')
#    f.write(str(dats1[NID]))
#    f.write('\n')
#    #f.write(str(dats2[NID]))
#    f.write('\n')
#    xs.Fit.perform()
#    xs.Fit.steppar("src:6 0.14 0.2 50")# src:12 0.55 0.85 50")
#    dats1=(xs.Fit.stepparResults('src:6'))
#    #dats2=(xs.Fit.stepparResults('src:12'))
#    dats3=xs.Fit.stepparResults('delstat')
#    M=min(dats3)
#    NID=dats3.index(M)
#    #f=open(comdict['outdirect']+key+'step.txt','w+')
#    f.write(key)
#    f.write('\n')
#    f.write(str(M))
#    f.write('\n')
#    f.write(str(dats1[NID]))
#    f.write('\n')
#    #f.write(str(dats2[NID]))
#    f.write('\n')
#    #xs.Fit.stepparResults('delstat')) #delta stat, find best.
#    f.close()
    #xs.AllData.notice('6.0-10.0')#hardcoded corner case, comment me out
    xs.Fit.perform()
    xs.Plot(comdict['plottype'])

#want dict with a "blank" key, all sub entries added to blank. Also need a name entry (matches key). 
def twotierdictwrite(outfile,diction,basekeys='blank'): #takes a dict made of dicts
    f=open(comdict['outdirect']+'MCMC_'+outfile+'.txt','w')
    global MCMCdat
    for x in MCMCdat:
        for y in x:
            f.write(str(y)+' ')
        f.write('\n')
    f.close()
    with open(outfile, 'w') as f:  # Just use 'w' mode in 3.x, overwrites
        w = csv.DictWriter(f, diction[basekeys].keys())
        w.writeheader() #column headers written hear from template dict entry
        for key in diction:
            if key != 'blank':
                    w.writerow(diction[key]) #write each subdict out as a row in CSV

global MCMCdat
MCMCdat=[]

def domcmc(key):
    #print 'About to write Markov chains to ', specbase+'chain1.fits'
    # Ensure that new chains will burn the first 100 iterations, will
    # have length 1000, and will use the proposal "gaussian fit"
    xs.AllChains.defBurn = 1500
    xs.AllChains.defLength = 15000
    xs.AllChains.defProposal = 'gaussian fit' # 'cauchy fit' # 
    xs.AllChains.defAlgorithm =  'gw' # 'mh' #
    xs.AllChains.defWalkers = 10 # only for gw
    
    # generate Markov chain
    xs.AllChains.clear() # clear the previous chains
    chainfile = key+'_chain.fits'
    print('About to write Markov chains to ', chainfile)
    # remove the file if it exists
    import os
    if os.path.isfile(chainfile) : os.remove(chainfile)
    # generate the chains
    chain1 = xs.Chain(chainfile, rescale=0.5)
    # show chain information
    xs.AllChains.show()
    xs.AllChains.stat('src:6')
    xs.AllChains.stat('src:9')
    #xs.AllChains.stat('src:12')
    xs.AllChains.stat('src:15')
    #xs.AllChains.stat('bkg:1')
    xs.AllChains.stat('bkg:2')
    #xs.AllChains.stat('bkg:3')
    xs.AllChains.stat('bkg:4')
    #xs.AllChains.stat('bkg:5')
    xs.AllChains.stat('bkg:6')
    xs.AllChains.stat('bkg:8')
    #xs.AllChains.stat('bkg:9')
    xs.AllChains.stat('bkg:10')
    xs.AllChains.stat('bkg:12')
    print('Best estimate of parameters:')
    print(xs.AllChains.best())
    global MCMCdat
    MCMCdat.append([key,xs.AllChains.best(),xs.Fit.statistic])
    # find errors on select model parameters
    stat, dof = xs.Fit.statistic, xs.Fit.statistic
    if stat/dof >= 2.0 : print('Chisq/DoF too large to find errors, ', stat/dof)
    else : 
      xs.Fit.error('src:6')
      xs.Fit.error('src:9')   
      xs.Fit.error('src:12')
      xs.Fit.error('src:15')
      xs.Fit.error('bkg:1')
      xs.Fit.error('bkg:2')
      #xs.Fit.error('bkg:3')
      xs.Fit.error('bkg:4')
      xs.Fit.error('bkg:5')
      xs.Fit.error('bkg:6')
      xs.Fit.error('bkg:8')
      xs.Fit.error('bkg:9')
      xs.Fit.error('bkg:10')
      xs.Fit.error('bkg:12')
        
def outdat(tgt): #write out data for spectra to files for plotting after the fact DEPRECATED
    for i in range(xs.AllData.nSpectra): #gets number for data
        px = xs.Plot.x(i+1, 1)
        f=open(comdict['outdirect']+tgt+'_'+str(i)+'_x.txt','w+')
        for x in px:
            f.write(str(x))
            f.write('\n')
        f.close()
        py = xs.Plot.y(i+1, 1)
        f=open(comdict['outdirect']+tgt+'_'+str(i)+'_y.txt','w+')
        for x in py:
            f.write(str(x))
            f.write('\n')
        f.close()
        pyerr = xs.Plot.yErr(i+1, 1)
        f=open(comdict['outdirect']+tgt+'_'+str(i)+'_yerr.txt','w+')
        for x in pyerr:
            f.write(str(x))
            f.write('\n')
        f.close()
        pmodel = xs.Plot.model(i+1, 1)
        f=open(comdict['outdirect']+tgt+'_'+str(i)+'_model.txt','w+')
        for x in pmodel:
            f.write(str(x))
            f.write('\n')
        f.close()

def outs(tgt,fnam): #write out data for spectra to files for plotting after the fact
    for i in range(xs.AllData.nSpectra): #gets number for data
        fnam2=comdict['outdirect']+fnam+'_data_'+str(i+1)+'.csv'
        px = xs.Plot.x(i+1, 1) #this extracts lists for plotting
        py = xs.Plot.y(i+1, 1)
        pyerr = xs.Plot.yErr(i+1, 1)
        pmodel = xs.Plot.model(i+1, 1)
        px.insert(0, 'x')
        py.insert(0, 'y') 
        pyerr.insert(0, 'y_err') 
        pmodel.insert(0, 'model')
        compout=[]
#        for ki in moddict: #addcomp was added in mar 2020 and does not appear in my install. --resolved this issue jan-2021.
            #print(dir(xs.Plot))
            #LN=len(xs.AllModels(i+1, ki).componentNames) #ki is src or bkg, i is dataset 1,2,3 -DEPRECATED
            #print(xs.Plot.add)
            #allnames=xs.AllModels(i+1, ki).componentNames
        for dig in range(addict):
                vlst = xs.Plot.addComp(dig+1, i+1, 1) #finds each component dig for a DPU i
                vlst.insert(0, 'component') #addcomp only functions for additive comps in the primary model it seems. bkg comps need to be handled separately...
                compout.append(vlst)
        with open(fnam2,'w') as result_file: #writes as columns
            wr = csv.writer(result_file, dialect='excel')
            for x in range(len(px)):   #write out as columns   
                ALL=[px[x],py[x],pyerr[x],pmodel[x]]
                for xnx in range(len(compout)):
                    ALL.append(compout[xnx][x])
                wr.writerow(ALL)

        #ALL=[px,py,pyerr,pmodel]
        #with open(fnam2,'w') as result_file: #writes all in 1 go, but as rows, needs list of lists
            #wr = csv.writer(result_file, dialect='excel')
            #wr.writerows(ALL) 
#            
#        for ki in moddict: #addcomp was added in mar 2020 and does not appear in my install. --resolved this issue jan-2021.
#            #print(dir(xs.Plot))
#            #LN=len(xs.AllModels(i+1, ki).componentNames) #ki is src or bkg, i is dataset 1,2,3 -DEPRECATED
#            #print(xs.Plot.add)
#            #print(xs.AllModels(i+1, ki).componentNames)
#            for dig in range(addict[ki]):
#                vlst = xs.Plot.addComp(dig+1, i+1, 1)
#                #print(vlst)

def err():
    #print(dir(xs.AllModels(1, 'src')))
    for ki in moddict: #this will repeat for every model
            N=(xs.AllModels(1,ki).nParameters) #this tells us how many parameters are in the model
            for x in range(N*int(comdict['Ndata'])): #Ndata tells us how many data sets are included, run error on all
                ipt=ki+':'+str(x+1)
                xs.Fit.error(ipt)

def res(targ): #saves results for target for later export
    results[targ]={}
    label=xs.Fit.statMethod+' stat method'
    results[targ][label]=xs.Fit.statistic
    results['blank'][label]=label
    label=xs.Fit.statTest+' stat test'
    results[targ][label]=xs.Fit.testStatistic
    results['blank'][label]=label
    results[targ]['dof']=xs.Fit.dof
    for ki in moddict:
        for N in range(comdict['Ndata']):
            NAME=comdict['datasets']['names'][N]
            mod = xs.AllModels(N+1, ki) 
            for comp in mod.componentNames :
              for param in mod.__getattribute__(comp).parameterNames :
                x = mod.__getattribute__(comp).__getattribute__(param) 
                headr=ki+' '+NAME+' '+comp+' '+param
                results[targ]['name']=targ
                results[targ][headr]=x.values[0]
                results['blank'][headr]=headr
                Uheaderr=headr+' upper error'
                Lheaderr=headr+' lower error'        
                results[targ][Uheaderr]=x.error[0]
                results[targ][Lheaderr]=x.error[1]
                results['blank'][headr]=headr
                results['blank'][Uheaderr]=Uheaderr
                results['blank'][Lheaderr]=Lheaderr

namu=sys.argv[1]
comdict={} #this is used internally for storing values for executing later commands
comdict['specdirect']=''#if no directory provided, use local
comdict['outdirect']=''#if no directory provided, use local
#paradict={} #model parameters live here
setdict={} #settings live here
moddict={}#models live here
results={}
global addict
addict=0 #dict to track additive comps
chrono=str(datetime.now())[0:10]
results['blank']={}
results['blank']['name']='name'
results['blank']['dof']='dof'
setdict['rmf']=[]
setdict['arf']=[]
setdict['PAC']=[]
paradict=parsefile(namu)
for key in paradict:
    if key != '':
        xs.Xset.openLog(comdict['outdirect']+chrono+'_'+key+'_log'+'.txt')
        loaddata(key)
        setsettings()
        domodel()
        setmodel(key)
        fitnshit(key)
        #err()
        #err()
        domcmc(key)
        res(key)
        xs.Xset.closeLog()
        outs(key,chrono+'_'+key)
twotierdictwrite(comdict['outdirect']+chrono+'_results.csv',results)

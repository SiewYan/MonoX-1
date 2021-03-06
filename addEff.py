from ROOT import *
import ROOT as r
import re, array, sys, numpy, os

gROOT.ProcessLine(
    "struct eff_t {\
     Float_t         eff;\
    }" )


def categoryWeight(iCategory,iSetup,isMC):
  weight=1
  if not isMC:
    return weight
  if iCategory == "photon":
    weight*=iSetup["photonSF"]
  if iCategory == "singlemuon":
    weight*=iSetup["muonSF"]
  if iCategory == "dimuon":
    weight*=iSetup["muonSF"]
    weight*=iSetup["muonSF"]
  return weight

def correctNtuple(iFile,iSample,iFileName,iScale):
    lTFile   = r.TFile('recoilfits/Trigger.root')
    lTriggerData    = lTFile.Get('Data')
    lTriggerMC      = lTFile.Get('MC')
    lNtuple  = iFile.Get(iSample)
    addTrigger = False
    if  lNtuple.GetName().find("Zll_di_muon_controlMet") > -1:
      addTrigger = True
    if  lNtuple.GetName().find("Znunu_signalMet") > -1:
      addTrigger = True

    lFile  = r.TFile(iFileName+'Eff','UPDATE')
    lTree = lNtuple.CloneTree(0)
    lTree.SetName (lNtuple.GetName() )
    lTree.SetTitle(lNtuple.GetTitle())
    lEff=eff_t()
    lTree.SetBranchAddress( 'weight',    AddressOf(lEff,"eff"))
    for i0 in range(0,lNtuple.GetEntriesFast()):
        lNtuple.GetEntry(i0)
        lEff.eff      = lNtuple.weight*iScale
        #correct the photon data to have additional SF to match MET turn on
        if addTrigger:
          pMet = lNtuple.metRaw
          pEff = lTriggerData.Eval(pMet)/lTriggerMC.Eval(pMet)
          if pMet > 240: # Above 240 its 1
            pEff = 1.
            lEff.eff     = lEff.eff*pEff
        lTree.Fill()
    lTree.Write()

sys.path.append("configs")
x = __import__(sys.argv[1]) 

for cat_id,cat in enumerate(x.categories):
    lBaseFile  = r.TFile.Open(cat['in_file_name'])
    samples = cat['samples'].keys()
    for sample in samples:
        entry = cat['samples'][sample]
        pScale = categoryWeight(entry[0],cat,entry[2])
        print "Sample :",sample,pScale
        correctNtuple(lBaseFile,sample,cat['in_file_name'],pScale)
        if sample.find('Met') > 0:
            correctNtuple(lBaseFile,sample+'_Up'  ,cat['in_file_name'],pScale)
            correctNtuple(lBaseFile,sample+'_Down',cat['in_file_name'],pScale)
    os.system('cp %s    %s_old' % (cat['in_file_name'],cat['in_file_name']))
    os.system('mv %sEff %s    ' % (cat['in_file_name'],cat['in_file_name']))

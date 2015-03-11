#!/usr/bin/python

import re, string, sys,datetime,os.path 
import serial
import serial.tools.list_ports
from threading import Thread
from pysimplesoap.client import SoapClient

device="40989BA0-EE75-44A5-B4A4-4457FA194856"
passphrase="brown!cow"
# serialdevice="/dev/ttyACM0"
serialdevice="/dev/cu.usbmodem24680241"

def main():
    
    print(list(serial.tools.list_ports.comports()))

    samplestring="\r\n\RING\r\n"
    
    samplestring+="MESG = 110101\r\n"
    samplestring+="DATE = 0126\r\n"
    samplestring+="TIME = 1954\r\n"
    samplestring+="NMBR = 07795276690\r\n"
    # samplestring+="NAME = WITHHELD\r\n"
    
    samplestring+="\r\n\RING\r\n"
    
    serialinit="ATZ\r\n"
    serialinit+="AT+VCID=1\r\n"
    serialinit+="ATS0=0\r\n"
    
    offlinemode=False
    
    print "Caller ID Listener"
    if (offlinemode):
        print "Offline Mode"
        decode(samplestring)
        return

    ser = serial.Serial(serialdevice,1200,timeout=1)
    try:
        if (not ser.isOpen()):
            print "Could Not Open Device "+serialdevice
        else:
            offlinemode=False
    except:
        print "Serial Port Not Found "+serialdevice



    print "Listening On "+serialdevice
    ser.flushInput()
    ser.flushOutput()
    buffer=""
    print "Initalising"

    ser.write(serialinit)
    ser.flush()
    #print serialinit
    while(True):
        response=ser.readline()
        if len(response)==0:
            continue
        d(response)
        buffer+=response
        if decode(buffer):
            buffer=""

def d(instring):
    msg=instring.replace("\r","")
    msg=msg.replace("\n","")
    if len(msg)==0:
        return
    print "Debug - "+msg

# returns true if the buffer needs clearing
def decode(instring):
    firsringpos=instring.find("RING")
    secondringpos=instring.rfind("RING")
            
  
    # we have found some rings
    if (firsringpos==-1 or secondringpos==-1):
        return False
    
    # we have only one ring
    if (firsringpos==secondringpos):
        return False


    workingstring=instring[firsringpos:secondringpos]
    #clear the buffer less than x characters between the two rings
    if (len(workingstring)<20):
        return True

    bits=workingstring.split("\r\n")
    ourmesg=getfield("MESG",bits)

    if (ourmesg==""):
        return True
    #ourdate=getfield("DATE",bits)
    #ourtime=getfield("TIME",bits)

    ournmbr=getfield("NMBR",bits)
    ourname=getfield("NAME",bits)
    if (ournmbr!="" and ourname==""):
        ourname=lookupfriendly(ournmbr)

    # decode the call type
    ourcalltype=ourmesg[4:6]

    friendlycalltype="Call Type ("+ourmesg+")"
    if ourcalltype=="01":
        friendlycalltype="Voice Call"
    if ourcalltype=="02":
        friendlycalltype="Ring Back"
    if ourcalltype=="82":
        friendlycalltype="Message Waiting"

    # decode the date
    ourdatetime=datetime.datetime.now()
        #try:
        #theyear=datetime.datetime.now().year;
        #themonth=int(ourdate[0:2])
        #theday=int(ourdate[2])
        #thehour=int(ourtime[0:2])
        #theminute=int(ourtime[2])
    
#ourdatetime=datetime.datetime(theyear, themonth,theday,thehour,theminute,0)
#   except:
#       d("Strange Date, Date = " +ourdate+" Time = "+ourtime)
#       pass
#       return True


    lineone=""
    if (ourname!=""):
        lineone+=ourname+" "
    if (ournmbr!=""):
        lineone+=ournmbr+" "

    linetwo="["+ourdatetime.strftime("%H:%M %d %b")+"] "
    linetwo+=friendlycalltype
#   print phonedevice
    print lineone
    print linetwo

    client = SoapClient(wsdl="http://binaryrefinery.com/CID/CIDManager.asmx?WSDL")
    response = client.PostCall(passphrase=passphrase,device=device,messagetype=ourmesg, phone_number=ournmbr)
    print response


    return True

# extracts the value from the data 'MESG = 110101'

def getfield(whichfield,bits):
    
    lookfor=whichfield+" = "
    for s in bits:
        if (not s.startswith(lookfor)):
            continue
        return getelement(s)
    return ""

def getelement(instring):
    bits=instring.split(" = ")
    if (len(bits)!=2):
        return ""
    return bits[1].strip()


def lookupfriendly(st):
    
    phonenumber=st.replace(' ','')

    fn="directory.txt"
    found=False;
    entry="";
    if (os.path.exists(fn)):
        f = open(fn, 'r')
        for line in f:
            if (line.startswith(phonenumber+'|')):
                entry=line;
                found=True
                break
    
        f.close()
    if (found):
        # get just the name out
        elements=entry.split('|')
        if (len(elements)>1):
            return elements[1].rstrip()
            
    unnamed="Unnamed"
    f = open(fn, "a")
    f.write(phonenumber+"|"+unnamed+"\n")
    f.close()
    return unnamed

if __name__ == '__main__':
    main() 
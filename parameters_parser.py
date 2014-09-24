import sys
import getopt



class parameters():
    """ configuration parameters storage class."""

    def __init__(self, programName, neededParams, optionalParams):
        """ initialize the parameter class. needeParams/optionalParams are lists
        of couples in the form: 
        "command line option"->[optionName, wantsValue, 
                   defaultValue, usageMessage, type]
        optional parameters should always use False as default value, so they 
        return False on getParam().

        ***Use only one-letter options***
        """

        self.neededParamsNames = {}
        self.optionalParamsNames = {}
        self.neededParams = {}
        self.optionalParams = {}

        self.programName = programName
        
        optionalParams.append(("-h", ["help", False, False, "show this help",
            int]))
        self.setParams(neededParams, optionalParams)

    def setParams(self, neededParams, optionalParams):
        self.parserString = ""
        for p in neededParams:
            self.neededParamsNames[p[0]] = p[1]
            if p[1][1] == True:
                self.parserString += p[0][1]+":"
            else:
                self.parserString += p[0][1]
        for p in optionalParams:
            self.optionalParamsNames[p[0]] = p[1]
            if p[1][1] == True:
                self.parserString += p[0][1]+":"
            else:
                self.parserString += p[0][1]

    def checkNeededParams(self):
        """ check if all needed params have been set """
        for clp,value in self.neededParamsNames.items():
            if value[0] not in self.neededParams:
                print >> sys.stderr, clp+" is a mandatory parameter "
                self.printUsage()
                sys.exit(1)
 
    def checkCorrectness(self):
        """ do some consistence checks here for the configuration parameters """
        self.checkNeededParams()
        if self.getParam("help") == True:
            return False
        return True

    def printUsage(self):
        """ print the usage of the program """
        print >> sys.stderr
        print >> sys.stderr, "usage ", self.programName+":"
        for pname, pvalue in self.neededParamsNames.items():
            print >> sys.stderr, " ", pname, pvalue[3]
        for pname, pvalue in self.optionalParamsNames.items():
            print >> sys.stderr, " [",pname, pvalue[3], "]"

    def getParam(self, paramName):
        """ return a configuration parameter """
        for pname, pvalue in self.neededParamsNames.items():
            if pvalue[0] == paramName:
                if paramName in self.neededParams:
                    return self.neededParams[paramName]
        for pname, pvalue in self.optionalParamsNames.items():
            if pvalue[0] == paramName:
                if paramName in self.neededParams:
                    return self.optionalParams[paramName]
        sys.exit(1)

    def printConf(self):
        """ just print all the configuration for debug """
        print ""
        for pname, pvalue in self.neededParams.items():
            print pname, pvalue
        for pname, pvalue in self.optionalParams.items():
            print pname, pvalue

    def parseArgs(self):
        """ argument parser """
        try:
            opts, args = getopt.getopt(sys.argv[1:], self.parserString)
        except getopt.GetoptError, err:
            print >> sys.stderr,  str(err)
            self.printUsage()
            sys.exit(2)
        for option,v in opts:
            if option == "-h":
                self.printUsage()
                sys.exit(2)
            if option in self.neededParamsNames.keys():
                optionValue = self.neededParamsNames[option]
                if optionValue[1] == True:
                    self.neededParams[optionValue[0]] = optionValue[4](v)
                else:
                    self.neededParams[optionValue[0]] = True
            elif option in self.optionalParamsNames.keys():
                optionValue = self.optionalParamsNames[option]
                if optionValue[1] == True:
                    self.optionalParams[optionValue[0]] = optionValue[4](v)
                else:
                    self.optionalParams[optionValue[0]] = True
            else:
                assert False, "unhandled option"
    



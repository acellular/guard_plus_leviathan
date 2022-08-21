#The agricultural returns via paradigm rules and soil depletion
class Agriculture:

    def __init__(self, community):
        self.community = community
        # local depletion array equates to each land-use type in paradigm "rules" array
        self.depletion = [0,0,0,0,0,0,0,0,0,0] 
        self.yields = 0
        self.yields_prev = 0
        self.workrate = .5
        
        
    #find the agricultural returns of this community
    def Run(self):
        
        self.yields_prev = self.yields
        self.yields = 0
        
        #NEW 0.11--LATITUDE SPREAD
        lat_modify = (1-(((abs(self.community.position[1]-self.community.paradigm.latitude))
            /self.community.paradigm.maxlat)*self.community.params.lat_mod))*self.community.params.mult
        
        #calculate yields and depletion for each section of community (in array)
        #TODO--replace with matrix calculation via numpy?
        if self.community.paradigm is not None:
            for i in range(len(self.community.paradigm.yield_rules)):
                self.yields += ((self.community.paradigm.yield_rules[i] * self.workrate)
                    - self.depletion[i]) * lat_modify
                self.depletion[i] += self.community.paradigm.depletion_rules[i] * self.workrate
                #bounds
                if self.depletion[i] > 1:
                    self.depletion[i] = 1
                elif self.depletion[i] < 0:
                    self.depletion[i] = 0
        else:
            print("SKIPPED NONE PARA IN AGRI")
__author__ = 'Rahul Manghwani'
__date__ = 'November 27, 2014'

import os
import csv
import math
import heapq
import time
import datetime
import operator
from hours import Hours
from toy import Toy
from elf import Elf

class Santas_lab(object):
    def __init__(self, NUM_ELVES, toy_file, soln_file):
        self.hrs = Hours()
        self.NUM_ELVES            = NUM_ELVES;
        self.LOW_PRODUCTIVE_ELVES = 10;
        self.no_of_days           = 0;  #No of days uptil which toys arrive
        #Toys sorted based on arrival time
        self.toys      = self.read(toy_file)
        #Elves(Divide the elf's into general purpose pool and low-productivity pool)
        self.general_purpose_elves = []
        self.low_productive_elves  = [] #They will do the long tasks
        
        self.ref_time              = datetime.datetime(2014, 1, 1, 0, 0)
        #Big job threasold
        self.big_job_threshold     = 20000
        self.round_robin_threshold = 100
        
        for i in range(0, (self.NUM_ELVES - self.LOW_PRODUCTIVE_ELVES)):
            elf = Elf(i)
            self.general_purpose_elves.append(elf)
            
        for i in range(0, self.LOW_PRODUCTIVE_ELVES):
            elf = Elf(i)
            self.low_productive_elves.append(elf)
            
        #Unassigned toys -- Toys which have arrived but not assigned yet
        self.unassigned_toys = [];
        
        self.output = open(soln_file, "w")
        self.output.write("ToyId,ElfId,StartTime,Duration" + "\n")
        
    def read(self, toy_file):
        toys = []
        with open(toy_file, 'rb') as f:
            toysfile = csv.reader(f)
            toysfile.next()  # header row
            
            for row in toysfile:
                current_toy = Toy(row[0], row[1], row[2])
                if int((current_toy.arrival_minute) / (24.0 * 60.0)) > self.no_of_days:
                    self.no_of_days = int((current_toy.arrival_minute) / (24.0 * 60.0));
                toys.append(current_toy)
                
        #Sort the Toy object based on arrival minute
        return sorted(toys, key=lambda x : x.arrival_minute)
    
    def assign_elf_to_toy(self,input_time, current_elf, current_toy):
        start_time = self.hrs.next_sanctioned_minute(input_time)  # double checks that work starts during sanctioned work hours
        duration = int(math.ceil(current_toy.duration / current_elf.rating))
        sanctioned, unsanctioned = self.hrs.get_sanctioned_breakdown(start_time, duration)
        if unsanctioned == 0:
            return self.hrs.next_sanctioned_minute(start_time + duration), duration
        else:
            return self.hrs.apply_resting_period(start_time + duration, unsanctioned), duration
        
    
    def allocate(self):
        current_toy_index = 0; 
        for day in range(1, self.no_of_days+1):
            
            if day % 10 == 0:
                print("Working on day : " + str(day))
            
            
            #Get all the toys which have arrived before today and haven't been assigned
            day_to_minute  = day * 24.0 * 60.0;
            candidate_toys = [];
            while current_toy_index < len(self.toys) and self.toys[current_toy_index].arrival_minute <= day_to_minute:
                candidate_toys.append(self.toys[current_toy_index])
                current_toy_index += 1;
            #Get all the unassigned toys
            for u_t in self.unassigned_toys:
                candidate_toys.append(u_t)
            
            #Empty the unassinged toys
            del self.unassigned_toys[:];
            
            #Very big jobs -- assign to low productive workers
            big_jobs = [x for x in candidate_toys if x.duration >= self.big_job_threshold]
            for current_toy in big_jobs:
                for low_prod_elves in self.low_productive_elves:
                    if current_toy.arrival_minute > low_prod_elves.next_available_time:
                        low_prod_elves.next_available_time, work_duration = self.assign_elf_to_toy(current_toy.arrival_minute, low_prod_elves, current_toy)
                        low_prod_elves.update_elf(self.hrs, current_toy, current_toy.arrival_minute, work_duration)
                    else:
                        #Put it back in unassigned toys
                        self.unassigned_toys.append(current_toy)
                        
                        
            candidate_toys = [x for x in candidate_toys if x.duration < self.big_job_threshold]
            #Normal jobs
            if day <= self.round_robin_threshold:
                #Find the next available elf from beginning of the queue
                #Round robin
                for current_toy in candidate_toys:
                    current_elf = None;
                    for i in range(0, len(self.general_purpose_elves)):
                        if current_toy.arrival_minute > self.general_purpose_elves[i].next_available_time:
                            current_elf = self.general_purpose_elves[i];
                            current_elf.next_available_time, work_duration = self.assign_elf_to_toy(current_toy.arrival_minute, current_elf, current_toy)
                            current_elf.update_elf(self.hrs, current_toy, current_toy.arrival_minute, work_duration);
                            
                            # write to file in correct format
                            tt = self.ref_time + datetime.timedelta(seconds=60*current_toy.arrival_minute)
                            time_string = " ".join([str(tt.year), str(tt.month), str(tt.day), str(tt.hour), str(tt.minute)])
                            self.output.write(str(current_toy.id) + "," + str(current_elf.id) + "," + str(time_string) + "," + str(work_duration) + "\n" )
                            
                            #Remove the elf 
                            del self.general_purpose_elves[i];
                            #Put it at the back of the queue
                            self.general_purpose_elves.append(current_elf)
                            break;
                    if current_elf == None:
                        self.unassigned_toys.append(current_toy)
            
            else:
                #Sort the candidates based on duration in descending order
                candidate_toys = sorted(candidate_toys, key=lambda x : x.duration, reverse=True)
                print("No of candidate toys " +str(len(candidate_toys)))
                #Pick the elf with the largest productivity
                for current_toy in candidate_toys:
                    current_elf = None;
                    max_productivity = -1.0;
                    current_elf_index = 0;
                    for i in range(0, len(self.general_purpose_elves)):
                        if current_toy.arrival_minute > self.general_purpose_elves[i].next_available_time:
                            if self.general_purpose_elves[i].rating > max_productivity:
                                max_productivity  = self.general_purpose_elves[i].rating;
                                current_elf       = self.general_purpose_elves[i];
                                current_elf_index = i;
                                
                    if current_elf == None:
                        self.unassigned_toys.append(current_toy)
                    else:
                        current_elf.next_available_time, work_duration = self.assign_elf_to_toy(current_toy.arrival_minute, current_elf, current_toy);
                        current_elf.update_elf(self.hrs, current_toy, current_toy.arrival_minute, work_duration);
                        self.general_purpose_elves[current_elf_index] = current_elf;
                        
                        # write to file in correct format
                        tt = self.ref_time + datetime.timedelta(seconds=60*current_toy.arrival_minute)
                        time_string = " ".join([str(tt.year), str(tt.month), str(tt.day), str(tt.hour), str(tt.minute)])
                        self.output.write(str(current_toy.id) + "," + str(current_elf.id) + "," + str(time_string) + "," + str(work_duration) + "\n" )

                        
        self.output.close();
                                    
            

# ======================================================================= #
# === MAIN === #

if __name__ == '__main__':

    start = time.time()

    NUM_ELVES = 900;
    toy_file  = os.path.join(os.getcwd(), 'data/toys_rev2_.csv');
    soln_file = os.path.join(os.getcwd(), 'data/sampleSubmission_rev2.csv')
    santa     = Santas_lab(NUM_ELVES, toy_file, soln_file)
    santa.allocate();
    print 'total runtime = {0}'.format(time.time() - start)
    
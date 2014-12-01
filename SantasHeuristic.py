__author__ = 'Rahul'
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
import numpy as np;

class Santas_lab(object):
    def __init__(self, NUM_ELVES, toy_file, soln_file):
        self.hrs = Hours()
        self.NUM_ELVES                = NUM_ELVES;
        self.LOW_PRODUCTIVE_ELVES     = 10;
        self.ref_time                 = datetime.datetime(2014, 1, 1, 0, 0)
        self.big_job_threshold        = 20000 #Big job threasold
        self.preRampUpPhase_threshold = 100

        #Toys sorted based on arrival time
        self.toys                     = self.read(toy_file)
        self.no_of_days               = int((self.toys[-1].arrival_minute)  / (24.0 * 60.0));  #No of days uptil which toys arrive

        #Elves(Divide the elf's into general purpose pool and low-productivity pool)
        self.general_purpose_elves    = dict()
        self.low_productive_elves     = dict() #They will do the long tasks

        for i in range(0, (self.NUM_ELVES - self.LOW_PRODUCTIVE_ELVES)):
            elf = Elf(i)
            self.general_purpose_elves[elf.id] = elf
            
        for i in range(0, self.LOW_PRODUCTIVE_ELVES):
            elf = Elf(i)
            self.low_productive_elves[elf.id]  = elf;
            
        self.output = open(soln_file, "w")
        self.output.write("ToyId,ElfId,StartTime,Duration" + "\n")
        self.temp_output = [];
        
    def read(self, toy_file):
        toys = []
        with open(toy_file, 'rb') as f:
            toysfile = csv.reader(f)
            toysfile.next()  # header row
            
            for row in toysfile:
                current_toy = Toy(row[0], row[1], row[2])
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
        


    def allocate_jobs(self, jobs, elves, big_or_nonbig):

        if big_or_nonbig == "big":
            #Randomly permute
            np.random.shuffle(jobs)
            np.random.shuffle(elves)


        i = 0;
        j = 0;
        completed_toys = [];

        while i < len(jobs) and j < len(elves):

            if big_or_nonbig == "big":
                self.low_productive_elves[elves[j].id].next_available_time, work_duration = self.assign_elf_to_toy(jobs[i].arrival_minute, self.low_productive_elves[elves[j].id], jobs[i])
                self.low_productive_elves[elves[j].id].update_elf(self.hrs, jobs[i], jobs[i].arrival_minute, work_duration)
            else:
                self.general_purpose_elves[elves[j].id].next_available_time, work_duration = self.assign_elf_to_toy(jobs[i].arrival_minute, self.general_purpose_elves[elves[j].id], jobs[i])
                self.general_purpose_elves[elves[j].id].update_elf(self.hrs, jobs[i], jobs[i].arrival_minute, work_duration)



            # write to file in correct format
            tt = self.ref_time + datetime.timedelta(seconds=60*jobs[i].arrival_minute)
            time_string = " ".join([str(tt.year), str(tt.month), str(tt.day), str(tt.hour), str(tt.minute)])
            self.temp_output.append( ( str(jobs[i].id) , str(elves[j].id), str(time_string), str(work_duration) ) );

            #Flushing non periodically to reduce the IO
            if len(self.temp_output) == 500000:
                #Flush
                for dp in self.temp_output:
                    self.output.write(dp[0] + "," + dp[1] + "," + dp[2] + "," + dp[3] + "\n");
                del self.temp_output[:];

            #Mark as completed
            completed_toys.append(jobs[i].id)

            i = i + 1;
            j = j + 1;


        return completed_toys;




    def allocate_preRampUpPhase(self, candidate_toys, candidate_gp_elves, candidate_lp_elves):
        big_jobs               = [candidate_toys[id] for id in candidate_toys.keys() if candidate_toys[id].duration >= self.big_job_threshold]
        non_big_jobs           = [candidate_toys[id] for id in candidate_toys.keys() if candidate_toys[id].duration <  self.big_job_threshold]

        #Big jobs
        completed_big_jobs     = self.allocate_jobs(big_jobs, candidate_lp_elves, "big")

        #For Non Big Jobs - Greedily pick the elf with the lowest rating and assign it to the highest duration toy
        #Sort the elf based on their rating in asceding order
        #Sort the toys based on their duration in descending order

        candidate_gp_elves     = sorted(candidate_gp_elves, key=lambda x : x.rating)
        non_big_jobs           = sorted(non_big_jobs, key=lambda x : x.duration, reverse=True)
        completed_non_big_jobs = self.allocate_jobs(non_big_jobs, candidate_gp_elves, "nonbig")

        return (completed_big_jobs + completed_non_big_jobs)


    def allocate_RampUpPhase(self, candidate_toys, candidate_gp_elves, mode, candidate_lp_elves=None):
        if mode == 1:
            big_jobs               = [candidate_toys[id] for id in candidate_toys.keys() if candidate_toys[id].duration >= self.big_job_threshold]
            non_big_jobs           = [candidate_toys[id] for id in candidate_toys.keys() if candidate_toys[id].duration <  self.big_job_threshold]

            #Big jobs
            completed_big_jobs     = self.allocate_jobs(big_jobs, candidate_lp_elves, "big")
            #For Non Big Jobs - Greedily pick the highest rating elf for the highest duration toy
            candidate_gp_elves     = sorted(candidate_gp_elves, key=lambda x : x.rating, reverse=True)
            non_big_jobs           = sorted(non_big_jobs, key=lambda x : x.duration, reverse=True)
            completed_non_big_jobs = self.allocate_jobs(non_big_jobs, candidate_gp_elves, "nonbig")

            return (completed_big_jobs + completed_non_big_jobs)
        else:
            candidate_toys         = [candidate_toys[id] for id in candidate_toys.keys()]
            candidate_gp_elves     = sorted(candidate_gp_elves, key=lambda x : x.rating, reverse=True)
            candidate_toys         = sorted(candidate_toys, key=lambda x : x.duration, reverse=True)
            completed_jobs         = self.allocate_jobs(candidate_toys, candidate_gp_elves, "nonbig")

            return  completed_jobs




    def allocate(self):
        current_toy_index   = 0;
        unassigned_old_toys = dict() #Toys which have already arrived but not assigned

        for day in range(0, self.no_of_days+1):
            
            #Get all the toys which have arrived before today and haven't been assigned
            day_to_minute  = day * 24 * 60;

            for minute in range(day_to_minute+self.hrs.day_start, day_to_minute+self.hrs.day_end):
                #Find out all the elves which are available
                candidate_gp_elves = [self.general_purpose_elves[elf_id] for elf_id in self.general_purpose_elves.keys() if self.general_purpose_elves[elf_id].next_available_time <= minute];
                candidate_lp_elves = [self.low_productive_elves[elf_id]  for elf_id in self.low_productive_elves.keys()  if self.low_productive_elves[elf_id].next_available_time <= minute];

                if day % 10 == 0 and minute == (day_to_minute+self.hrs.day_start):
                    print("Working on day : " + str(day) + " Unassigned Toys : " + str(len(unassigned_old_toys.keys())) + " GP Elves : " +str(len(candidate_gp_elves)) + " LP Elves : " + str(len(candidate_lp_elves)))


                #Get list of new toys which have arrived uptil this minute
                new_toys = dict()
                while current_toy_index < len(self.toys) and self.toys[current_toy_index].arrival_minute <= minute:
                    new_toys[self.toys[current_toy_index].id] = self.toys[current_toy_index]
                    current_toy_index += 1;


                candidate_toys  = dict(unassigned_old_toys, **new_toys)

                #Call the desired allocation strategy based on the phase
                if day <= self.preRampUpPhase_threshold:
                    completed_job_ids  = self.allocate_preRampUpPhase(candidate_toys, candidate_gp_elves, candidate_lp_elves);
                else:
                    completed_job_ids  = self.allocate_RampUpPhase(candidate_toys, candidate_gp_elves, 1, candidate_lp_elves);


                #Update the dict
                for id in completed_job_ids:
                    del candidate_toys[id]

                #Reassign
                unassigned_old_toys = candidate_toys;


        #Add any remaining toys
        while current_toy_index < len(self.toys):
            unassigned_old_toys[self.toys[current_toy_index].id] = self.toys[current_toy_index]
            current_toy_index += 1;

        #If toys remaining beyond the last day
        while unassigned_old_toys:

            day_to_minute  = day * 24 * 60;
            for minute in range(day_to_minute+self.hrs.day_start, day_to_minute+self.hrs.day_end):


                if unassigned_old_toys:
                   #Use all the general purpose elves
                   candidate_gp_elves = [self.general_purpose_elves[elf_id] for elf_id in self.general_purpose_elves.keys() if self.general_purpose_elves[elf_id].next_available_time <= minute];
                   completed_job_ids  = self.allocate_RampUpPhase(unassigned_old_toys, candidate_gp_elves, 0, None);

                   if day % 10 == 0 and minute == (day_to_minute+self.hrs.day_start):
                       print("Working on day : " + str(day) + " Unassigned Toys : " + str(len(unassigned_old_toys.keys())) + " GP Elves : " +str(len(candidate_gp_elves)))

                   #Update the dict
                   for id in completed_job_ids:
                       del unassigned_old_toys[id]

                else:
                    break;
            #Next day
            day = day + 1;

        #Flush the remaining
        for dp in self.temp_output:
            self.output.write(dp[0] + "," + dp[1] + "," + dp[2] + "," + dp[3] + "\n");

        print("Working on day : " + str(day) + " Remaining Toys : " + str(len(unassigned_old_toys.keys())))
        #Close the file
        self.output.close();
                                    
            

# ======================================================================= #
# === MAIN === #

if __name__ == '__main__':

    start = time.time()

    NUM_ELVES = 900;
    toy_file  = os.path.join(os.getcwd(), 'data/toys_rev2.csv');
    soln_file = os.path.join(os.getcwd(), 'data/sampleSubmission_rev2.csv')
    santa     = Santas_lab(NUM_ELVES, toy_file, soln_file)
    santa.allocate();
    print 'total runtime = {0}'.format(time.time() - start)
    

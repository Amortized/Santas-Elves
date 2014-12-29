__author__ = 'Rahul'
__date__ = 'Dec 21, 2014'

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
from random import shuffle;
from random import randint;
import random;
import pickle;
import sys;
import copy;
import time;
from multiprocessing import Pool;

class Santas_lab(object):
    def __init__(self, NUM_ELVES, toy_file):
        #Output file
        self.hrs                      = Hours()
        self.NUM_ELVES                = NUM_ELVES;
        self.ref_time                 = datetime.datetime(2014, 1, 1, 0, 0);
        self.toy_baskets              = dict();
        self.max_duration_log         = 11.0;  #Predetermined from analysis
        self.elves                    = dict(); #elf_id -> (elf Object, list of allocated toys, optimimum toy workflow)
        self.boost_productive_th      = 24; #All jobs with hr duration less than this qualify as boosters

        self.create_toy_baskets(toy_file)

        #Every elf maintains list of toys which it has to optically work on
        for i in xrange(1, NUM_ELVES+1):
            elf = Elf(i);
            self.elves[elf.id]  = (elf, [], []);



    def create_toy_baskets(self, toy_file):
        '''
        :Builds toy_baskets where each basket is granularized based on log(duration)
        :return : Final structure has the ids of the toys belonging to that duration bucket
        '''
        #Create baskets of toys where the granularity of log(duration) = 0.01
        self.toy_baskets = dict();
        i = 1;
        duration_log_granularity = 0.0005;
        while i <= int(self.max_duration_log/duration_log_granularity):
            self.toy_baskets[i] = [] # A list of toys
            i += 1;

        i = 0;
        with open(toy_file, 'rb') as f:
            toysfile = csv.reader(f)
            toysfile.next()  # header row

            for row in toysfile:
              i = i + 1;
              if i % 10000 == 0:
                  print("Reading # " + str(i))
              current_toy       = ( int(row[0]), float(row[2]) );
              #Find the right bucket no
              bucket                   = 1 + int(round(math.log(current_toy[1]), 4) / duration_log_granularity); #Rounded to log_granularity decimal places
              self.toy_baskets[bucket].append(current_toy);




    def allocate_baskets_to_elf(self):
        '''
        :return: allocates toys from various baskets to various elves
        '''
        #Initialize the hour map maintained by each elf

        for bucket in self.toy_baskets:
            toys  = self.toy_baskets[bucket]
            shuffle(toys); #Shuffle toys
            toys_per_elf = int(len(toys) / self.NUM_ELVES);

            current_elf_id = 1;
            for i in range(0, (toys_per_elf*self.NUM_ELVES)):
                duration_hr = int(toys[i][1]/60.0);
                if duration_hr <= self.boost_productive_th:
                    self.elves[current_elf_id][1].append((  toys[i][0]  , toys[i][1] ))  
                else:
                    self.elves[current_elf_id][2].append((  toys[i][0]  , toys[i][1] ))  

                current_elf_id += 1;
                if current_elf_id > self.NUM_ELVES:
                    current_elf_id = 1;

            #For remaining toys, randomly pick an elf and assign
            for i in range((toys_per_elf*self.NUM_ELVES), len(toys)):
                random_toy = randint(1, self.NUM_ELVES);

                duration_hr = int(toys[i][1]/60.0);
                if duration_hr <= self.boost_productive_th:
                    self.elves[random_toy][1].append((  toys[i][0]  , toys[i][1] ))  
                else:
                    self.elves[random_toy][2].append((  toys[i][0]  , toys[i][1] ))  




def breakDownWork(input_time, current_elf, toy_duration, hrs):
    """

    :param input_time: Datetime object
    :param current_elf: Elf Object
    :param toy_duration: Duration of Toy
    :param hrs: Hrs Object
    :return:
    """
    start_time = hrs.next_sanctioned_minute(input_time)  # double checks that work starts during sanctioned work hours
    duration = int(math.ceil(toy_duration / current_elf.rating))
    sanctioned, unsanctioned = hrs.get_sanctioned_breakdown(start_time, duration)

    return sanctioned, unsanctioned;


def assign_elf_to_toy(input_time, current_elf, toy_duration, hrs):
    """ Given a toy, assigns the next elf to the toy. Computes the elf's updated rating,
        applies the rest period (if any), and sets the next available time.
        :param input_time: list of tuples (next_available_time, elf)
        :param current_elf: elf object
        :param current_toy: toy object
        :param hrs: hours object
        :return: list of elves in order of next available
    """
    start_time = hrs.next_sanctioned_minute(input_time)  # double checks that work starts during sanctioned work hours
    duration = int(math.ceil(toy_duration / current_elf.rating))
    sanctioned, unsanctioned = hrs.get_sanctioned_breakdown(start_time, duration)

    if unsanctioned == 0:
        return hrs.next_sanctioned_minute(start_time + duration), duration
    else:
        return hrs.apply_resting_period(start_time + duration, unsanctioned), duration

def play_elf(output, elf_object, toy_id, toy_duration, work_start_time=None):
    """

    :param elf_id:  Elf id
    :param toy_id:  Toy_Id
    :param work_start_time: Minute since Jan, 2014
    :return:
    """

    hrs          = Hours();
    ref_time     = datetime.datetime(2014, 1, 1, 0, 0);

    if work_start_time == None:
           work_start_time = elf_object.next_available_time;


    elf_object.next_available_time, work_duration = \
        assign_elf_to_toy(work_start_time, elf_object, toy_duration, hrs);
    elf_object.update_elf(hrs, Toy(toy_id, '2014 01 01 01 01' ,toy_duration), work_start_time, work_duration); #Every toy has default arrival time(irrelevant)

 
    tt = ref_time + datetime.timedelta(seconds=60*work_start_time)
    time_string = " ".join([str(tt.year), str(tt.month), str(tt.day), str(tt.hour), str(tt.minute)])

    output.append((toy_id, time_string, work_duration, work_start_time)); #work_start_time will be used to print in sorted order

    return tt.year;


def powerRequiredEstimation(big_jobs, hrs):
    """

    :param big_jobs:  List of Big Jobs
    :param hrs:  Hrs Object
    :return:
    """
    power_per_unit   = [];
    #Dummy Elf
    dummy_elf        = Elf(0);
    dummy_elf.rating = 0.25;


    for job in big_jobs:
      #Play the toys at min rating at 9:00 on start of the day
      sanctioned, unsanctioned = breakDownWork(dummy_elf.next_available_time, dummy_elf, job[1], hrs);
      power_per_unit.append(unsanctioned);

    total_power    = sum(power_per_unit);
    power_per_unit = [i/float(total_power) for i in power_per_unit];

    return power_per_unit;

def powerAvailableEstimation(big_jobs, boosters, hrs):
    '''
      Assume a rating of 0.25, total gain in ratings that can be obtained for different jobs 
    '''
   
    total_gain              = 0.0;
    ratio_big_jobs_boosters = len(big_jobs) / float( len(big_jobs)  + len(boosters) );

    #Dummy Elf
    dummy_elf               = Elf(0);
    dummy_elf.rating        = 0.25;

    work_start_time         = 540; #All boosters are played with maximum sanctioned time

    shuffle(boosters);

    for job in boosters:
        
        #Assume the work starts at 9:00 on start of the day
        next_available_time, work_duration = \
           assign_elf_to_toy(work_start_time, dummy_elf, job[1], hrs);

        dummy_elf.update_elf(hrs, Toy(0, '2014 01 01 01 01' ,job[1]), work_start_time, work_duration); #Every toy has default arrival time(irrelevant)

        #Flip a coin and play a big job based on above probability
        if random.random() < ratio_big_jobs_boosters:
            #Big Job Played - Measure the gain
            if dummy_elf.rating > 0.25:
               total_gain += (dummy_elf.rating - 0.25);
            #Reinitialize the dummy_elf
            dummy_elf               = Elf(0);
            dummy_elf.rating        = 0.25;


    return total_gain;


def generateOptimumRatings(big_jobs, boosters, hrs, alpha):
    '''
       Generates optimimum ratings for the big_jobs to be operated on
    '''
    
    #Generate desired ratings
    power_reqd_per_unit  = powerRequiredEstimation(big_jobs, hrs);
    #Total Gain Estimation - Repeat the random process x=10 times
    total_gain           = sum([powerAvailableEstimation(big_jobs, boosters, hrs) for x in range(0, 10)]) / float(10.0);
    
    ratings              = [ 0.25 + alpha + (power_reqd_per_unit[i] * total_gain) for i in range(0, len(power_reqd_per_unit))];

    return ratings;


def optimize(elf_object, boosters, big_jobs):
    """
    :param elf_object:  Elf Object
    :param boosters:    List of (Toy_Id, Duration)
    :param big_jobs:    List of (Toy_Id, Duration)
    :return:
    """


    output                      = [];
    file_handler                = open(  ("data/submission_" + str(elf_object.id) + ".csv"), "wb"  );
    hrs                         = Hours();
    last_job_completed_year     = 0;

    alpha                       = 0.00;           #BumpupParameter
    min_desired_rating          = (0.25 + alpha); #Base Min Rate + Bumpup Parameter

    total_no_of_toys            = len(boosters) + len(big_jobs);
    #Sort the big jobs in descending order of duration
    big_jobs.sort(key=operator.itemgetter(1),reverse=True);
    #Sort the boosters in ascending order of duration
    boosters.sort(key=operator.itemgetter(1));

    no_completed_toys = 0;

    #Does not work as well
    #ratings           = generateOptimumRatings(big_jobs, boosters, hrs, alpha); 



    while no_completed_toys < total_no_of_toys:
        
        
        if len(big_jobs) > 0:
            print("Optimizing : Elf " + str(elf_object.id) + " Rating : " + str(elf_object.rating) + " Completed : " + str(no_completed_toys) + " Boosters : " + str(len(boosters)) + " Big Jobs : " + str(len(big_jobs)) + " Last Completed Year : " +str(last_job_completed_year) + " Duration(hr) : " +str( int(big_jobs[0][1]/60.0) ));

            #Play the first toy in the queue on the following day
            work_start_time = hrs.day_start  + int(hrs.minutes_in_24h * math.ceil(elf_object.next_available_time / float(hrs.minutes_in_24h)));
            completion_yr   = play_elf(output, elf_object, big_jobs[0][0], big_jobs[0][1], work_start_time);

            #completion_yr = play_elf(output, elf_object, big_jobs[0][0], big_jobs[0][1]);
            if completion_yr > last_job_completed_year:
                last_job_completed_year = completion_yr;
            
            #Delete this toy
            del big_jobs[0];

            #Change the desired rating based on hr duration of upcoming job
            if len(big_jobs) > 0 and int(big_jobs[0][1]/60.0) >= 350:
               min_desired_rating = 0.34;
            elif len(big_jobs) > 0 and int(big_jobs[0][1]/60.0) >= 300 and int(big_jobs[0][1]/60.0) < 350:
               min_desired_rating = 0.32; 
            elif len(big_jobs) > 0 and int(big_jobs[0][1]/60.0) >= 250 and int(big_jobs[0][1]/60.0) < 300:
               min_desired_rating = 0.31;
            elif len(big_jobs) > 0 and int(big_jobs[0][1]/60.0) >= 200 and int(big_jobs[0][1]/60.0) < 250:
               min_desired_rating = 0.30;   
            else:
               min_desired_rating = 0.28; 


            no_completed_toys += 1;


        print("**Seeking a rating : " + str(min_desired_rating));


        #Iterate through the boosters and increase the productivity
        while ( round(elf_object.rating,2) + 0.01 < round(min_desired_rating,2) or len(big_jobs) == 0) and no_completed_toys < total_no_of_toys:
            print("***Optimizing : Elf " + str(elf_object.id) + " Rating : " + str(elf_object.rating) + " Completed : " + str(no_completed_toys) + " Boosters : " + str(len(boosters)) + " Big Jobs : " + str(len(big_jobs)))

            if len(boosters) == 0:
                break;

            #Generate a random no
            random_toy = randint(0, len(boosters)-1);

            #Play the one with no unsanctioned time
            sanctioned, unsanctioned = breakDownWork(elf_object.next_available_time, elf_object, boosters[random_toy][1], hrs);

            if unsanctioned == 0:
                completion_yr = play_elf(output, elf_object, boosters[random_toy][0], boosters[random_toy][1]);
                #Remove the toy played
                del boosters[random_toy];                
            else:
                #Play the first toy as it has the least amount of unsanctioned time
                #Set the next available time to next day, 9:00 am
                work_start_time = hrs.day_start  + int(hrs.minutes_in_24h * math.ceil(elf_object.next_available_time / float(hrs.minutes_in_24h)));
                completion_yr   = play_elf(output, elf_object, boosters[0][0], boosters[0][1], work_start_time);
                
                del boosters[0];

            if completion_yr > last_job_completed_year:
                last_job_completed_year = completion_yr;
            no_completed_toys += 1;                

            
            


    #Sort the output based on work_start_time
    output.sort(key=operator.itemgetter(3));


    #Flush the output of this elf to file
    for toy in output:
        file_handler.write( str(toy[0]) + "," + str(elf_object.id) + "," \
                            + str(toy[1]) + "," + str(toy[2]) + "\n");

    file_handler.close();

    return last_job_completed_year;


def optimize_wrapper(args):
    return optimize(*args);

                

# ======================================================================= #
# === MAIN === #

if __name__ == '__main__':
    args  = list(sys.argv[1:]);

    start = time.time();
    NUM_ELVES = 900;
    #Construct workflows for toys and dump them
    toy_file  = os.path.join(os.getcwd(), 'data/toys_rev2.csv');
    santa     = Santas_lab(NUM_ELVES, toy_file);
    santa.allocate_baskets_to_elf();

    #Contruct parameters as a list
    elf_worflows = [ (Elf(i), copy.copy(santa.elves[i][1]), copy.copy(santa.elves[i][2]) ) for i in xrange(1, NUM_ELVES+1) ];

    #Create a Thread pool.
    pool     = Pool();
    results  = pool.map( optimize_wrapper, elf_worflows );

    pool.close();
    pool.join();

    print("Last Job Completed in year : " + str(max(results)));
    print 'total runtime = {0}'.format(time.time() - start);


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

        self.create_toy_baskets(toy_file)

        #Every elf maintains list of toys which it has to optically work on
        for i in xrange(1, NUM_ELVES+1):
            elf = Elf(i);
            self.elves[elf.id]  = (elf, dict(), dict());



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
        for i in xrange(1, self.NUM_ELVES+1):
            for hr in xrange(0, 1000): #No Task is greater than 1000hrs
                self.elves[i][2][hr] = [0, []];

        for bucket in self.toy_baskets:
            toys  = self.toy_baskets[bucket]
            shuffle(toys); #Shuffle toys
            toys_per_elf = int(len(toys) / self.NUM_ELVES);

            current_elf_id = 1;
            for i in range(0, (toys_per_elf*self.NUM_ELVES)):
                self.elves[current_elf_id][1][toys[i][0]] = toys[i][1];
                self.elves[current_elf_id][2][int(toys[i][1]/60.0)][0] += 1;
                self.elves[current_elf_id][2][int(toys[i][1]/60.0)][1].append(toys[i][0])

                current_elf_id += 1;
                if current_elf_id > self.NUM_ELVES:
                    current_elf_id = 1;

            #For remaining toys, randomly pick an elf and assign
            for i in range((toys_per_elf*self.NUM_ELVES), len(toys)):
                random_toy = randint(1, self.NUM_ELVES);
                self.elves[random_toy][1][toys[i][0]] = toys[i][1];
                self.elves[random_toy][2][int(toys[i][1]/60.0)][0] += 1;
                self.elves[random_toy][2][int(toys[i][1]/60.0)][1].append(toys[i][0])




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
    output[toy_id] = (elf_object.id, time_string, work_duration);

    return tt.year;


def optimize(elf_object, toy_duration_map, duration_bucket):


    output                      = dict();
    file_handler                = open(  ("data/submission_" + str(elf_object.id) + ".csv"), "wb"  );
    hrs                         = Hours();
    last_job_completed_year     = 0;

    #Toys less than folling counter are used to boost productivity
    boost_productive_worker = 24;
    #Rating thresold
    rating_thresold = 0.40;
    
    #Job's which require productivity to be maintained at above 0.40
    decrease_productivity_threshold = 150;



    no_completed_toys = 0;
    #Current expensive toy counter
    exp_toy_counter = max(duration_bucket.keys());
    while no_completed_toys < len(toy_duration_map):
        if exp_toy_counter < decrease_productivity_threshold:
           rating_thresold = 0.30; 

        print("Optimizing : Elf " + str(elf_object.id)  + " Completed : " + str(no_completed_toys));
        #Play a expensive toy
        while exp_toy_counter > boost_productive_worker and duration_bucket[exp_toy_counter][0] == 0:
            exp_toy_counter -= 1;

        if exp_toy_counter > boost_productive_worker:
           #Remove the toy
           duration_bucket[exp_toy_counter][0] -= 1;
           for toy_id in duration_bucket[exp_toy_counter][1]:
               if toy_id in output:
                   #Already completed
                   pass;
               else:
                   #Play this elf
                   completion_yr = play_elf(output, elf_object, toy_id, toy_duration_map[toy_id]);
                   if completion_yr > last_job_completed_year:
                       last_job_completed_year = completion_yr;
                   no_completed_toys += 1;
                   break;


        toys = [];
        for k in xrange(0, boost_productive_worker+1):
            for z in duration_bucket[k][1]:
                if z in output:
                    pass;
                else:
                    toys.append(z);

        while (elf_object.rating < rating_thresold or exp_toy_counter <= boost_productive_worker) and no_completed_toys < len(toy_duration_map):
            if len(toys) == 0:
                break;


            shuffle(toys);
            min_unsanctioned_time = sys.maxsize;
            min_toy_id            = None;
            played                = False;

            for toy_id in toys:
                #Play the toy with no unsanctioned time
                sanctioned, unsanctioned = breakDownWork(elf_object.next_available_time, elf_object, toy_duration_map[toy_id], hrs);
                if unsanctioned == 0:
                    completion_yr = play_elf(output, elf_object, toy_id, toy_duration_map[toy_id]);
                    if completion_yr > last_job_completed_year:
                        last_job_completed_year = completion_yr;
                    #Remove the toy
                    toys.remove(toy_id);
                    played = True;
                    no_completed_toys += 1;
                    break;
                elif unsanctioned < min_unsanctioned_time:
                    min_toy_id = toy_id;
                    min_unsanctioned_time = unsanctioned;

            if played == False:
                #Set the next available time to next day, 9:00 am
                work_start_time = hrs.day_start  + int(hrs.minutes_in_24h * math.ceil(elf_object.next_available_time / hrs.minutes_in_24h));
                completion_yr = play_elf(output, elf_object, min_toy_id, toy_duration_map[min_toy_id], work_start_time);
                if completion_yr > last_job_completed_year:
                    last_job_completed_year = completion_yr;
                toys.remove(min_toy_id);
                no_completed_toys += 1;
                print("Optimizing : Elf " + str(elf_object.id)  + " Boosters remaining : " + str(len(toys)));




    #Flush the output of this elf to file
    for toy_id in output:
        file_handler.write( str(toy_id) + "," + str(output[toy_id][0]) + "," \
                            + str(output[toy_id][1]) + "," + str(output[toy_id][2]) + "\n");

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
    elf_worflows = [ (santa.elves[i][0], santa.elves[i][1], santa.elves[i][2]) for i in xrange(1, NUM_ELVES+1) ];

    #Create a Thread pool.
    pool     = Pool();
    results  = pool.map( optimize_wrapper, elf_worflows );

    pool.close();
    pool.join();

    print("Last Job Completed in year : " + str(max(results)));
    print 'total runtime = {0}'.format(time.time() - start);


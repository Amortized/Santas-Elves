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
import sys;
import copy;
import time;
import Queue;

class Santas_lab(object):
    def __init__(self, NUM_ELVES, toy_file):
        self.boost_productive_th      = 24; #All jobs with hr duration less than this qualify as boosters
        self.boosters                 = [];
        self.big_jobs                 = [];

        self.create_toy_baskets(toy_file);




    def create_toy_baskets(self, toy_file):

        i = 0;
        with open(toy_file, 'rb') as f:
            toysfile = csv.reader(f)
            toysfile.next()  # header row

            for row in toysfile:
                i = i + 1;
                if i % 10000 == 0:
                    print("Reading # " + str(i))
                current_toy       = ( int(row[0]), float(row[2]) );
                if int(current_toy[1]/60.0) <= self.boost_productive_th:
                    self.boosters.append(current_toy);
                else:
                    self.big_jobs.append(current_toy);



    def breakDownWork(self, input_time, current_elf, toy_duration, hrs):
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


    def assign_elf_to_toy(self, input_time, current_elf, toy_duration, hrs):
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

    def play_elf(self, output, elf_object, toy_id, toy_duration, work_start_time=None):
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
            self.assign_elf_to_toy(work_start_time, elf_object, toy_duration, hrs);
        elf_object.update_elf(hrs, Toy(toy_id, '2014 01 01 01 01' ,toy_duration), work_start_time, work_duration); #Every toy has default arrival time(irrelevant)


        tt = ref_time + datetime.timedelta(seconds=60*work_start_time)
        time_string = " ".join([str(tt.year), str(tt.month), str(tt.day), str(tt.hour), str(tt.minute)])

        if elf_object.id in output:
            output[elf_object.id].append((toy_id, time_string, work_duration, work_start_time)); #work_start_time will be used to print in sorted order
        else:
            output[elf_object.id] = [(toy_id, time_string, work_duration, work_start_time)];

        return tt.year;




    def optimize(self, NUM_ELVES, boosters, big_jobs):
        """
        :param elf_object:  Elf Object
        :param boosters:    List of (Toy_Id, Duration)
        :param big_jobs:    List of (Toy_Id, Duration)
        :return:
        """




        output                      = dict();

        file_handler                = open(  ("data/finalSubmission1"  + ".csv"), "wb"  );
        hrs                         = Hours();
        last_job_completed_year     = 0;

        min_desired_rating          = 0.32;

        total_no_of_toys            = len(boosters) + len(big_jobs);
        #Sort the big jobs in descending order of duration
        big_jobs.sort(key=operator.itemgetter(1),reverse=True);
        #Sort the boosters in ascending order of duration
        boosters.sort(key=operator.itemgetter(1));

        rating_change_index1 = 0;
        rating_change_index2 = 0;
        for i in range(0, len(big_jobs)):
            if int(big_jobs[i][1]/60.0) <= 300 and int(big_jobs[i][1]/60.0) > 200:
                rating_change_index1 = i;
            if int(big_jobs[i][1]/60.0) <= 200:
                rating_change_index2 = i;

        no_completed_toys           = 0;
        big_job_counter             = 0;


        elves = Queue.Queue();
        for i in xrange(1, NUM_ELVES+1):
            elf                     = Elf(i);
            elves.put(elf);


        while no_completed_toys < total_no_of_toys:
            if no_completed_toys % 10000 == 0:
                print(" Algorithm : Boost_Play , Boosters : " + str(len(boosters)) + " Big Jobs : " + str(len(big_jobs)));


            #print("**Seeking a rating : " + str(min_desired_rating));
            if len(big_jobs) == 0:
                break;

            #Pick an elf
            elf_object = elves.get();


            #Iterate through the boosters and increase the productivity
            no_of_toys_played = 0;
            while ( round(elf_object.rating,3) + 0.002 < round(min_desired_rating,3) ):

                if len(boosters) == 0 or no_of_toys_played > 20:
                    break;

                #Generate a random no
                random_toy = randint(0, len(boosters)-1);

                #Play the one with no unsanctioned time
                sanctioned, unsanctioned = self.breakDownWork(elf_object.next_available_time, elf_object, boosters[random_toy][1], hrs);

                if unsanctioned == 0:
                    completion_yr = self.play_elf(output, elf_object, boosters[random_toy][0], boosters[random_toy][1]);
                    #Remove the toy played
                    del boosters[random_toy];
                else:
                    #Play the first toy as it has the least amount of unsanctioned time
                    #Set the next available time to next day, 9:00 am
                    work_start_time = hrs.day_start  + int(hrs.minutes_in_24h * math.ceil(elf_object.next_available_time / float(hrs.minutes_in_24h)));
                    completion_yr   = self.play_elf(output, elf_object, boosters[0][0], boosters[0][1], work_start_time);

                    del boosters[0];

                if completion_yr > last_job_completed_year:
                    last_job_completed_year = completion_yr;
                no_completed_toys += 1;
                no_of_toys_played += 1;


            if len(big_jobs) > 0:

                if big_job_counter >= rating_change_index1:
                    min_desired_rating = 0.31;

                if big_job_counter >= rating_change_index2:
                    min_desired_rating = 0.29;


                #Play the first toy in the queue on the following day
                work_start_time = hrs.day_start  + int(hrs.minutes_in_24h * math.ceil(elf_object.next_available_time / float(hrs.minutes_in_24h)));
                completion_yr   = self.play_elf(output, elf_object, big_jobs[0][0], big_jobs[0][1], work_start_time);

                #completion_yr = play_elf(output, elf_object, big_jobs[0][0], big_jobs[0][1]);
                if completion_yr > last_job_completed_year:
                    last_job_completed_year = completion_yr;

                #Delete this toy
                del big_jobs[0];

                no_completed_toys += 1;
                big_job_counter   += 1;

            #Put the elf back in
            elves.put(elf_object);

        #Play naively
        myelves = []
        while not elves.empty():
            current_elf = elves.get();
            heapq.heappush(myelves, (current_elf.next_available_time, current_elf));


        if len(boosters) == 0:
            remaining_jobs = big_jobs;
        else:
            remaining_jobs = boosters;


        while len(remaining_jobs) > 0:

            print(" Algorithm : Naive , Boosters : " + str(len(boosters)) + " Big Jobs : " + str(len(remaining_jobs)));

            elf_available_time, current_elf = heapq.heappop(myelves);
            completion_yr   = self.play_elf(output, current_elf, remaining_jobs[0][0], remaining_jobs[0][1]);
            if completion_yr > last_job_completed_year:
                last_job_completed_year = completion_yr;
            # put elf back in heap
            heapq.heappush(myelves, (current_elf.next_available_time, current_elf));
            no_completed_toys += 1;

            print(current_elf.id);

            del remaining_jobs[0];


        for elf_id in output:
            #Sort the output based on work_start_time
            output[elf_id].sort(key=operator.itemgetter(3));
            #Flush the output of this elf to file
            for toy in  output[elf_id]:
                file_handler.write( str(toy[0]) + "," + str(elf_id) + "," \
                                    + str(toy[1]) + "," + str(toy[2]) + "\n");

        file_handler.close();

        return last_job_completed_year;




# ======================================================================= #
# === MAIN === #

if __name__ == '__main__':
    args                    = list(sys.argv[1:]);

    start                   = time.time();
    NUM_ELVES               = 900;
    #Construct workflows for toys and dump them
    toy_file                = os.path.join(os.getcwd(), 'data/toys_rev2.csv');
    santa                   = Santas_lab(NUM_ELVES, toy_file);
    last_job_completed_year = santa.optimize(NUM_ELVES, santa.boosters, santa.big_jobs)

    print(last_job_completed_year)
    print('total runtime = {0}'.format(time.time() - start));


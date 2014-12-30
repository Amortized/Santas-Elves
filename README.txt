Code for Kaggle's 2014 Holiday competition, Helping Santa's Helpers.

This repo includes: (1) elf.py; (2) toy.py; (3) hours.py; (4) SantasHelpers_NaiveSolution.py; (5) SantasHelpers_Evaluation_Metric.py

--Download the data from kaggle 

http://www.kaggle.com/c/helping-santas-helpers/download/toys_rev2.zip

--Save it inside toys : data/toys_rev2.csv

--My improved heuristics are in : SantasHeuristic.py; Santas_Global_Optimizer.py

  --Initial run  python2 SantasHeuristic.py

  --This generates 900 submission files. Combine all the submission files into big file "data/finalSubmission1.csv". Make sure ToyId,ElfId,StartTime, Duration appended to beginning of file.

  --Finally runt the global optimizer on this file : python2 Santas_Global_Optimizer.py. Output is at : data/finalModifiedSubmission1.csv. Upload csv to Kaggle


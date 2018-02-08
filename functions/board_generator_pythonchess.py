import chess
import random
from vectorize import board2vector, vector2string
from call_engine import best_board
import numpy as np
import h5py
import datetime
import time
import glob
import os

'''
This function is designed to generate moves by letting stockfish play against itself.
The input X (boards) starts with a new board and the output Y (nextboards) are generated by the stockfish engine.
The next input is then the same output (Xi+1 = Y).
This way stockfish plays a game untill one of the conditions is met:
-Game over, checkmate
-Insufficient material
-Stalemate
-There is a fivefold repetition
-The maximum of seventyfive moves is achieved (this can be changed by lowering the value of max_moves / 2)

Stockfish is not deterministic and randomness can also be expected due to factors such as multi-threading.
However, to ensure that games have a big variety when generating large datasets, the engine is called with a random search depth, which adds randomness to the games.
It is recommended to keep this value between 5 and 15 to keep a high quality games while keeping decent calculating times on a PC.
'''

#Set this value to True to continue adding to the newest generated database. Set to False to start a new one
continue_database = False
#Set this parameter to either None, "gzip", "gzip", "lzf", "szip", to compress the data with the given algorithm.
#Only holds for new data files.
compression = "gzip"
#Set this to True to visualize the first generated game, which consists of an average of 75 moves
visualise = False
#Set this to True to log a summary of why a self-played game was ended
log_info = True

#Set this to less than 150 to shorten the games further than the default 75 moves.
max_moves = 500

#Set this value to limit the total boards added to database.
max_board_length_database = 2e3

#Configure database
list_of_files = glob.glob('./../data/*.h5')
if continue_database and list_of_files:
    fname = max(list_of_files, key=os.path.getctime)
else:
    fname = './../data/' + datetime.datetime.now().strftime('%Y%m%dT%H%M') + 'boards.h5'
    h5f = h5py.File(fname, 'w')
    dsI = h5f.create_dataset("input_boards", (792,0), maxshape=(792,None), dtype='f', chunks=(792,1000), compression=compression)
    dsO = h5f.create_dataset("output_boards", (792,0), maxshape=(792,None), dtype='f', chunks=(792,1000), compression=compression)

    h5f.close()

#Initialize parameters
start = time.time()
boards = []
nextboards = []
N = 0

while N < max_board_length_database:
    board = chess.Board()
    boards.append(board2vector(board))

    i = 0
    while not i > max_moves \
            and not board.is_game_over() \
            and not board.is_insufficient_material() \
            and not board.is_stalemate() \
            and not board.is_fivefold_repetition() \
            and not board.is_seventyfive_moves():


        i = i + 1
        #use the transformation function before adding it to board
        boardvec = board2vector(best_board(board,search_depth=random.randint(6,12)))
        nextboards.append(boardvec)
        if not i > max_moves \
            and not board.is_game_over() \
            and not board.is_insufficient_material() \
            and not board.is_stalemate() \
            and not board.is_fivefold_repetition() \
            and not board.is_seventyfive_moves():
                boards.append(boardvec)


        if N == 0 and visualise:
            print(board)
            print('---------------')
            print('---Move '+str(i)+'----')
            print('---------------')


    if log_info:
        if  not board.is_insufficient_material() \
            and not board.is_stalemate() \
            and not board.is_fivefold_repetition() \
            and not board.is_seventyfive_moves():
            print('Game ended: Checkmate!')
        elif board.is_insufficient_material():
            print('Game ended: Insufficient Material')
        elif board.is_fivefold_repetition():
            print('Game ended: Fivefold Repetition')
        elif board.is_stalemate():
            print('Game ended: Stalemate')
        elif board.is_seventyfive_moves():
            print('Game ended: Maximum of 75 moves')
        elif i > max_moves:
            print('Game ended: Maximum of '+str(i)+' moves')

    #Save game data to h5py files
    h5f = h5py.File(fname, 'a')

    dsetIn = h5f["input_boards"]
    dsetOut = h5f["output_boards"]

    curlength = dsetIn.shape[1]
    dsetIn.resize(curlength+len(boards), axis=1)
    dsetIn[:,curlength:]=np.transpose(np.array(boards))

    curlength = dsetOut.shape[1]
    dsetOut.resize(curlength+len(nextboards), axis=1)
    dsetOut[:,curlength:]=np.transpose(np.array(nextboards))

    N = dsetIn.shape[1]
    h5f.close()

    boards = []
    nextboards = []
    print("Database now contains " + str(N) + " boards")

end = time.time()
print('Elapsed time {} sec'.format(end-start))



//
// Copyright 2014 Ettus Research
//
// SPDX-License-Identifier: GPL-3.0
//

#ifndef INCLUDED_AD9361_SYNTH_LUT_HPP
#define INCLUDED_AD9361_SYNTH_LUT_HPP


double vco_index[53] = {12605000000.0, 12245000000.0, 11906000000.0, 11588000000.0,
                        11288000000.0, 11007000000.0, 10742000000.0, 10492000000.0,
                        10258000000.0, 10036000000.0, 9827800000.0, 9631100000.0,
                        9445300000.0, 9269800000.0, 9103600000.0, 8946300000.0,
                        8797000000.0, 8655300000.0, 8520600000.0, 8392300000.0,
                        8269900000.0, 8153100000.0, 8041400000.0, 7934400000.0,
                        7831800000.0, 7733200000.0, 7638400000.0, 7547100000.0,
                        7459000000.0, 7374000000.0, 7291900000.0, 7212400000.0,
                        7135500000.0, 7061000000.0, 6988700000.0, 6918600000.0,
                        6850600000.0, 6784600000.0, 6720500000.0, 6658200000.0,
                        6597800000.0, 6539200000.0, 6482300000.0, 6427000000.0,
                        6373400000.0, 6321400000.0, 6270900000.0, 6222000000.0,
                        6174500000.0, 6128400000.0, 6083600000.0, 6040100000.0,
                        5997700000.0};

int synth_cal_lut[53][12] = {   {10, 0, 4, 0, 15, 8, 8, 13, 4, 13, 15, 9},
                                {10, 0, 4, 0, 15, 8, 9, 13, 4, 13, 15, 9},
                                {10, 0, 4, 0, 15, 8, 10, 13, 4, 13, 15, 9},
                                {10, 0, 4, 0, 15, 8, 11, 13, 4, 13, 15, 9},
                                {10, 0, 4, 0, 15, 8, 11, 13, 4, 13, 15, 9},
                                {10, 0, 4, 0, 14, 8, 12, 13, 4, 13, 15, 9},
                                {10, 0, 4, 0, 14, 8, 13, 13, 4, 13, 15, 9},
                                {10, 0, 5, 1, 14, 9, 13, 13, 4, 13, 15, 9},
                                {10, 0, 5, 1, 14, 9, 14, 13, 4, 13, 15, 9},
                                {10, 0, 5, 1, 14, 9, 15, 13, 4, 13, 15, 9},
                                {10, 0, 5, 1, 14, 9, 15, 13, 4, 13, 15, 9},
                                {10, 0, 5, 1, 13, 9, 16, 13, 4, 13, 15, 9},
                                {10, 0, 5, 1, 13, 9, 17, 13, 4, 13, 15, 9},
                                {10, 0, 5, 1, 13, 9, 18, 13, 4, 13, 15, 9},
                                {10, 0, 5, 1, 13, 9, 18, 13, 4, 13, 15, 9},
                                {10, 0, 5, 1, 13, 9, 19, 13, 4, 13, 15, 9},
                                {10, 1, 6, 1, 15, 11, 14, 13, 4, 13, 15, 9},
                                {10, 1, 6, 1, 15, 11, 14, 13, 4, 13, 15, 9},
                                {10, 1, 6, 1, 15, 11, 15, 13, 4, 13, 15, 9},
                                {10, 1, 6, 1, 15, 11, 15, 13, 4, 13, 15, 9},
                                {10, 1, 6, 1, 15, 11, 16, 13, 4, 13, 15, 9},
                                {10, 1, 6, 1, 15, 11, 16, 13, 4, 13, 15, 9},
                                {10, 1, 6, 1, 15, 11, 17, 13, 4, 13, 15, 9},
                                {10, 1, 6, 1, 15, 11, 17, 13, 4, 13, 15, 9},
                                {10, 1, 6, 1, 15, 11, 18, 13, 4, 13, 15, 9},
                                {10, 1, 6, 1, 15, 11, 18, 13, 4, 13, 15, 9},
                                {10, 1, 6, 1, 15, 11, 19, 13, 4, 13, 15, 9},
                                {10, 1, 6, 1, 15, 11, 19, 13, 4, 13, 15, 9},
                                {10, 1, 6, 1, 15, 11, 20, 13, 4, 13, 15, 9},
                                {10, 1, 7, 2, 15, 12, 20, 13, 4, 13, 15, 9},
                                {10, 1, 7, 2, 15, 12, 21, 13, 4, 13, 15, 9},
                                {10, 1, 7, 2, 15, 12, 21, 13, 4, 13, 15, 9},
                                {10, 1, 7, 2, 15, 14, 22, 13, 4, 13, 15, 9},
                                {10, 1, 7, 2, 15, 14, 22, 13, 4, 13, 15, 9},
                                {10, 1, 7, 2, 15, 14, 23, 13, 4, 13, 15, 9},
                                {10, 1, 7, 2, 15, 14, 23, 13, 4, 13, 15, 9},
                                {10, 1, 7, 2, 15, 14, 24, 13, 4, 13, 15, 9},
                                {10, 1, 7, 2, 15, 14, 24, 13, 4, 13, 15, 9},
                                {10, 1, 7, 2, 15, 14, 25, 13, 4, 13, 15, 9},
                                {10, 1, 7, 2, 15, 14, 25, 13, 4, 13, 15, 9},
                                {10, 1, 7, 2, 15, 14, 26, 13, 4, 13, 15, 9},
                                {10, 1, 7, 2, 15, 14, 26, 13, 4, 13, 15, 9},
                                {10, 1, 7, 2, 15, 14, 27, 13, 4, 13, 15, 9},
                                {10, 1, 7, 2, 15, 14, 27, 13, 4, 13, 15, 9},
                                {10, 3, 7, 3, 15, 12, 18, 13, 4, 13, 15, 9},
                                {10, 3, 7, 3, 15, 12, 18, 13, 4, 13, 15, 9},
                                {10, 3, 7, 3, 15, 12, 18, 13, 4, 13, 15, 9},
                                {10, 3, 7, 3, 15, 12, 19, 13, 4, 13, 15, 9},
                                {10, 3, 7, 3, 15, 12, 19, 13, 4, 13, 15, 9},
                                {10, 3, 7, 3, 15, 12, 19, 13, 4, 13, 15, 9},
                                {10, 3, 7, 3, 15, 12, 19, 13, 4, 13, 15, 9},
                                {10, 3, 7, 3, 15, 12, 20, 13, 4, 13, 15, 9},
                                {10, 3, 7, 3, 15, 12, 20, 13, 4, 13, 15, 9}};


#if 0 /* This is the table for a 40MHz RFPLL Reference */
int synth_cal_lut[53][12] = {   {10, 0, 4, 0, 15, 8, 8, 12, 3, 14, 15, 11},
                                {10, 0, 4, 0, 15, 8, 9, 12, 3, 14, 15, 11},
                                {10, 0, 4, 0, 15, 8, 9, 12, 3, 14, 15, 11},
                                {10, 0, 4, 0, 15, 8, 10, 12, 3, 14, 15, 11},
                                {10, 0, 4, 0, 15, 8, 11, 12, 3, 14, 15, 11},
                                {10, 0, 4, 0, 15, 8, 11, 12, 3, 14, 15, 11},
                                {10, 0, 4, 0, 14, 8, 12, 12, 3, 14, 15, 11},
                                {10, 0, 5, 1, 14, 9, 13, 12, 3, 14, 15, 11},
                                {10, 0, 5, 1, 14, 9, 13, 12, 3, 14, 15, 11},
                                {10, 0, 5, 1, 14, 9, 14, 12, 3, 14, 15, 11},
                                {10, 0, 5, 1, 14, 9, 15, 12, 3, 14, 15, 11},
                                {10, 0, 5, 1, 14, 9, 15, 12, 3, 14, 15, 11},
                                {10, 0, 5, 1, 14, 9, 16, 12, 3, 14, 15, 11},
                                {10, 0, 5, 1, 14, 9, 17, 12, 3, 14, 15, 11},
                                {10, 0, 5, 1, 14, 9, 17, 12, 3, 14, 15, 11},
                                {10, 0, 5, 1, 14, 9, 18, 12, 3, 14, 15, 11},
                                {10, 1, 6, 1, 15, 11, 13, 12, 3, 14, 15, 11},
                                {10, 1, 6, 1, 15, 11, 14, 12, 3, 14, 15, 11},
                                {10, 1, 6, 1, 15, 11, 14, 12, 3, 14, 15, 11},
                                {10, 1, 6, 1, 15, 11, 15, 12, 3, 14, 15, 11},
                                {10, 1, 6, 1, 15, 11, 15, 12, 3, 14, 15, 11},
                                {10, 1, 6, 1, 15, 11, 16, 12, 3, 14, 15, 11},
                                {10, 1, 6, 1, 15, 11, 16, 12, 3, 14, 15, 11},
                                {10, 1, 6, 1, 15, 11, 17, 12, 3, 14, 15, 11},
                                {10, 1, 6, 1, 15, 11, 17, 12, 3, 14, 15, 11},
                                {10, 1, 6, 1, 15, 11, 17, 12, 3, 14, 15, 11},
                                {10, 1, 6, 1, 15, 11, 18, 12, 3, 14, 15, 11},
                                {10, 1, 6, 1, 15, 11, 18, 12, 3, 14, 15, 11},
                                {10, 1, 6, 1, 15, 11, 19, 12, 3, 14, 15, 11},
                                {10, 1, 7, 2, 15, 12, 19, 12, 3, 14, 15, 11},
                                {10, 1, 7, 2, 15, 12, 20, 12, 3, 14, 15, 11},
                                {10, 1, 7, 2, 15, 12, 20, 12, 3, 14, 15, 11},
                                {10, 1, 7, 2, 15, 14, 21, 12, 3, 14, 15, 11},
                                {10, 1, 7, 2, 15, 14, 21, 12, 3, 14, 15, 11},
                                {10, 1, 7, 2, 15, 14, 22, 12, 3, 14, 15, 11},
                                {10, 1, 7, 2, 15, 14, 22, 12, 3, 14, 15, 11},
                                {10, 1, 7, 2, 15, 14, 23, 12, 3, 14, 15, 11},
                                {10, 1, 7, 2, 15, 14, 23, 12, 3, 14, 15, 11},
                                {10, 1, 7, 2, 15, 14, 24, 12, 3, 14, 15, 11},
                                {10, 1, 7, 2, 15, 14, 24, 12, 3, 14, 15, 11},
                                {10, 1, 7, 2, 15, 14, 25, 12, 3, 14, 15, 11},
                                {10, 1, 7, 2, 15, 14, 25, 12, 3, 14, 15, 11},
                                {10, 1, 7, 2, 15, 14, 26, 12, 3, 14, 15, 11},
                                {10, 1, 7, 2, 15, 14, 26, 12, 3, 14, 15, 11},
                                {10, 3, 7, 3, 15, 12, 17, 12, 3, 14, 15, 11},
                                {10, 3, 7, 3, 15, 12, 17, 12, 3, 14, 15, 11},
                                {10, 3, 7, 3, 15, 12, 17, 12, 3, 14, 15, 11},
                                {10, 3, 7, 3, 15, 12, 18, 12, 3, 14, 15, 11},
                                {10, 3, 7, 3, 15, 12, 18, 12, 3, 14, 15, 11},
                                {10, 3, 7, 3, 15, 12, 18, 12, 3, 14, 15, 11},
                                {10, 3, 7, 3, 15, 12, 18, 12, 3, 14, 15, 11},
                                {10, 3, 7, 3, 15, 12, 19, 12, 3, 14, 15, 11},
                                {10, 3, 7, 3, 15, 12, 19, 12, 3, 14, 15, 11} };
#endif

#endif /* INCLUDED_AD9361_SYNTH_LUT_HPP */

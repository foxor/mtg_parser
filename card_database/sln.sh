#!/bin/bash
rm wget.*
./create_wget_input.sh > wget.in
wget -i wget.in -O wget.out -o wget.log

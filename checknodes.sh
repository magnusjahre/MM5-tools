#!/bin/bash

nodes=$@

for n in $nodes; do
    ssh $n /home/jahre/bin/jahre-nodecommands.sh
done
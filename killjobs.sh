#!/bin/bash

I=$1

while [ $I -lt $2 ]
  do
  qdel $I
  echo "deleting $I"
  I=$((I+1))
done

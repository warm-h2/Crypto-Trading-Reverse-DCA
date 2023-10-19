#!/bin/bash

CONDAPATH="$CONDAPATH"
ENVNAME="rdca"

if [ "$ENVNAME" == "base" ]; then
  ENVPATH="$CONDAPATH"
else
  ENVPATH="$CONDAPATH/envs/$ENVNAME"
fi

source "$CONDAPATH/Scripts/activate" "$ENVPATH"

cd "$(dirname "$0")"
python main.py

read -p "Press Enter to continue..."
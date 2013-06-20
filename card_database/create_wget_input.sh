#!/bin/bash
#for i in {1..218079}
echo "http://gatherer.wizards.com/Pages/Card/Details.aspx?multiverseid=58"
for i in {218079..276300}
do
   echo "http://gatherer.wizards.com/Pages/Card/Details.aspx?multiverseid=$i"
done

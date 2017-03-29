==Beaker power scripts==

These are power scripts for beaker to work with amt devices. The two scripts
are for the two implementations of amt:
* ```amt``` - for the (deprecated) soap implementation of amt, which can be used
  in amt versions below 6.0
* ```amt-ws``` - for the wsman implementation of amt, which can be used in amt
  versions from 3.2 and up

If you want to use these scripts with beaker you have to configure amt for the
user admin (this can't be changed), place these scripts in the
```/etc/beaker/power-scripts/``` directory and install both fence-agents-amt
and fence-agents-amt-ws 

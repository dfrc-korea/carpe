# carpe
Carpe Forensics

## Dependency Requirement
### [ python package ]
* structureReader

## [ Usage ]
python actuator.py -t (type to carve) -f (file path) [-e (encoding)] [-b (block size)] [-from (start point)] [-to (end point)] 

Support type :

* event(evt/evtx)

* index(index.dat)

* link(lnk)

* mft entry

* pe(exe,dll)

* prefetch(pf)

* registry

* sqlite

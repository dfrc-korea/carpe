# carpe
Carpe Forensics

## Dependency Requirement
### [ python package ]
* structureReader

## [ Usage ]
python actuator.py -t (type to carve) -f (file path) [-e (encoding)] [-b (block size)] [-from (start point)] [-to (end point)] 

Support type :

* event (evt/evtx)
> Essential parameter : 
> Image file, Base offset, Cluster size

* index (index.dat)
> Essential parameter : 
> Image file, Base offset, Cluster size

* link (lnk)
> Essential parameter : 
> Image file, Base offset, Cluster size, Encoding type

* mft
> Essential parameter :
> Image file, Base offset, Cluster size

* pe (exe,dll)
> Essential parameter : 
> Image file, Base offset

* prefetch (pf)
> Essential parameter : 
> Image file, Base offset, Cluster size

* registry
> Essential parameter : 
> Image file, Base offset, Cluster size

* sqlite
> Essential parameter : 
> Image file, Base offset


# carpe
Carpe Forensics

## Dependency Requirement
### [ python package ]
* structureReader

## [ Usage ]
python actuator.py -t (type to carve) -f (file path) [-e (encoding)] [-b (block size)] [-from (start point)] [-to (end point)] [-cmd (string)] [-opt (bool)]

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

## [ 파라미터 특성 ]

* Image file   : 파일 경로 ("string")
* Base offset  : 시작 오프셋 ("int", default=0)
* Cluster size : 클러스터 크기 ("int")
* Encoding type: 인코딩 타입 ("string", default="utf-8")
* Last offset  : 마지막 오프셋 ("int", default=0)

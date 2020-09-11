# Android Usagestats XML & Protobuf Parser  

![alt text](/usage%20example.PNG "Usage example")

To view details on the script and accompanying SQL query see the blogpost here:  
https://abrignoni.blogspot.com/2019/02/android-usagestats-xml-parser.html 

Usage:  
1. Extract usagestats directory.  
2. Place script in the same root directory as the extracted usagestats directory.  
3. Run script. No arguments needed.  
4. Open the generated usagestats.db SQLite database with any SQLite viewer software.  
5. Run the results.sql query on the generated database.  
6. Export the results and/or modify SQL query as needed.  

This now works with both XML based usagestats as well as the newer Protocol buffer one.
For Protocol buffer support the following is a pre-requirement: pip install protobuf

Thanks and all credit go to Yogesh Khatri for protobuf support. FOr more information see the following blogpost:
https://www.swiftforensics.com/2020/01/usagestats-on-android-10-q.html

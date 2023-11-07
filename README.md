# retrocomputing-database
This scraper creates a retrocomputing database of vintage computer models, collecting data from: https://www.1000bit.it, https://www.system-cfg.com and https://www.oldcomputer.info 



## Install


This project requires PostgreSQL. See https://www.postgresql.org/ for easy installation instructions. 

<br>
Clone the git repository:

``` git clone  https://github.com/micb5/retrocomputing-database.git```

<br>
Install the requirements using pip:

``` pip install -r requirements.txt ```


## Run


Insert your PostgreSQL connection parameters in the <code>database.ini</code> file.  
As an example:

```
[postgresql]
host=localhost
database=retrocomputing
user=postgres
password=Pa$$word
port=5432
```

<br>
Run the code:

``` python retrocomputing.py ```


<br>
<br>
Alternatively, you can run the scripts one by one. The following order is recommended:

``` python ws_1000bit.py```

``` python ws_systemcfg.py```

``` python ws_oldcomputer.py```



# Drill Workshop - Amazon Spot Prices

## Framework

1. short but rich introduction (~20- 30 minutes?) that really tells the story, gives the take-home concepts etc. so that if people don't stay the entire time or cannot get connected etc. they still get a good bit of information, a good discussion, a good lesson.

Let's guess your audience is mainly business analysts: Don't jump to details or comparisons with Impala. Instead jump into what they might want to do with Drill: what purpose does it serve for them?

Give several examples, with the business need, the role of Drill, the benefit of using it. Keep them fairly brief and fairly fast moving but rich. Then sum up this part with a quick comparison (if appropriate) to Impala for instance and mainly some summary statements about when/ why Drill is useful. These latter "bullet points" may become the key concepts of the demo/workshop in Part 2.

2. Main workshop:  hands-on, or live demo or recorded examples + discussion.  45 min - 60 min

Pick 3 - 5 concepts or key variations on what Drill can do. Build at least an intro slide for each one so that people get a strong visual imprint of the lesson you are showing. (Depending on what you do and how long it would take, maybe 10 - 15 minute each concept)

in other words: "Drill can query nested data such as you'd need in <give an example> Let's see how that works..." and then show or have them do it.

I'm not sure what examples you want to show. Here are some that pop to mind, but I'd need to refresh my thinking on Drill to suggest anything really useful.

Different data types? (that might be several of your concepts)

How to use views?

The "shape" of a good query? 

Connections to a visualization tool such as Tableau?

Remember you can use a combination of slides, discussion, live demo, recorded demo with discussion, etc. 

A good format is to separate each topic, even if just different data types. Clearly identify the "lesson" or point you're making for each one at the start and the end of each little lesson.
Tell what you'll show, 
then show how to do it, 
ask questions that spark discussion (do you use data like this? what types of SQL queries do you usually use? etc)
close with a slide that reiterates what they've seen or done (just the main idea
Part 3  Closing short discussion or summary 5 - 10 min
This doesn't need to be long since you'll have interspersed discussion and questions.  

Close with a slide you repeat from the opening that shows resources:

Drill website <add link>
Drill 10 min tutorial  <add link>
@ApacheDrill Twitter identity
 Pick one of the good blogs (Drill site or MapR site, preferably the latter) and offer link to it.

Perhaps add link to "Free Hadoop Training" and MapR edu services link.



## Goals

At the end of this workshop, we hope you'll have learned about the following concepts in Drill:

* Storage plugins
* Querying files in your file system with Drill
* Contrast between JSON and Parquet format
** Space
** Performance (Query time)
* Views
* ODBC (Time permitting)
* Visualization (Time permitting)


## Overview
short but rich introduction (~20- 30 minutes?) that really tells the story, gives the take-home concepts etc. so that if people don't stay the entire time or cannot get connected etc. they still get a good bit of information, a good discussion, a good lesson.



## Prerequisites

Download Apache Drill 0.8.0. From the command line on linux or Mac OS:

```
curl -LO http://getdrill.org/drill/download/apache-drill-0.8.0.tar.gz
```

Follow the instructions to install Drill on your platform.

### Start drill in embedded mode

Start Drill with an embedded Zookeeper as follows (adjust the path to sqlline as needed, based on where you installed Drill):

```
/opt/apache-drill-0.8.0/bin/sqlline -u jdbc:drill:zk=local
```

Once done, you should be able to connect to http://localhost:8047 in your browser and explore the Drill UI.


## Storage Plugins and Workspaces
Slide: What are storage plugins used for? How do we use them here?

Drill uses storage plugins to connect to different types of data. Beyond the scope of this workshop, but you can develop a plugin and contribute it back to the project (link to info).

Make a directory on your system to create a destination for the data we'll be working with. You can do

```
mkdir /tmp/spot_data
```

To create the directory we will place the data in.

In the Drill UI (http://localhost:8047), navigate to the "Storage" tab, then click "Update" next to the "dfs" plugin. We're going to edit this plugin to add a workspace.

Delete the contents of the dfs plugin. Open a browser window to: http://goo.gl/6JJahf

Copy and paste the JSON you see at that link into the dfs plugin, and click "Update". The status bar the bottom of the browser should show "success".


## The Data

Slide: The data is complex, with nested elements. The data will also need to be joined later, since no individual view has everything we might want to know. 

Get the data we're working with here: https://s3.amazonaws.com/vgonzalez/data/spot-prices/spot-price-data.tar.gz

Unpack this to the directory you added to the dfs storage plugin.

We will use spot instance data from Amazon ec2. I used the below to get data on spot instance requests in a few regions (you don't need to do this, supplied for reference):

https://gist.github.com/vicenteg/2174325e1ee6095e679b

The data obtained is complex in that it has nested elements. 

```
{
    "SpotInstanceRequests": [
        {
            "Status": {
                "UpdateTime": "2015-01-23T04:18:20.000Z", 
                "Code": "fulfilled", 
                "Message": "Your Spot request is fulfilled."
            }, 
            "ProductDescription": "Windows", 
            "Tags": [
                {
                    "Value": "apernsteiner", 
                    "Key": "user"
                }, 
                {
                    "Value": "apernsteiner-win", 
                    "Key": "Name"
                }
            ], 
            "InstanceId": "i-6451589f", 
            "SpotInstanceRequestId": "sir-02ev4q8d", 
            "State": "active", 
            "LaunchedAvailabilityZone": "us-east-1b", 
...
            "CreateTime": "2015-01-23T04:12:29.000Z", 
            "SpotPrice": "0.500000"
        }, ...
```

The key SpotInstanceRequests has a value that is a list of maps, and each map contains more key-value pairs where the values can be complex objects themselves (lists, maps, or scalar values).

We'll also work with some simpler JSON data, that is not nested, and is in more of a tabular format.

For the history data, there is a top level directory called data, with date partitioned directories (`/history/<year>/<month>/<day>/<region>-prices.json`).

The script used to produce this data is available on github. The script uses the AWS CLI script to download the data, then do some simple reshaping of the JSON object - instead of storing all the data for a single request in a single large JSON object, we store each spot price change object as a single object on a single line in the file.

The script also automatically partitions the data by date - each request with the AWS CLI obtains a day's worth of spot price changes, and the script stores them in one file per region per day.

All the data being used here is JSON, but we will change that later.

## Some Exploratory Queries
N.B.: before doing these queries, any files with empty schemas need to be removed, or you will get errors related to empty schemas from Drill.

Having just downloaded this data, maybe we don't really know what's in it. You could explore the schema, and try to figure out the structure first. That's a good idea. But you could also just see if Drill can figure it out for you (sometimes it can, sometimes it can't).

Provided drill is running and you set up your workspace, you can now run the following queries to see what Drill makes of the data:

```
use dfs.spot;
show files;
select * from history limit 1;
select * from instances limit 1;
select * from requests limit 1;
```

Line 1 selects the dfs.spot workspace, which tells Drill that it should look for any tables relative to the workspace path.

Line 2 shows the files in that workspace, which should look like this:

```
0: jdbc:drill:zk=localhost:2181> show files;
+------------+-------------+------------+------------+------------+------------+-------------+------------+------------------+
|    name    | isDirectory |   isFile   |   length   |   owner    |   group    | permissions | accessTime | modificationTime |
+------------+-------------+------------+------------+------------+------------+-------------+------------+------------------+
| history    | true        | false      | 136        | vince      | staff      | rwxr-xr-x   | 1969-12-31 19:00:00.0 | 2015-03-16 12:46:43.0 |
| instances  | true        | false      | 272        | vince      | staff      | rwxr-xr-x   | 1969-12-31 19:00:00.0 | 2015-03-31 09:01:49.0 |
| requests   | true        | false      | 136        | vince      | staff      | rwxr-xr-x   | 1969-12-31 19:00:00.0 | 2015-03-30 15:30:36.0 |
+------------+-------------+------------+------------+------------+------------+-------------+------------+------------------+
3 rows selected (0.066 seconds)
```

Questions:

What do you notice that's interesting about the history data?
There's (dir0,dir1,dir2)
What do you notice about the instances and requests data?
There's one row, with JSON embedded in it.

## On Demand Pricing

Here's a query to obtain the on-demand pricing:

```
select * from ondemand where os='linux' and ebsoptimized='false' and pricing='od' and latest='true';
```


## Instance Data

We queried the instances directory and got back a single column with a JSON "blob" in it. This is not real helpful. We want to turn the data into multiple columns that we can query. But there's also complex objects in the data; things like lists and maps inside of other lists and maps. So let's use a query that pulls out the data we're interested in and presents it in a tabular form that we can use in further queries.

Here's what the original query looked like (shortened for brevity):

```
0: jdbc:drill:zk=localhost:2181> select * from instances limit 1;
+--------------+
| Reservations |
+--------------+
| [{"OwnerId":"674241104242","ReservationId":"r-ade6226c","Instances":[{"Monitoring":{"State":"disabled"},"PublicDnsName":"ec2-54-93-49-199.eu-central-1.compute.amazonaws.com"...
+--------------+
1 row selected (0.266 seconds)
```

There are a couple of problems with this. First, the entire JSON object is in one column. Second, if we remove the limit clause, we see there's a row per file. 

Notice that the "Reservations" column is a list containing maps. We want each map to become a row in the result set.  We do this with the FLATTEN function, and we'll use the COUNT function to show that we've now got more rows:

```
0: jdbc:drill:zk=localhost:2181> select count(flatten(Reservations)) from instances;
+------------+
|   EXPR$0   |
+------------+
| 90         |
+------------+
1 row selected (0.947 seconds)
```

Remove the COUNT around the FLATTEN in your own query if you want to see the rows for yourself.

This is better, but we still have a blob in a single column. Tough to make anything of this as-is. So let's query it again, pulling out the fields we care about into columns.


## Spot Price History Data
Form the query with some light transforms and casts to get things to the right type

The data as obtained from Amazon contains timestamps that can't be parsed by Drill as-is if we want to use the timestamp type. So we need to transform them. We'll use the replace function in order to remove the bits of text that make the date unparseable. Note the replace functions inside the cast for Timestamp. Also note the use of backticks around replace and the Timestamp column name - we need these because Drill is still rather protective around reserved words.

```
create or replace view spot_price_history as 
  (select 
    dir0 as `year`,
    dir1 as `month`,
    dir2 as `day`,
    cast(AvailabilityZone as varchar(15)) as AvailabilityZone,
    cast(SpotPrice as float) as SpotPrice,
    cast(InstanceType as varchar(15)) as InstanceType,
    cast(ProductDescription as varchar(15)) as ProductDescription,
    cast(`replace`(`replace`(`Timestamp`, 'T', ' '), '.000Z', '') as timestamp) as `Timestamp`
  from dfs.spot.history);
```

```
create or replace view spot_price_history as 
  (select 
    dir0 as `year`,
    dir1 as `month`,
    dir2 as `day`,
    cast(AvailabilityZone as varchar(15)) as AvailabilityZone,
    cast(SpotPrice as float) as SpotPrice,
    cast(InstanceType as varchar(15)) as InstanceType,
    cast(ProductDescription as varchar(15)) as ProductDescription,
    to_timestamp(`replace`(`replace`(`Timestamp`, 'T', ' '), '.000Z', ''), 'YYYY-MM-dd HH:mm:ss') as `Timestamp`
from dfs.spot.history);
```

```
create or replace view spot_price_history as 
  (select 
    dir0 as `year`,
    dir1 as `month`,
    dir2 as `day`,
    cast(AvailabilityZone as varchar(15)) as AvailabilityZone,
    cast(SpotPrice as float) as SpotPrice,
    cast(InstanceType as varchar(15)) as InstanceType,
    cast(ProductDescription as varchar(15)) as ProductDescription,
    to_timestamp(`Timestamp`, 'YYYY-MM-dd''T''HH:mm:ss.SSS''Z''') as `Timestamp`
from dfs.spot.history);
```

## Why use a view?

1. It allows us to simplify future queries
2. It allows us to use the files in-place while casting to Drill types (for joins and comparisons)


## Convert from JSON to Parquet

```
alter session set `store.format`='parquet';
create table t as select * from spot_price_history;
```

# Analysis

## Get variance


We'll compute the variance of the spot prices by region, using the built-in variance function:

select AvailabilityZone,InstanceType,min(SpotPrice) as min_price,avg(SpotPrice) as avg_price,max(SpotPrice) as max_price, variance(SpotPrice) as price_variance from p_spot_prices where InstanceType in ('hi1.4xlarge') group by AvailabilityZone,InstanceType order by AvailabilityZone,price_variance asc;




# Notes

## On-demand Pricing

http://info.awsstream.com/instances.json?

## Clearing Tag Values

jq command line used to replace tag values (since they might contain "interesting" information):

```
$ jq '.["Reservations"][]["Instances"][]["Tags"][]["Value"] |= "foo"'  <\
  instances-us-east-1.json >\
  instances-us-east-1-cleaned.json
```

## Questions we want to ask of the data

Distribution of bids? 

Are certain times more volatile than others for a given region/AZ?

Which are the most/least volatile instance types? Regions?

Spread between spot and on-demand - which instance types give best bang/buck versus on-demand? Versus reserved instances?

For some actual instances, how much are we saving/wasting versus on-demand/spot instances?


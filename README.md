# Drill Workshop - Amazon Spot Prices


## Goals

At the end of this workshop, we hope you'll have learned about the following concepts in Drill:

* Storage plugins
* Querying files in your file system with Drill
* Contrast between JSON and Parquet format
  * Space
  * Performance (Query time)
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


### Spot Instance Requests

The spot instance request data is complex in that it has nested elements:

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

### Spot Price History Data

The spot price history data is simpler than the spot request data. It is not nested, and is in more of a tabular format. It is still JSON.

In the history data, there is a top level directory called `history`, with date partitioned directories (`/history/<year>/<month>/<day>/<region>-prices.json`).

The script used to produce this data is available on github. The script uses the AWS CLI script to download the data, then do some simple reshaping of the JSON object - instead of storing all the data for a single request in a single large JSON object, we store each spot price change object as a single object on a single line in the file.

The script also automatically partitions the data by date - each request with the AWS CLI obtains a day's worth of spot price changes, and the script stores them in one file per region per day.

I used the below to get data on spot instance requests in a few regions (you don't need to do this, supplied for reference):

https://gist.github.com/vicenteg/2174325e1ee6095e679b

### EC2 on demand pricing

I obtained the on-demand pricing data here: http://info.awsstream.com/instances.json?

It required some simple reshaping for which I used jq.


### Some Exploratory Queries

Having just downloaded this data, maybe we don't really know what's in it. You could explore the schema, and try to figure out the structure first. That's a good idea. But you could also just see if Drill can figure it out for you (sometimes it can, sometimes it can't).

Provided drill is running and you set up your workspace, you can now run the following queries to see what Drill makes of the data:

```
use dfs.spot;
show files;
select * from history limit 1;
select * from instances limit 1;
select * from requests limit 1;
select * from ondemand limit 1;
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

* What do you notice that's interesting about the history data?
  * dir0,dir1,dir2 match the date partitions.

* What do you notice about the instances and requests data?
  * There's one row, with JSON embedded in it.


## On Demand Pricing

There's lots in here we're going to ignore. So set up a view with just the stuff we want:

```
create or replace view ondemand_linux_price_view as
    select region, cast(hourly as float) as hourly, model 
        from ondemand 
        where os='linux' and ebsoptimized='false' and pricing='od' and latest='true';
```

Here's a query to obtain the on-demand pricing:

```
select * from ondemand where os='linux' and ebsoptimized='false' and pricing='od' and latest='true';
```


## Instance Data


We queried the instances directory and got back a single column with a JSON "blob" in it. This is not terribly helpful. We want to turn the data into rows and columns that we can query. But there's also complex objects in the data; things like lists and maps inside of other lists and maps. So let's use a query that pulls out the data we're interested in and presents it in a tabular form that we can use in further queries.

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
0: jdbc:drill:zk=localhost:2181> select count(*) from (select flatten(Reservations) from instances);
+------------+
|   EXPR$0   |
+------------+
| 90         |
+------------+
1 row selected (0.947 seconds)
```

Use only the sub-select if you want to see all the rows:

```
0: jdbc:drill:zk=local> select flatten(Reservations) from instances;
```

This is better, but we still have a blob in a single column. Tough to make anything of this as-is. So let's query it again, pulling out the fields we care about into columns. We care about the Instance details, so let's get the instances data.

Hmm. Looking at the "Instances" value, we have yet another array (dead giveaway is that each row in the column starts with a `[`). So we'll need to flatten it again to get a row for each Instance:

```
select flatten(r.Reservations['Instances']) as Instances from (select flatten(Reservations) as Reservations from instances) as r;
```

You should see that we went from having 90 rows to 232 rows. 

From here, we can create a view from the parts of the Instance object that we care about:

```
select
    Instances['Placement']['AvailabilityZone'] as AvailabilityZone,
    Instances['InstanceType'] as InstanceType,
    cast(to_timestamp(`replace`(Instances['LaunchTime'], 'T', ' '), 'YYYY-MM-dd HH:mm:ss.SSSZ') as Timestamp) as LaunchTime,
    Instances['State']['Name'] as State
  from 
    (select flatten(r.Reservations['Instances']) as Instances from 
        (select flatten(Reservations) as Reservations from instances) as r);
```

This is getting complicated. Once we're pretty sure this is how we want our table to look, we can make future queries against this easier by creating a view. When creating the view, we'll make sure to be explicit about the column types, to make comparisons smoother.

```
create or replace view instance_view as
  select
    cast(Instances['Placement']['AvailabilityZone'] as VARCHAR(32)) as AvailabilityZone,
    cast(Instances['InstanceType'] as VARCHAR(16)) as InstanceType,
    cast(to_timestamp(`replace`(Instances['LaunchTime'], 'T', ' '), 'YYYY-MM-dd HH:mm:ss.SSSZ') as Timestamp) as LaunchTime,
    cast(Instances['State']['Name'] as VARCHAR(16)) as State
  from 
    (select flatten(r.Reservations['Instances']) as Instances from 
        (select flatten(Reservations) as Reservations from instances) as r);
```

Now we can get the same result as above from a much simpler query:

```
select * from instance_view;
```

### Questions:

1. Take a look at the directory where you unpacked the files (your workspace). Look at the files with the `.view.drill` extension, and notice how they're constructed.


## Spot Price History Data

The data as obtained from Amazon contains timestamps that can't be parsed by Drill as-is if we want to use the timestamp type. So we need to transform them. We'll use the replace function in order to remove the bits of text that make the date unparseable. Note the replace functions inside the cast for Timestamp. Also note the use of backticks around replace and the Timestamp column name - we need these because Drill is still rather protective around reserved words.

```
create or replace view spot_price_history as 
  (select 
    cast(dir0 as INT) as `year`,
    cast(dir1 as INT) as `month`,
    cast(dir2 as INT) as `day`,
    to_timestamp(`replace`(`Timestamp`, 'T', ' '), 'YYYY-MM-dd HH:mm:ss.SSSZ') as `Timestamp`,
    cast(ProductDescription as VARCHAR(32)) as ProductDescription,
    cast(InstanceType as VARCHAR(16)) as InstanceType,
    cast(SpotPrice as float) as SpotPrice,
    cast(AvailabilityZone as VARCHAR(20)) as AvailabilityZone
  from dfs.spot.history);
```

## Why use a view?

1. It allows us to simplify future queries
2. It allows us to use the files in-place while casting to Drill types (for joins and comparisons)

# A Join 

```
select
    iv.InstanceType,
    100 - (100 * (avg(sv.SpotPrice) / avg(od.hourly))) as SpotSavingsPercent 
  from
    instance_view iv,
    spot_price_history sv,
    ondemand_linux_price_view od
  where 
    iv.InstanceType = sv.InstanceType and 
    iv.InstanceType = od.model 
  group by iv.InstanceType;
```

This query takes way too long - over 6 minutes on my laptop. Perhaps it's because we're scanning through a couple of gigabytes of spot price history that's stored in a suboptimal format (for performance).


```
select
    iv.InstanceType,
    100 - (100 * (avg(sv.SpotPrice) / avg(od.hourly))) as SpotSavingsPercent 
  from
    (select InstanceType,AvailabilityZone,avg(SpotPrice) as SpotPrice from history_parquet group by InstanceType, AvailabilityZone) sv,
    instance_view iv,
    ondemand_linux_price_view od
  where 
    iv.InstanceType = sv.InstanceType and 
    iv.InstanceType = od.model 
  group by iv.InstanceType
  order by SpotSavingsPercent desc;
```


## Convert from JSON to Parquet

```
alter session set `store.format`='parquet';
create table history_parquet as
  select 
    to_timestamp(`replace`(`Timestamp`, 'T', ' '), 'YYYY-MM-dd HH:mm:ss.SSSZ') as `Timestamp`,
    cast(ProductDescription as VARCHAR(32)) as ProductDescription,
    cast(InstanceType as VARCHAR(16)) as InstanceType,
    cast(SpotPrice as float) as SpotPrice,
    cast(AvailabilityZone as VARCHAR(20)) as AvailabilityZone
  from history;
```

# Analysis

## Get variance

We'll compute the variance of the spot prices by region, using the built-in variance function:


```
select 
    AvailabilityZone,
    InstanceType,min(SpotPrice) as min_price,
    round(avg(SpotPrice) as avg_price),
    max(SpotPrice) as max_price, 
    variance(SpotPrice) as price_variance 
  from 
    history_parquet 
  where 
    InstanceType in ('hi1.4xlarge') 
  group by 
    AvailabilityZone,
    InstanceType 
  order by 
    AvailabilityZone,
    price_variance
  asc;
```



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

Spread between spot and on-demand - which instance types give best bang/buck versus on-demand?

For some actual instances, how much are we saving/wasting versus on-demand/spot instances?


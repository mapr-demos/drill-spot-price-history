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

## Prerequisites

Download Apache Drill 1.5.0. From the command line on linux or Mac OS:

```bash
curl -LO 'http://www.apache.org/dyn/closer.lua?filename=drill/drill-1.5.0/apache-drill-1.5.0.tar.gz&action=download'
```

If you are at the workshop in person, you can also use the thumb drives that are around to copy Drill and the data onto your laptop.

Follow the instructions to install Drill on your platform. I recommend for this exercise that you install to a home directory. On my mac, this looks like:

```bash
cd ~
curl -L 'http://www.apache.org/dyn/closer.lua?filename=drill/drill-1.5.0/apache-drill-1.5.0.tar.gz&action=download' | tar -vxzf -
```

### Start drill in embedded mode

Start Drill with an embedded Zookeeper as follows (adjust the path to sqlline as needed, based on where you installed Drill):

```bash
~/apache-drill-1.5.0/bin/sqlline -u jdbc:drill:zk=local
```

Once done, you should be able to connect to http://localhost:8047 in your browser and explore the Drill UI.


## Storage Plugins and Workspaces

Drill uses storage plugins to connect to different types of data. Beyond the scope of this workshop, but you can develop a plugin and contribute it back to the project: http://drill.apache.org/docs/apache-drill-contribution-guidelines/.

Let’s get the data we’ll be working with. You can download the data here: 

https://s3.amazonaws.com/vgonzalez/data/spot-prices/spot_data.tar.gz

On my mac, I can download and unpack the data in one step to my tmp directory (be sure you have ~2GB of free space before unpacking!):

```bash
curl -L https://s3.amazonaws.com/vgonzalez/data/spot-prices/spot_data.tar.gz | tar -C /tmp -vxzf -
```
This will create a directory in `/tmp` called `spot_data`. Note the path to this directory if you unpacked the tar ball somewhere else.

If you're at the workshop in person, there are also some thumb drives around with all the needed things on it. The directory looks like this:

![](img/directory.png?raw=true)

You can copy the `spot_data` directory to a location on your disk, noting the path since you'll need that later.

## Create a Workspace in Drill

Let’s create a workspace for this data by editing the dfs plugin.

In the Drill UI (http://localhost:8047), navigate to the "Storage" tab, then click "Update" next to the "dfs" plugin. 

Delete the contents of the dfs plugin. Open a browser window to: http://goo.gl/6JJahf

Copy and paste the JSON you see at that link into the dfs plugin. If you unpacked the spot_data tar ball to somewhere other than where I did, please find the `spot_data` workspace and modify the path there accordingly. Then click "Update". The status bar the bottom of the browser should show "success".

## About The Data

Some of the data we’ll use is complex, with nested elements. Some of the data is simple, without nested elements. All the data is in JSON format.

The data will also need to be joined later, since no individual view has everything we might want to know. 

### Instances

This directory contains nested data about the EC2 instances that exist.

### Spot Instance Requests

The spot instance request data is complex in that it has nested elements:

```JSON
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

I used the below to get data on spot instance requests in a few regions (you don’t need to do this, supplied for reference):

https://gist.github.com/vicenteg/2174325e1ee6095e679b

### Spot Price History Data

The spot price history data is simpler than the spot request data. It is not nested, and has a simple row/column format with each JSON object being a row. 

In the history data, there is a top level directory called `history`, with date partitioned directories (`/history/<year>/<month>/<day>/<region>-prices.json`). The path components containing the date components can be used by Drill to prune directories from the query.

The script used to produce this data is available on github. The script uses the AWS CLI script to download the data, then do some simple reshaping of the JSON object - instead of storing all the data for a single request in a single large JSON object, we store each spot price change object as a single object on a single line in the file.

The script also automatically partitions the data by date - each request with the AWS CLI obtains a day's worth of spot price changes, and the script stores them in one file per region per day.

### EC2 on demand pricing data

I obtained the on-demand pricing data here: http://info.awsstream.com/instances.json?

It required some simple reshaping for which I used jq. So the data downloaded from the above URL is modified to make it easy to query with Drill.

## Start sqlline

Drill ships with a command line tool called sqlline that you can use to submit queries. When you started sqlline above, you are actually running what's called an embedded drillbit on your local machine.

## Some Exploratory Queries

Having just downloaded this data, maybe we don't really know what's in it. You could explore the schema, and try to figure out the structure first. But you could also just see if Drill can figure it out for you, and maybe you can skip a step.

Provided drill is running and you set up your workspace, you can now run the following queries to see what Drill makes of the data:

```SQL
use dfs.spot;
show files;
select * from history limit 1;
select * from instances limit 1;
select * from requests limit 1;
```


The first query, `use dfs.spot;` selects the dfs.spot workspace, which tells Drill that it should look for any tables relative to the workspace path.

The next query shows the files in that workspace, which should look like this:

```
0: jdbc:drill:zk=local> show files;
+------------+--------------+---------+---------+--------+--------+--------------+------------------------+------------------------+
|    name    | isDirectory  | isFile  | length  | owner  | group  | permissions  |       accessTime       |    modificationTime    |
+------------+--------------+---------+---------+--------+--------+--------------+------------------------+------------------------+
| history    | true         | false   | 102     | vince  | staff  | rwxr-xr-x    | 1969-12-31 19:00:00.0  | 2015-04-06 15:17:32.0  |
| instances  | true         | false   | 272     | vince  | staff  | rwxr-xr-x    | 1969-12-31 19:00:00.0  | 2015-04-07 05:36:05.0  |
| ondemand   | true         | false   | 102     | vince  | staff  | rwxr-xr-x    | 1969-12-31 19:00:00.0  | 2015-04-06 11:25:54.0  |
| requests   | true         | false   | 136     | vince  | staff  | rwxr-xr-x    | 1969-12-31 19:00:00.0  | 2015-04-03 10:58:07.0  |
+------------+--------------+---------+---------+--------+--------+--------------+------------------------+------------------------+
4 rows selected (0.119 seconds)
```

Run a query on one more directory. This one will fail:

```SQL
select * from ondemand limit 1;
```

When you run this, you’ll probably get an error with an exception like:

```
Query failed: Query stopped., You tried to write a BigInt type when you are using a ValueWriter of type NullableFloat8WriterImpl. [ 1ecc13be-1ed2-47b8-ac32-99d0a618c681 on 192.168.1.5:31010 ]
```

This is saying that there was a schema change somewhere in the data that confused Drill; so the query fails. Specifically, somewhere in the data, the type Drill originally inferred changed from a float to an int. What we do here is tell Drill to treat numeric types as text, which means we'll need to tell it later what type to consider it. We do that by setting the following option:

```SQL
alter system set `store.json.all_text_mode` = True;
```

Once done, you should be able to query the on demand data:

```SQL
0: jdbc:drill:zk=local> select * from ondemand limit 1;
+---------+------------+----------+---------+---------------------------+---------------------------+-------+---------+-----------+--------+----------+---------------+
|   id    |   region   | upfront  | hourly  |        created_at         |        updated_at         | term  | latest  |   model   |   os   | pricing  | ebsoptimized  |
+---------+------------+----------+---------+---------------------------+---------------------------+-------+---------+-----------+--------+----------+---------------+
| 193565  | us-east-1  | 0        | 0.013   | 2015-04-01T22:15:33.157Z  | 2015-04-01T22:15:33.157Z  | 0     | true    | t2.micro  | linux  | od       | false         |
+---------+------------+----------+---------+---------------------------+---------------------------+-------+---------+-----------+--------+----------+---------------+
1 row selected (0.375 seconds)
```

In Drill 1.4.0 and later, you can also enable the UNION type (note that this feature is experimental, and it will actually break a query later; don't worry about that right now though):

```SQL
0: jdbc:drill:zk=local> ALTER SESSION SET `exec.enable_union_type` = true;
+-------+----------------------------------+
|  ok   |             summary              |
+-------+----------------------------------+
| true  | exec.enable_union_type updated.  |
+-------+----------------------------------+
1 row selected (0.09 seconds)
```

Either will allow the query to complete successfully.


### Questions:

* What do you notice that's interesting about the history data?
  * dir0,dir1,dir2 match the date partitions.

* What do you notice about the instances and requests data?
  * There's one row, with JSON embedded in it.


## On Demand Pricing

Here’s a query to obtain the on-demand pricing, filtering the results to include only Linux, on-demand instances, and instances that are not EBS optimized:

```SQL
select * 
  from ondemand 
  where 
    os='linux' and
    ebsoptimized='false' and
    pricing='od' and
    latest='true';
```

Let’s set up a view to make future queries against this result set easier:

```SQL
create or replace view ondemand_view as
    select 
      region,
      cast(hourly as float) as hourly,
      cast(model as VARCHAR(16)) as InstanceType
    from ondemand 
    where os='linux' and 
      ebsoptimized='false' and 
      pricing='od' and 
      latest='true';
```

Now you can do this:

```SQL
select * from ondemand_view;
```


### Why use a view?

1. It allows us to simplify future queries
2. It allows us to use the files in-place while casting to Drill types (for joins and comparisons)
3. It makes the query available to BI tools (such as Tableau, Excel, Microstrategy, etc)


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

If this query failed for you, perhaps you enabled the UNION type earlier. Disable it as follows, then try again:

```SQL
0: jdbc:drill:zk=local> ALTER SESSION SET `exec.enable_union_type` = false;
+-------+----------------------------------+
|  ok   |             summary              |
+-------+----------------------------------+
| true  | exec.enable_union_type updated.  |
+-------+----------------------------------+
1 row selected (0.067 seconds)
```

Use only the sub-select if you want to see all the rows:

```SQL
select flatten(Reservations) from instances;
```

This is better, but we still have a blob of JSON in a single column. Tough to make anything of this as-is. So let's query it again, pulling out the fields we care about into columns. We care about the Instance details, so let's get the instances data.

Hmm. Looking at the "Instances" value, we have yet another array (dead giveaway is that each row in the column starts with a `[`). So we'll need to flatten it again to get a row for each Instance:

```SQL
select flatten(r.Reservations.Instances) as Instances 
  from (select flatten(Reservations) as Reservations from instances) as r;
```

You should see that we went from having 90 rows to 232 rows. 

From here, we can create a view from the parts of the Instance object that we care about. Note the syntax for drilling into the nested structure:


```SQL
select
    t.Instances.InstanceId as InstanceId,
    t.Instances.Placement.AvailabilityZone as AvailabilityZone,
    t.Instances.InstanceType as InstanceType,
    cast(to_timestamp(`replace`(t.Instances.LaunchTime, 'T', ' '), 'YYYY-MM-dd HH:mm:ss.SSSZ') as Timestamp) as LaunchTime,
    t.Instances.State.Name as State
  from 
    (select flatten(r.Reservations['Instances']) as Instances from 
        (select flatten(Reservations) as Reservations from instances) as r) t;
```

One thing to node here is that to use the "dot" notation, we need to provide an alias to the table. In this case, I'm using `t`. Notice it at the very end of the query, just before the terminating semi-colon.

This is getting complicated. Once we're pretty sure this is how we want our table to look, we can make future queries against this easier by creating a view. When creating the view, we'll make sure to be explicit about the column types, to make comparisons smoother.

```SQL
create or replace view instance_view as
  select
    cast(t.Instances.InstanceId as VARCHAR(16)) as InstanceId,
    cast(t.Instances.Placement.AvailabilityZone as VARCHAR(32)) as AvailabilityZone,
    cast(t.Instances.InstanceType as VARCHAR(16)) as InstanceType,
    cast(to_timestamp(`replace`(t.Instances.LaunchTime, 'T', ' '), 'YYYY-MM-dd HH:mm:ss.SSSZ') as Timestamp) as LaunchTime,
    cast(t.Instances.State.Name as VARCHAR(16)) as State
  from 
    (select flatten(r.Reservations.Instances) as Instances from 
        (select flatten(Reservations) as Reservations from instances) as r) t;
```

Now we can get the same result as above from a much simpler query:

```SQL
select * from instance_view;
```

### Questions:

1. Take a look at the directory where you unpacked the files (your workspace). Look at the files with the `.view.drill` extension in your favorite editor, and notice how they're constructed.


## Spot Price History Data

The data as obtained from Amazon contains timestamps that can't be parsed by Drill as-is if we want to use the timestamp type. So we need to transform them. We'll use the replace function in order to remove the bits of text that make the date unparseable. Note the replace functions inside the cast for Timestamp. Also note the use of backticks around replace and the Timestamp column name - we need these because Drill includes Timestamp as a reserved word, since it is the name of a type.

```SQL
create or replace view spot_price_history as 
  (select 
    cast(dir0 as INT) as yr,
    cast(dir1 as INT) as mo,
    cast(dir2 as INT) as dy,
    cast(to_timestamp(`replace`(`Timestamp`, 'T', ' '), 'YYYY-MM-dd HH:mm:ss.SSSZ') as Timestamp) as `Timestamp`,
    cast(ProductDescription as VARCHAR(32)) as ProductDescription,
    cast(InstanceType as VARCHAR(16)) as InstanceType,
    cast(SpotPrice as float) as SpotPrice,
    cast(AvailabilityZone as VARCHAR(20)) as AvailabilityZone
  from history);
```

## Spot Requests

The spot request data is nested, so we'll use Drill's ability to query nested data to create a view for looking at the spot data we care about; instance type, launch time and pricing as it relates to availability zone:

```SQL
create or replace view requests_view as
  select 
    cast(t.req.InstanceId as VARCHAR(16)) as InstanceId,
    cast(t.req.LaunchedAvailabilityZone as VARCHAR(20)) as AvailabilityZone,
    cast(t.req.LaunchSpecification.InstanceType as VARCHAR(16)) as InstanceType,
    cast(to_timestamp(`replace`(t.req.CreateTime, 'T', ' '), 'YYYY-MM-dd HH:mm:ss.SSSZ') as Timestamp) as CreateTime
  from
    (select flatten(SpotInstanceRequests) as req from requests) t;
```


## A Join 

So let's see what kind of percent difference spot pricing would make against the instances that currently exist. To do that, we need to join together a few tables - the instance data, the on-demand pricing data, and the spot pricing data. That's a three way join, across three data sets that are backed by JSON files (note that this query will fail if you did not enable `store.json.all_text_mode` above):


```SQL
select
    iv.InstanceType,
    100 - (100 * (avg(sv.SpotPrice) / avg(od.hourly))) as SpotSavingsPercent 
  from
    instance_view iv,
    spot_price_history sv,
    ondemand_view od
  where 
    iv.InstanceType = sv.InstanceType and 
    iv.InstanceType = od.InstanceType 
  group by iv.InstanceType
  order by SpotSavingsPercent desc;
```

This query takes way too long - nearly 48 seconds (down from over a minute on Drill 1.0.0, but still a long time) on my laptop. Perhaps it's in part because we're scanning through a couple of gigabytes of spot price history when we don't really need to look at all of it.

Maybe we can prune away some of the data in the query, so that we don't have to scan the entire history? Let's just use the average spot price for one month, April (4):

```SQL
select
    iv.InstanceType,
    100 - (100 * (avg(sv.SpotPrice) / avg(od.hourly))) as SpotSavingsPercent 
  from
    (select InstanceType,AvailabilityZone,avg(SpotPrice) as SpotPrice from spot_price_history where yr = 2015 and mo = 4 group by InstanceType, AvailabilityZone) sv,
    instance_view iv,
    ondemand_view od
  where 
    iv.InstanceType = sv.InstanceType and 
    iv.InstanceType = od.InstanceType 
  group by iv.InstanceType
  order by SpotSavingsPercent desc;
```

Queried as above, Drill will ignore the directories that don't satisfy the `yr = 2015 and mo = 4` constraints, and the query goes a lot faster. <3 seconds versus several minutes. That's a pretty easy optimization we can make, and all we have to do to take advantage of it is organize the historical data into a sensible directory scheme.

We can also store the historical data in a more efficient format. Let's convert it to Parquet.

```SQL
alter session set `store.format`='parquet';
create table history_parquet as
  select 
    cast(dir0 as INT) as yr,
    cast(dir1 as INT) as mo,
    cast(dir2 as INT) as dy,
    cast(to_timestamp(`replace`(`Timestamp`, 'T', ' '), 'YYYY-MM-dd HH:mm:ss.SSSZ') as Timestamp) as `Timestamp`,
    cast(ProductDescription as VARCHAR(32)) as ProductDescription,
    cast(InstanceType as VARCHAR(16)) as InstanceType,
    cast(SpotPrice as float) as SpotPrice,
    cast(AvailabilityZone as VARCHAR(20)) as AvailabilityZone
  from history;
```

15 seconds later, we have history data in Parquet format. Big difference in terms of space:

```
$ du -hs history history_parquet/
662M  history
 52M  history_parquet/
```

Now let's replace the original view so that we can ensure comparisons work as we expect.

```SQL
create or replace view spot_price_history as
  select 
    cast(yr as INT) as yr,
    cast(mo as INT) as mo,
    cast(dy as INT) as dy,
    cast(to_timestamp(`Timestamp`, 'YYYY-MM-dd HH:mm:ss.SSS') as Timestamp) as `Timestamp`,
    cast(ProductDescription as VARCHAR(32)) as ProductDescription,
    cast(InstanceType as VARCHAR(16)) as InstanceType,
    cast(SpotPrice as float) as SpotPrice,
    cast(AvailabilityZone as VARCHAR(20)) as AvailabilityZone
  from history_parquet;
```


Let's run the partitioned query against this table:

```SQL
select
  iv.InstanceType,
  100 - (100 * (avg(sv.SpotPrice) / avg(od.hourly))) as SpotSavingsPercent
from
  instance_view iv,
  (select InstanceType,AvailabilityZone,avg(SpotPrice) as SpotPrice from spot_price_history where yr = 2015 and mo = 4 group by InstanceType, AvailabilityZone) sv,
  ondemand_view od
where
  iv.InstanceType = sv.InstanceType and
  iv.InstanceType = od.InstanceType
group by iv.InstanceType
order by SpotSavingsPercent desc;
```

This outputs:

```
+---------------+----------------------+
| InstanceType  |  SpotSavingsPercent  |
+---------------+----------------------+
| r3.2xlarge    | 70.6909299159247     |
| r3.xlarge     | 61.19331669744847    |
| c3.2xlarge    | 60.775396162075175   |
| r3.large      | 58.1294674134876     |
| m3.2xlarge    | 19.0772286095427     |
| m3.large      | 2.8905956029435487   |
| m3.xlarge     | -4.536922939991015   |
| m3.medium     | -27.335018595241195  |
+---------------+----------------------+
8 rows selected (2.443 seconds)
```

And we get an answer back in a few seconds.


Unpartitioned, we see a dramatic speedup; a little more than 3 seconds on my laptop compared with nearly 80 seconds before:

```SQL
select
  iv.InstanceType,
  100 - (100 * (avg(sv.SpotPrice) / avg(od.hourly))) as SpotSavingsPercent
from
  instance_view iv,
  (select InstanceType,AvailabilityZone,avg(SpotPrice) as SpotPrice from spot_price_history group by InstanceType, AvailabilityZone) sv,
  ondemand_view od
where
  iv.InstanceType = sv.InstanceType and
  iv.InstanceType = od.InstanceType
group by iv.InstanceType
order by SpotSavingsPercent desc;
```

Output:

```

+---------------+---------------------+
| InstanceType  | SpotSavingsPercent  |
+---------------+---------------------+
| r3.2xlarge    | 69.15557987569018   |
| r3.xlarge     | 66.36492802897897   |
| c3.2xlarge    | 63.62399021040896   |
| r3.large      | 55.885678882778755  |
| m3.2xlarge    | 18.735199249473595  |
| m3.large      | -2.138299714762695  |
| m3.xlarge     | -3.048532790786382  |
| m3.medium     | -39.01277350417584  |
+---------------+---------------------+
8 rows selected (3.271 seconds)
```


## Questions we want to ask of the data

### Volatility

Let's say I want to pick the most stable spot price for an instance. What instance type should it be, and where should I place those instances?

Use the variance function to find the volatility in spot pricing by instance and region. Let's get the top 10 most stable spot prices, across all regions:

```SQL
select 
    InstanceType,min(SpotPrice) as MinPrice,
    round(avg(SpotPrice), 3) as AvgPrice,
    max(SpotPrice) as MaxPrice, 
    round(variance(SpotPrice), 5) as PriceVariance 
  from 
    spot_price_history
  group by 
    InstanceType 
  order by 
    PriceVariance
  asc limit 10;
```

Now let's get the most stable region for an instance type of our choice:

```SQL
select 
    AvailabilityZone,
    InstanceType,min(SpotPrice) as min_price,
    round(avg(SpotPrice), 3) as avg_price,
    max(SpotPrice) as max_price, 
    variance(SpotPrice) as price_variance,
    min(`Timestamp`), max(`Timestamp`) 
  from 
    history_parquet 
  where 
    InstanceType in ('hi1.4xlarge') 
  group by 
    AvailabilityZone,
    InstanceType 
  order by 
    price_variance
  asc
  limit 10;
```


### On-demand/spot spread

Spread between spot and on-demand - which instance types give best bang/buck versus on-demand?

This will require a join between the ondemand and spot pricing tables.

```SQL
select 
    history_parquet.InstanceType,
    round(avg(history_parquet.SpotPrice),3) as AvgSpotPrice,
    round(avg(ondemand_view.hourly), 3) as AvgOnDemandPrice,
    round(((avg(history_parquet.SpotPrice) / avg(ondemand_view.hourly)) * 100),2) as PercentSavings
  from 
    history_parquet,
    ondemand_view
  where
    history_parquet.InstanceType = ondemand_view.InstanceType
  group by 
    history_parquet.InstanceType 
  order by
    PercentSavings
  desc;
```

### Efficiency

For some actual instances, how much are we saving/wasting versus on-demand/spot instances?

```SQL
select 
    iv.InstanceId,
    iv.InstanceType,
    round(avg(od.hourly),2) as AverageOnDemandPrice,
    round(avg(h.SpotPrice),2) as AvgSpotPrice
  from
    instance_view iv,
    ondemand_view od,
    history_parquet h
  where
    iv.State = 'running' and
    iv.InstanceType = od.InstanceType and
    od.InstanceType = h.InstanceType
  group by
    iv.InstanceId,
    iv.InstanceType
  order by
    InstanceType;
```

# Notes

## Making the data tarball

Exclude resource forks on Mac OS:

```bash
bsdtar -cvzf ~/Desktop/spot_data.tar.gz --disable-copyfile spot_data
```

## Clearing Tag Values

jq command line used to replace tag values (since they might contain "interesting" information):

```bash
$ jq '.["Reservations"][]["Instances"][]["Tags"][]["Value"] |= "foo"'  <\
  instances-us-east-1.json >\
  instances-us-east-1-cleaned.json
```



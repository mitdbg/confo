-- calculate conference stats
drop table if exists conf_counts;
begin;
create table conf_counts as
select c.id as id, c.id as cid, count(*) as count, min(y.year) as minyear, max(y.year) as maxyear, ''::text as yearcounts
from conferences as c, years as y, papers as p 
where p.cid = y.id and y.cid = c.id 
group by c.id;

CREATE UNIQUE INDEX conf_counts_pkey ON conf_counts USING btree (id);
CREATE UNIQUE INDEX conf_counts_cid_key ON conf_counts USING btree (cid);
commit;


-- update author publication counts

drop table if exists authors_tmp;
begin;
create table authors_tmp as 
  select a.id as id, a.name as name, count(*) as pubcount
  from authors as a, papers_authors as pa 
  where pa.author_id = a.id group by a.id, a.name;
drop table authors;
alter table authors_tmp rename to authors;

CREATE UNIQUE INDEX authors_pkey ON authors USING btree (id);
CREATE INDEX authors_name ON authors USING btree (name);
CREATE INDEX authors_name_like ON authors USING btree (name text_pattern_ops);

commit;
vacuum authors;
analyze authors;



--
-- first name statistics
--
-- drop table if exists firstname_confyears;
-- create table firstname_confyears as  
-- select split_part(a.name, ' ', 1) as firstname, p.cid, count(*) as c 
-- from authors as a, papers_authors as pa, papers as p  
-- where pa.paper_id = p.id and a.id = pa.author_id 
-- group by firstname, p.cid;

drop table if exists fname_overall_stats;
drop table if exists authors_by_fname;

begin;
create table fname_overall_stats as 
select split_part(name, ' ', 1) as fname, stddev(pubcount), avg(pubcount), count(*) 
from authors group by fname order by avg desc;

select fname, avg::int, count 
from fname_overall_stats 
where char_length(fname) > 2 
order by count desc limit 10;

-- create authors, but storing first names instead of the full name
create table authors_by_fname as 
  select id, split_part(name, ' ', 1) as fname, pubcount 
  from authors;
commit;
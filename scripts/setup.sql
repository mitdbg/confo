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


-- calculate paper-word counts
drop table if exists papers_word_counts;
create table papers_word_counts as 
select pid, word,  count(*) as c 
from words 
group by pid, word having count(*) > 1  order by c desc;


-- create tfidf table
drop table if exists year_tfidf;
create table year_tfidf (id serial,
                    yid int,
                    word varchar(128), 
                    count int, 
                    tfidf float);
create index tfidf_yid on year_tfidf(yid);
create index tfidf_word on year_tfidf(word);


drop table if exists conf_idf;
create table conf_idf (id serial,
                    cid int,
                    word varchar(128), 
                    idf float);
create index idf_cid on conf_idf(cid);
create index idf_word on conf_idf(word);


-- create conference/word -> first paper with that term table
drop table if exists first_papers;
create table first_papers (id serial,
                    cid int,
                    pid int,
                    word varchar(128));
create index fpapers_cidword on first_papers(cid, word);
create index fpapers_pid on first_papers(cid);


-- create year-paper similarity table
drop table if exists year_paper_similarity;
create table year_paper_similarity (id serial,
                     yid int,
                     pid int,
                     dist float);
create index yps_yid on year_paper_similarity(yid);
create index yps_pid on year_paper_similarity(pid);

-- calculate conference-year+word counts
drop table if exists year_word_counts;
create table year_word_counts as 
 select y.id as yid, w.word as word, count(*) as count 
 from years as y, papers as p, words as w 
 where w.pid = p.id and p.cid = y.id 
 group by y.id, w.word  
 having count(*) > 2 
 order by count desc;

CREATE INDEX cywc_yid on year_word_counts(yid);
CREATE INDEX cywc_word on year_word_counts USING btree (word);
vacuum year_word_counts;
analyze year_word_counts;


-- calculate author_year+word counts
-- drop table if exists auth_word_counts;
-- create table auth_word_counts as
--  select a.id as aid, y.id as yid, w.word as word, count(*) as count
--  from years as y, papers as p, papers_authors as pa, authors as a, words as w
--  where a.id = pa.author_id and p.id = pa.paper_id and y.id = p.cid and w.pid = p.id and
--  a.pubcount > 5
--  group by a.id, y.id, w.word;

-- CREATE INDEX awc_aid on auth_word_counts(aid);
-- CREATE INDEX awc_yid on auth_word_counts(yid);
-- CREATE INDEX awc_word on auth_word_counts USING btree (word);
-- vacuum auth_word_counts;
-- analyze auth_word_counts;


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
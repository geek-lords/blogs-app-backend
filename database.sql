create table Users (
    id varchar(36) primary key,
    first_name text not null,
    last_name text not null,
    email_address varchar(100) unique,
    password text not null
);

create table blog(
    id varchar(36) primary key,
    user_id varchar(36) not null,
    title text not null,
    content text not null,
    like_count text default 0
);
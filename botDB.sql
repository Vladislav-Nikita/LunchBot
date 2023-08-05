create database lunchBot;
set sql_safe_updates = 0;
drop database lunchBot;


use lunchBot;

create table users(
user_tgid bigint primary key,
first_name varchar(50),
last_name varchar(50),
username varchar(50),
special_role varchar(50),
credit_card integer
);

insert into users
(user_tgid, first_name, last_name, username, special_role, credit_card)
values
(589562037, 'Vlados', 'Nikitos', 'vlad_isl0ve_test', 'admin', 123),
(111111111, 'Vasya', 'Nevasya', 'vasya_username', null, 222);


insert into users
(user_tgid, first_name, last_name, username, special_role, credit_card)
values
(222222222, 'CookName', 'surname', 'cookusername', 'cook', 234);


insert into users
(user_tgid, first_name, last_name, username, special_role, credit_card)
values
(5170240692, 'User', 'OrGuest', 'someUser_Nase', null, 11111);
select user_tgid, username from users
where users.special_role = 'cook' 
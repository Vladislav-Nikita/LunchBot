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
credit_card integer,
total_in_month float default 0
);


#  Добавить таблицу с заказами
create table orders(
order_id int primary key auto_increment,
user_tgid bigint,
create_date date,
create_time time,
price float,
foreign key (user_tgid) references users(user_tgid)
);

insert into orders
(user_tgid, create_date, create_time, price)
values
(589562037, '2023.08.07','18:00',12.3);
delete from orders
where user_tgid =589562037;


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
(5170240692, 'User', 'OrGuest', 'someUser_Nase', 'admin', 11111);

delete from users
where user_tgid = 5170240692;


#____bl_sup______
insert into users
(user_tgid, first_name, last_name, username, special_role, credit_card)
values
(6321049452, 'B-Logic', 'Support', 'bl_sup', 'admin', 44444);


select user_tgid, username from users
where users.special_role = 'cook' ;

select user_tgid, username, total_in_month from users;

update users 
set total_in_month = total_in_month + 10
where user_tgid = 111111111;


select * from users;
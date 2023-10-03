CREATE TABLE IF NOT EXISTS public.users
(
    user_tgid bigint NOT NULL,
    first_name character varying(50) COLLATE pg_catalog."default",
    last_name character varying(50) COLLATE pg_catalog."default",
    username character varying(50) COLLATE pg_catalog."default",
    special_role character varying(50) COLLATE pg_catalog."default",
    CONSTRAINT users_pkey PRIMARY KEY (user_tgid)
)


INSERT INTO public.users(
	user_tgid, first_name, last_name, username, special_role)
	VALUES (589562037, 'Vladislav', 'Nikita', 'vlad_is_l0ve', 'admin');
	
INSERT INTO public.users(
	user_tgid, first_name, last_name, username, special_role)
	VALUES (6321049452, 'B-Logic', 'Support', 'bl_sup', 'admin');
	

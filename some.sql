

alter table v_user modify column `last_login` datetime(6) ;
alter table v_user modify column `nickname` varchar(200) ;
alter table v_user modify column `mobile` varchar(200) ;

show create table v_user;

CREATE TABLE `v_classification` (
`id` int NOT NULL AUTO_INCREMENT,
`title` varchar(200) NOT NULL,
`status` int DEFAULT NULL,
PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3;


CREATE TABLE `v_video` (
`id` int NOT NULL AUTO_INCREMENT,
`title` varchar(200) NOT NULL,
`desc` varchar(200) DEFAULT NULL,
`classification` varchar(200) DEFAULT NULL,
`classification_id` varchar(200) DEFAULT NULL,
`file` varchar(200) NOT NULL,
`cover` varchar(200) DEFAULT NULL,
`status` int DEFAULT NULL,
`view_count` int DEFAULT NULL,
`liked` int DEFAULT NULL,
`collected` int DEFAULT NULL,
`create_time` datetime(6) DEFAULT NULL,
`mocap_res`varchar(200) DEFAULT NULL,
`vmlalgorithm` varchar(200) DEFAULT NULL,
PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3;

  INSERT INTO v_video(title, `desc`, classification, file, cover) VALUES ("1", "1", "1", "1", "1");


CREATE TABLE `v_comment` (
`id` int NOT NULL AUTO_INCREMENT,
`user_id` varchar(200) NOT NULL,
`nickname` varchar(200) NOT NULL,
`avatar` varchar(200) NOT NULL,
`video_id` varchar(200) NOT NULL,
`content` varchar(200) NOT NULL,
`timestamp` varchar(200) NOT NULL,
PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3;

drop table  django_admin_log;
CREATE TABLE `django_admin_log` (
  `id` int NOT NULL AUTO_INCREMENT,
  `action_time` datetime(6) NOT NULL,
  `object_id` longtext,
  `object_repr` varchar(200) NOT NULL,
  `action_flag` smallint unsigned NOT NULL,
  `change_message` longtext NOT NULL,
  `content_type_id` int DEFAULT NULL,
  `user_id` int NOT NULL,
  PRIMARY KEY (`id`),
  KEY `django_admin_log_content_type_id_c4bce8eb_fk_django_co` (`content_type_id`),
  KEY `django_admin_log_user_id_c564eba6_fk_v_user_id` (`user_id`),
  CONSTRAINT `django_admin_log_content_type_id_c4bce8eb_fk_django_co` FOREIGN KEY (`content_type_id`) REFERENCES `django_content_type` (`id`),
  CONSTRAINT `django_admin_log_user_id_c564eba6_fk_v_user_id` FOREIGN KEY (`user_id`) REFERENCES `v_user` (`id`),
  CONSTRAINT `django_admin_log_chk_1` CHECK ((`action_flag` >= 0))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3


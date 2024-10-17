-- --------------------------------------------------------
-- 호스트:                          127.0.0.1
-- 서버 버전:                        10.4.32-MariaDB - mariadb.org binary distribution
-- 서버 OS:                        Win64
-- HeidiSQL 버전:                  12.8.0.6908
-- --------------------------------------------------------

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET NAMES utf8 */;
/*!50503 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;


-- go_pro 데이터베이스 구조 내보내기
CREATE DATABASE IF NOT EXISTS `go_pro` /*!40100 DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci */;
USE `go_pro`;

-- 테이블 go_pro.newscements 구조 내보내기
CREATE TABLE IF NOT EXISTS `newscements` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `title` varchar(255) NOT NULL,
  `author` varchar(255) NOT NULL,
  `date` date NOT NULL,
  `content` text NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- 테이블 데이터 go_pro.newscements:~2 rows (대략적) 내보내기
INSERT INTO `newscements` (`id`, `title`, `author`, `date`, `content`) VALUES
	(1, '테스트', '라니', '2024-10-09', '테스트입니다'),
	(3, '안녕', '운영자', '2024-10-11', '안녕 하세요\r\n라니입니다\r\n반가워요~');

-- 테이블 go_pro.comments 구조 내보내기
CREATE TABLE IF NOT EXISTS `comments` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `post_id` int(11) DEFAULT NULL,
  `author` varchar(100) NOT NULL,
  `content` text NOT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id`),
  KEY `post_id` (`post_id`),
  CONSTRAINT `comments_ibfk_1` FOREIGN KEY (`post_id`) REFERENCES `posts` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=9 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- 테이블 데이터 go_pro.comments:~8 rows (대략적) 내보내기
INSERT INTO `comments` (`id`, `post_id`, `author`, `content`, `created_at`) VALUES
	(1, 1, '안녕', '안녕안녕', '2024-10-10 14:43:04'),
	(2, 1, '라니', '응ㅋ', '2024-10-10 14:43:41'),
	(3, 1, 'ansh6647', '안녕', '2024-10-10 15:19:54'),
	(4, 1, 'ansh6647', '안녕', '2024-10-10 15:26:16'),
	(5, 1, 'ansh6647', 'dd', '2024-10-10 15:26:32'),
	(6, 2, 'ansh6647', '넹', '2024-10-10 15:44:39'),
	(7, 2, 'ansh6647', '명ㅇㅇ', '2024-10-10 15:44:41'),
	(8, 2, 'ansh6647', '안녕안녕안녕안녕안녕안녕안녕안녕안녕안녕안녕안녕안녕안녕안녕안녕안녕안녕안녕안녕안녕안녕안녕안녕안녕안녕안녕안녕안녕안녕안녕안녕안녕안녕안녕안녕안녕안녕안녕안녕안녕안녕', '2024-10-10 15:47:43');

-- 테이블 go_pro.posts 구조 내보내기
CREATE TABLE IF NOT EXISTS `posts` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `title` varchar(255) NOT NULL,
  `author` varchar(100) NOT NULL,
  `content` text NOT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- 테이블 데이터 go_pro.posts:~2 rows (대략적) 내보내기
INSERT INTO `posts` (`id`, `title`, `author`, `content`, `created_at`) VALUES
	(1, '테스트임', '라니라니', '안녕\r\n라니양', '2024-10-10 14:42:56'),
	(2, '안녕 테스트', 'ansh6647', 'hi\r\nbro hello', '2024-10-10 15:44:34'),
	(4, '타 계정 테스트', 'test', '테스트\r\n테스트(수정)', '2024-10-11 13:59:17');

-- 테이블 go_pro.users 구조 내보내기
CREATE TABLE IF NOT EXISTS `users` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `username` varchar(50) NOT NULL,
  `email` varchar(100) NOT NULL,
  `password` varchar(255) NOT NULL,
  `role` varchar(20) DEFAULT 'user',
  PRIMARY KEY (`id`),
  UNIQUE KEY `username` (`username`),
  UNIQUE KEY `email` (`email`)
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- 테이블 데이터 go_pro.users:~3 rows (대략적) 내보내기
INSERT INTO `users` (`id`, `username`, `email`, `password`, `role`) VALUES
	(1, 'ansh6647', 'ansh6647@naver.com', 'pbkdf2:sha512:600000$FyF8G9vPDZpUKwen$a0dc9fc834857b33b1216e035bd6e7a485f0c9e1ebd1ec590e22eff4f2d88730e320e916c666a658ce15eda984d3b809b8535ad466ed71507f2b576f2a8a89a6', 'admin'),
	(2, 'test', 'testtest@con.com', 'pbkdf2:sha512:600000$MYeEMm07EiMxpAct$9cfcce3ceea443c26f94afd81fc51128838ce4b2f80d837236ae107ee24709c4866ccdd32f21a240a2fe4b774487ec74c2d5d912b090e6a9ddf854541948d81c', 'user'),
	(3, 'test2', 'testtest2@con.com', 'pbkdf2:sha512:600000$akuM3SpCWStsed3W$e4a12b9d16abec124da0ddd079877755b586a82b04883f63170bb71a421652703c6c067c3af2cad44579399ba7120b0238613f93c640eee0324b7c107670b428', 'user');

/*!40103 SET TIME_ZONE=IFNULL(@OLD_TIME_ZONE, 'system') */;
/*!40101 SET SQL_MODE=IFNULL(@OLD_SQL_MODE, '') */;
/*!40014 SET FOREIGN_KEY_CHECKS=IFNULL(@OLD_FOREIGN_KEY_CHECKS, 1) */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40111 SET SQL_NOTES=IFNULL(@OLD_SQL_NOTES, 1) */;

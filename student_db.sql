-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- 主機： localhost
-- 產生時間： 2026 年 01 月 06 日 14:54
-- 伺服器版本： 10.4.28-MariaDB
-- PHP 版本： 8.0.28

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- 資料庫： `student_db`
--

-- --------------------------------------------------------

--
-- 資料表結構 `attendance`
--

CREATE TABLE `attendance` (
  `attendance_id` int(11) NOT NULL,
  `course_id` int(11) DEFAULT NULL,
  `student_id` varchar(20) DEFAULT NULL,
  `date` date DEFAULT NULL,
  `status` varchar(20) DEFAULT NULL,
  `record_time` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- 傾印資料表的資料 `attendance`
--

INSERT INTO `attendance` (`attendance_id`, `course_id`, `student_id`, `date`, `status`, `record_time`) VALUES
(1, 3, 'S2026003', '2026-01-06', '出席', '2026-01-06 08:49:05'),
(2, 3, 'S2026004', '2026-01-06', '出席', '2026-01-06 08:49:05'),
(3, 3, 'S2026005', '2026-01-06', '出席', '2026-01-06 08:49:05'),
(4, 3, 'S2026001', '2026-01-06', '出席', '2026-01-06 08:49:05'),
(5, 3, 'S2026003', '2026-01-06', '遲到', '2026-01-06 08:49:21'),
(6, 3, 'S2026004', '2026-01-06', '出席', '2026-01-06 08:49:21'),
(7, 3, 'S2026005', '2026-01-06', '出席', '2026-01-06 08:49:21'),
(8, 3, 'S2026001', '2026-01-06', '出席', '2026-01-06 08:49:21'),
(9, 2, 'S2026003', '2026-01-06', '出席', '2026-01-06 13:15:06'),
(10, 2, 'S2026004', '2026-01-06', '出席', '2026-01-06 13:15:06'),
(11, 2, 'S2026005', '2026-01-06', '出席', '2026-01-06 13:15:06'),
(12, 2, 'S2026001', '2026-01-06', '出席', '2026-01-06 13:15:06');

-- --------------------------------------------------------

--
-- 資料表結構 `courses`
--

CREATE TABLE `courses` (
  `course_id` int(11) NOT NULL,
  `course_name` varchar(100) NOT NULL,
  `teacher_id` int(11) DEFAULT NULL COMMENT '對應 users.user_id',
  `base_fee` int(11) DEFAULT 0 COMMENT '標準學費',
  `description` varchar(255) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- 傾印資料表的資料 `courses`
--

INSERT INTO `courses` (`course_id`, `course_name`, `teacher_id`, `base_fee`, `description`) VALUES
(1, '國二數學進度班', 2, 6000, '每週三、五上課'),
(2, '高一英文基礎班', 1, 5500, '每週六上課'),
(3, '高一物理基礎班', 3, 5000, '每週二 18:30'),
(4, '國三國文衝刺班', 4, 4500, '每週四 19:00');

-- --------------------------------------------------------

--
-- 資料表結構 `course_schedule`
--

CREATE TABLE `course_schedule` (
  `schedule_id` int(11) NOT NULL,
  `course_id` int(11) NOT NULL,
  `day_of_week` enum('週一','週二','週三','週四','週五','週六','週日') NOT NULL,
  `start_time` time NOT NULL,
  `end_time` time NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- 傾印資料表的資料 `course_schedule`
--

INSERT INTO `course_schedule` (`schedule_id`, `course_id`, `day_of_week`, `start_time`, `end_time`) VALUES
(1, 1, '週三', '18:30:00', '21:00:00'),
(2, 1, '週五', '18:30:00', '21:00:00'),
(3, 2, '週六', '09:00:00', '12:00:00'),
(4, 1, '週三', '18:30:00', '21:00:00'),
(5, 1, '週五', '18:30:00', '21:00:00'),
(6, 2, '週六', '09:00:00', '12:00:00'),
(7, 1, '週三', '18:30:00', '21:00:00'),
(8, 1, '週五', '18:30:00', '21:00:00'),
(9, 2, '週六', '09:00:00', '12:00:00'),
(10, 1, '週三', '18:30:00', '21:00:00'),
(11, 1, '週五', '18:30:00', '21:00:00'),
(12, 2, '週六', '09:00:00', '12:00:00');

-- --------------------------------------------------------

--
-- 資料表結構 `enrollments`
--

CREATE TABLE `enrollments` (
  `enrollment_id` int(11) NOT NULL,
  `student_id` varchar(20) DEFAULT NULL,
  `course_id` int(11) DEFAULT NULL,
  `enroll_date` date DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- 傾印資料表的資料 `enrollments`
--

INSERT INTO `enrollments` (`enrollment_id`, `student_id`, `course_id`, `enroll_date`) VALUES
(1, 'S2026001', 1, '2026-01-06'),
(2, 'S2026001', 2, '2026-01-06'),
(3, 'S2026008', 2, '2026-01-06'),
(4, 'S2026008', 4, '2026-01-06'),
(5, 'S2026003', 2, '2026-01-06'),
(6, 'S2026003', 4, '2026-01-06'),
(7, 'S2026004', 2, '2026-01-06'),
(8, 'S2026005', 3, '2026-01-06'),
(9, 'S2026009', 4, '2026-01-06'),
(12, 'S2025002', 3, '2026-01-06'),
(13, 'S2025001', 1, '2026-01-06');

-- --------------------------------------------------------

--
-- 資料表結構 `payment_records`
--

CREATE TABLE `payment_records` (
  `pay_id` int(11) NOT NULL,
  `student_id` varchar(20) NOT NULL,
  `amount` int(11) NOT NULL,
  `pay_date` datetime DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- 傾印資料表的資料 `payment_records`
--

INSERT INTO `payment_records` (`pay_id`, `student_id`, `amount`, `pay_date`) VALUES
(1, 'S2025001', 6000, '2025-08-20 16:00:00'),
(2, 'S2025002', 12000, '2025-09-15 11:00:00'),
(3, 'S2025001', 4000, '2025-10-10 10:30:00'),
(4, 'S2025003', 8000, '2025-10-12 14:00:00'),
(5, 'S2025001', 3500, '2025-11-05 17:20:00'),
(6, 'S2025004', 6000, '2025-11-25 09:00:00'),
(7, 'S2025002', 12000, '2025-12-20 15:00:00');

-- --------------------------------------------------------

--
-- 資料表結構 `students_pro`
--

CREATE TABLE `students_pro` (
  `id` int(11) NOT NULL,
  `student_id` varchar(20) NOT NULL COMMENT '學號/掃描碼',
  `name` varchar(50) NOT NULL COMMENT '姓名',
  `gender` enum('男','女','其他') DEFAULT '男',
  `phone` varchar(20) DEFAULT NULL COMMENT '學生手機',
  `parent_phone` varchar(20) NOT NULL COMMENT '家長緊急聯絡電話',
  `address` varchar(255) DEFAULT NULL,
  `status` enum('在學','休學','退班','畢業') DEFAULT '在學',
  `tuition_balance` int(11) DEFAULT 0 COMMENT '剩餘應繳學費 (欠款)',
  `notes` text DEFAULT NULL COMMENT '備註',
  `create_time` datetime DEFAULT current_timestamp(),
  `update_time` datetime DEFAULT current_timestamp() ON UPDATE current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- 傾印資料表的資料 `students_pro`
--

INSERT INTO `students_pro` (`id`, `student_id`, `name`, `gender`, `phone`, `parent_phone`, `address`, `status`, `tuition_balance`, `notes`, `create_time`, `update_time`) VALUES
(1, 'S2026001', '王小明', '男', '0912-345678', '0988-111222', '台北市信義區', '在學', 0, NULL, '2026-01-06 16:19:58', '2026-01-06 21:34:38'),
(2, 'S2026002', '李美美', '女', '0922-000111', '0977-333444', '新北市板橋區', '畢業', 0, NULL, '2026-01-06 16:19:58', '2026-01-06 16:43:42'),
(9, 'S2026003', '張書豪', '男', '0933-555-666', '0911-222-333', '桃園市中壢區延平路', '在學', 0, NULL, '2026-01-06 16:32:31', '2026-01-06 21:32:47'),
(10, 'S2026004', '黃品睿', '男', '0955-888-999', '0922-444-555', '台中市西屯區', '在學', 0, NULL, '2026-01-06 16:32:31', '2026-01-06 21:32:52'),
(11, 'S2026005', '許雅婷', '女', '0966-777-888', '0933-111-999', '高雄市苓雅區', '在學', 0, NULL, '2026-01-06 16:32:31', '2026-01-06 21:32:57'),
(12, 'S2026006', '王大同', '男', '0910-111-222', '0920-333-444', '台北市內湖區', '畢業', 0, NULL, '2026-01-06 16:32:31', '2026-01-06 16:43:38'),
(19, 'S2025001', '林志明', '男', '0912345678', '0922345678', '台北市信義路', '在學', 0, NULL, '2025-08-15 10:00:00', '2026-01-06 21:33:19'),
(20, 'S2025002', '陳靜宜', '女', '0933445566', '0944556677', '台北市大安區', '在學', 0, NULL, '2025-09-10 14:00:00', '2026-01-06 21:22:55'),
(21, 'S2025003', '王伯翰', '男', '0955667788', '0966778899', '新北市板橋區', '在學', 0, NULL, '2025-10-05 09:30:00', '2026-01-06 21:33:16'),
(22, 'S2025004', '張家豪', '男', '0911222333', '0922333444', '台北市內湖區', '畢業', 0, NULL, '2025-11-20 11:20:00', '2026-01-06 21:33:30'),
(23, 'S2026008', '李佳佳', '女', '0977888999', '0988999000', '台北市松山區', '在學', 0, NULL, '2026-01-02 15:45:00', '2026-01-06 21:33:08'),
(24, 'S2026009', '趙子龍', '男', '0919283746', '0928374655', '桃園市桃園區', '在學', 0, NULL, '2026-01-05 13:00:00', '2026-01-06 21:33:04');

-- --------------------------------------------------------

--
-- 資料表結構 `student_scores`
--

CREATE TABLE `student_scores` (
  `score_id` int(11) NOT NULL,
  `student_id` varchar(20) DEFAULT NULL,
  `subject` varchar(50) DEFAULT NULL,
  `score` int(11) DEFAULT NULL,
  `exam_date` date DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- 傾印資料表的資料 `student_scores`
--

INSERT INTO `student_scores` (`score_id`, `student_id`, `subject`, `score`, `exam_date`) VALUES
(1, 'S2025001', '英文小考', 85, '2026-01-05'),
(2, 'S2025001', '數學月考', 78, '2026-01-06'),
(3, 'S2026001', '英文小考', 92, '2026-01-05'),
(4, 'S2026001', '數學', 65, '2026-01-06');

-- --------------------------------------------------------

--
-- 資料表結構 `users`
--

CREATE TABLE `users` (
  `user_id` int(11) NOT NULL,
  `username` varchar(50) NOT NULL,
  `password` varchar(255) NOT NULL,
  `real_name` varchar(50) DEFAULT NULL,
  `role` enum('admin','staff','teacher') DEFAULT 'staff',
  `last_login` datetime DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- 傾印資料表的資料 `users`
--

INSERT INTO `users` (`user_id`, `username`, `password`, `real_name`, `role`, `last_login`) VALUES
(1, 'admin', '1234', '主任', 'admin', NULL),
(2, 'teacher01', '1234', '張大千老師', 'staff', NULL),
(3, 'teacher_wang', '1234', '王小英老師', 'staff', NULL),
(4, 'teacher_lee', '1234', '李大華老師', 'staff', NULL);

-- --------------------------------------------------------

--
-- 資料表結構 `work_attendance`
--

CREATE TABLE `work_attendance` (
  `log_id` int(11) NOT NULL,
  `user_id` int(11) NOT NULL,
  `check_in` datetime DEFAULT NULL,
  `check_out` datetime DEFAULT NULL,
  `work_date` date NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- 傾印資料表的資料 `work_attendance`
--

INSERT INTO `work_attendance` (`log_id`, `user_id`, `check_in`, `check_out`, `work_date`) VALUES
(1, 2, '2026-01-06 17:04:38', '2026-01-06 17:04:40', '2026-01-06'),
(2, 1, '2026-01-06 17:05:32', '2026-01-06 17:05:34', '2026-01-06');

--
-- 已傾印資料表的索引
--

--
-- 資料表索引 `attendance`
--
ALTER TABLE `attendance`
  ADD PRIMARY KEY (`attendance_id`);

--
-- 資料表索引 `courses`
--
ALTER TABLE `courses`
  ADD PRIMARY KEY (`course_id`),
  ADD KEY `teacher_id` (`teacher_id`);

--
-- 資料表索引 `course_schedule`
--
ALTER TABLE `course_schedule`
  ADD PRIMARY KEY (`schedule_id`),
  ADD KEY `course_id` (`course_id`);

--
-- 資料表索引 `enrollments`
--
ALTER TABLE `enrollments`
  ADD PRIMARY KEY (`enrollment_id`),
  ADD KEY `fk_enroll_student` (`student_id`),
  ADD KEY `fk_enroll_course` (`course_id`);

--
-- 資料表索引 `payment_records`
--
ALTER TABLE `payment_records`
  ADD PRIMARY KEY (`pay_id`);

--
-- 資料表索引 `students_pro`
--
ALTER TABLE `students_pro`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `student_id` (`student_id`);

--
-- 資料表索引 `student_scores`
--
ALTER TABLE `student_scores`
  ADD PRIMARY KEY (`score_id`),
  ADD KEY `student_id` (`student_id`);

--
-- 資料表索引 `users`
--
ALTER TABLE `users`
  ADD PRIMARY KEY (`user_id`),
  ADD UNIQUE KEY `username` (`username`);

--
-- 資料表索引 `work_attendance`
--
ALTER TABLE `work_attendance`
  ADD PRIMARY KEY (`log_id`),
  ADD KEY `user_id` (`user_id`);

--
-- 在傾印的資料表使用自動遞增(AUTO_INCREMENT)
--

--
-- 使用資料表自動遞增(AUTO_INCREMENT) `attendance`
--
ALTER TABLE `attendance`
  MODIFY `attendance_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=13;

--
-- 使用資料表自動遞增(AUTO_INCREMENT) `courses`
--
ALTER TABLE `courses`
  MODIFY `course_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=5;

--
-- 使用資料表自動遞增(AUTO_INCREMENT) `course_schedule`
--
ALTER TABLE `course_schedule`
  MODIFY `schedule_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=13;

--
-- 使用資料表自動遞增(AUTO_INCREMENT) `enrollments`
--
ALTER TABLE `enrollments`
  MODIFY `enrollment_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=14;

--
-- 使用資料表自動遞增(AUTO_INCREMENT) `payment_records`
--
ALTER TABLE `payment_records`
  MODIFY `pay_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=12;

--
-- 使用資料表自動遞增(AUTO_INCREMENT) `students_pro`
--
ALTER TABLE `students_pro`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=25;

--
-- 使用資料表自動遞增(AUTO_INCREMENT) `student_scores`
--
ALTER TABLE `student_scores`
  MODIFY `score_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=5;

--
-- 使用資料表自動遞增(AUTO_INCREMENT) `users`
--
ALTER TABLE `users`
  MODIFY `user_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=5;

--
-- 使用資料表自動遞增(AUTO_INCREMENT) `work_attendance`
--
ALTER TABLE `work_attendance`
  MODIFY `log_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=3;

--
-- 已傾印資料表的限制式
--

--
-- 資料表的限制式 `courses`
--
ALTER TABLE `courses`
  ADD CONSTRAINT `fk_teacher` FOREIGN KEY (`teacher_id`) REFERENCES `users` (`user_id`) ON DELETE SET NULL;

--
-- 資料表的限制式 `course_schedule`
--
ALTER TABLE `course_schedule`
  ADD CONSTRAINT `course_schedule_ibfk_1` FOREIGN KEY (`course_id`) REFERENCES `courses` (`course_id`) ON DELETE CASCADE;

--
-- 資料表的限制式 `enrollments`
--
ALTER TABLE `enrollments`
  ADD CONSTRAINT `fk_enroll_course` FOREIGN KEY (`course_id`) REFERENCES `courses` (`course_id`) ON DELETE CASCADE,
  ADD CONSTRAINT `fk_enroll_student` FOREIGN KEY (`student_id`) REFERENCES `students_pro` (`student_id`) ON DELETE CASCADE;

--
-- 資料表的限制式 `student_scores`
--
ALTER TABLE `student_scores`
  ADD CONSTRAINT `student_scores_ibfk_1` FOREIGN KEY (`student_id`) REFERENCES `students_pro` (`student_id`) ON DELETE CASCADE;

--
-- 資料表的限制式 `work_attendance`
--
ALTER TABLE `work_attendance`
  ADD CONSTRAINT `work_attendance_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`) ON DELETE CASCADE;
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;

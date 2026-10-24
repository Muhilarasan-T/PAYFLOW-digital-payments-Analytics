-- ============================================================================
-- PAYFLOW — Database Engineering & SQL Modeling
-- Script 01: Create Database and User Privileges
-- Database: payflow_db
-- Dialect: MySQL 8.0+
-- ============================================================================

-- Drop existing database if required (for repeatable setup)
-- DROP DATABASE IF EXISTS payflow_db;

-- Create database with UTF-8 character encoding for rupee symbols and footnotes
CREATE DATABASE IF NOT EXISTS payflow_db
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE payflow_db;

-- Display database verification
SELECT 
    DATABASE() AS current_database,
    @@character_set_database AS default_charset,
    @@collation_database AS default_collation,
    NOW() AS setup_timestamp;

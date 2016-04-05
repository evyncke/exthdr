-- phpMyAdmin SQL Dump
-- version 4.2.12deb2
-- http://www.phpmyadmin.net
--
-- Client :  localhost
-- Généré le :  Mar 26 Mai 2015 à 17:01
-- Version du serveur :  5.5.43-0+deb8u1
-- Version de PHP :  5.6.7-1

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8 */;

--
-- Base de données :  `ipv6status`
--

-- --------------------------------------------------------

--
-- Structure de la table `bgp_exthdr`
--

DROP TABLE IF EXISTS `bgp_exthdr`;
CREATE TABLE `bgp_exthdr` (
  `address` varchar(39) NOT NULL,
  `domain` text,
  `test` tinyint(4) NOT NULL,
  `hop` tinyint(4) NOT NULL,
  `router` varchar(39) DEFAULT NULL,
  `asn` smallint(6) DEFAULT NULL,
  `message` char(3) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

-- --------------------------------------------------------

--
-- Structure de la table `bgp_exthdr_summary`
--

DROP TABLE IF EXISTS `bgp_exthdr_summary`;
CREATE TABLE `bgp_exthdr_summary` (
  `dest_addr` varchar(39) NOT NULL,
  `domain` text,
  `dest_prefix` varchar(16) DEFAULT NULL,
  `dest_as` varchar(128) DEFAULT NULL,
  `test_nb` int(11) NOT NULL,
  `result` varchar(32) DEFAULT NULL,
  `dropping_addr` varchar(39) DEFAULT NULL,
  `dropping_as` varchar(128) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

-- --------------------------------------------------------

--
-- Structure de la table `exthdr`
--

DROP TABLE IF EXISTS `exthdr`;
CREATE TABLE `exthdr` (
  `address` varchar(39) NOT NULL,
  `domain` text,
  `test` tinyint(4) NOT NULL,
  `hop` tinyint(4) NOT NULL,
  `router` varchar(39) DEFAULT NULL,
  `asn` smallint(6) DEFAULT NULL,
  `message` char(3) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

-- --------------------------------------------------------

--
-- Structure de la table `exthdr_summary`
--

DROP TABLE IF EXISTS `exthdr_summary`;
CREATE TABLE `exthdr_summary` (
  `dest_addr` varchar(39) NOT NULL,
  `domain` text,
  `dest_prefix` varchar(16) DEFAULT NULL,
  `dest_as` varchar(128) DEFAULT NULL,
  `test_nb` int(11) NOT NULL,
  `result` varchar(32) DEFAULT NULL,
  `dropping_addr` varchar(39) DEFAULT NULL,
  `dropping_as` varchar(128) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

-- --------------------------------------------------------

--
-- Structure de la table `ixp`
--

DROP TABLE IF EXISTS `ixp`;
CREATE TABLE `ixp` (
  `address` varchar(39) NOT NULL,
  `asn` int(11) DEFAULT NULL,
  `as_name` varchar(128) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

DROP TABLE IF EXISTS `exthdr_results`;
CREATE TABLE `exthdr_results` (
  `result` varchar(32) NOT NULL,
  `color` varchar(32) DEFAULT NULL,
  `display_order` tinyint(4) DEFAULT NULL,
  `show_as` tinyint(1) DEFAULT NULL,
  PRIMARY KEY (`result`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `exthdr_results`
--

LOCK TABLES `exthdr_results` WRITE;
/*!40000 ALTER TABLE `exthdr_results` DISABLE KEYS */;
INSERT INTO `exthdr_results` VALUES ('destination AS drop','lightgreen',2,1),('destination host drop','lawngreen',1,1),('eh filtered by ISP','orange',3,0),('not dropped','green',0,0),('not reached','black',6,0),('transit AS drop','red',4,1),('unknown','gray',5,0);
/*!40000 ALTER TABLE `exthdr_results` ENABLE KEYS */;

--
-- Index pour la table `bgp_exthdr`
--
ALTER TABLE `bgp_exthdr`
 ADD PRIMARY KEY (`address`,`test`,`hop`);

--
-- Index pour la table `bgp_exthdr_summary`
--
ALTER TABLE `bgp_exthdr_summary`
 ADD PRIMARY KEY (`dest_addr`,`test_nb`);

--
-- Index pour la table `exthdr`
--
ALTER TABLE `exthdr`
 ADD PRIMARY KEY (`address`,`test`,`hop`);

--
-- Index pour la table `exthdr_summary`
--
ALTER TABLE `exthdr_summary`
 ADD PRIMARY KEY (`dest_addr`,`test_nb`);

--
-- Index pour la table `ixp`
--
ALTER TABLE `ixp`
 ADD PRIMARY KEY (`address`);

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;

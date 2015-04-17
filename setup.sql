
SET NAMES 'utf8';

DROP TABLE IF EXISTS docs;
CREATE TABLE docs (
  doc_id INT(11) UNSIGNED NOT NULL auto_increment,
  status SMALLINT(6) DEFAULT 1,
  url VARCHAR(255) NOT NULL,
  filetype VARCHAR(8) DEFAULT NULL,
  found_date DATETIME DEFAULT NULL,
  authors VARCHAR(255) DEFAULT NULL,
  title VARCHAR(255) DEFAULT NULL,
  abstract TEXT DEFAULT NULL,
  numwords SMALLINT(6) UNSIGNED DEFAULT NULL,
  source_url VARCHAR(255) DEFAULT NULL,
  meta_confidence FLOAT(4,3) UNSIGNED DEFAULT NULL,
  spamminess FLOAT(4,3) UNSIGNED DEFAULT NULL,
  content MEDIUMTEXT DEFAULT NULL,
  PRIMARY KEY (doc_id),
  KEY (found_date)
) ENGINE=InnoDB CHARACTER SET utf8;

DROP TABLE IF EXISTS topics;
CREATE TABLE topics (
  topic_id INT(11) UNSIGNED NOT NULL auto_increment,
  label VARCHAR(255) DEFAULT NULL,
  is_default TINYINT(1) UNSIGNED DEFAULT 0,
  PRIMARY KEY (topic_id),
  KEY (is_default)
) ENGINE=InnoDB CHARACTER SET utf8;

DROP TABLE IF EXISTS docs2topics;
CREATE TABLE docs2topics (
  doc_id INT(11) UNSIGNED NOT NULL,
  topic_id INT(11) UNSIGNED NOT NULL,
  strength FLOAT(4,3) UNSIGNED DEFAULT NULL,
  is_training TINYINT(1) UNSIGNED DEFAULT 0,
  PRIMARY KEY (doc_id, topic_id),
  KEY (doc_id),
  KEY (topic_id)
) ENGINE=InnoDB CHARACTER SET utf8;

INSERT INTO topics (label, is_default) VALUES ('Metaphysics', 1);
INSERT INTO topics (label, is_default) VALUES ('Epistemology', 1);
INSERT INTO topics (label, is_default) VALUES ('Language', 1);
INSERT INTO topics (label, is_default) VALUES ('Mind', 1);
INSERT INTO topics (label, is_default) VALUES ('Action', 1);
INSERT INTO topics (label, is_default) VALUES ('Religion', 1);
INSERT INTO topics (label, is_default) VALUES ('Aesthetics', 1);
INSERT INTO topics (label, is_default) VALUES ('Ethics', 1);
INSERT INTO topics (label, is_default) VALUES ('Law', 1);
INSERT INTO topics (label, is_default) VALUES ('Culture', 1);
INSERT INTO topics (label, is_default) VALUES ('Political', 1);
INSERT INTO topics (label, is_default) VALUES ('Science', 1);
INSERT INTO topics (label, is_default) VALUES ('Biology', 1);
INSERT INTO topics (label, is_default) VALUES ('Cognition', 1);
INSERT INTO topics (label, is_default) VALUES ('Physics', 1);
INSERT INTO topics (label, is_default) VALUES ('Logic', 1);
INSERT INTO topics (label, is_default) VALUES ('Mathematics', 1);
INSERT INTO topics (label, is_default) VALUES ('Ancient', 1);
INSERT INTO topics (label, is_default) VALUES ('Modern', 1);
INSERT INTO topics (label, is_default) VALUES ('Continental', 1);
INSERT INTO topics (label, is_default) VALUES ('Asian', 1);

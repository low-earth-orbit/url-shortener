-- users table
CREATE TABLE users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(320) UNIQUE NOT NULL
);

-- links table
CREATE TABLE links (
    link_id INT AUTO_INCREMENT PRIMARY KEY,
    destination VARCHAR(2048) NOT NULL,
    shortcut VARCHAR(6) UNIQUE NOT NULL, -- shortcut must be unique
    user_id INT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE -- if the associated user is deleted, the link will also be deleted
);

-- addUser
DELIMITER //
DROP PROCEDURE IF EXISTS addUser;
CREATE PROCEDURE addUser(IN _username VARCHAR(320))
BEGIN
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        SELECT 'Error occurred in addUser';
    END;

    INSERT INTO users(username) VALUES (_username);
END //
DELIMITER ;

-- createLink
-- We can either generate unique shortcut here or in the app. Generating shortcut here can avoid additional communication between DB and app in the rare case of collision. Either option is open. When we work with API we'll have a better idea.
DELIMITER //
DROP PROCEDURE IF EXISTS createLink;
CREATE PROCEDURE createLink(IN _destination VARCHAR(2048), IN _user_id INT)
BEGIN
    DECLARE _shortcut VARCHAR(6);
    DECLARE collision_flag INT DEFAULT 1;
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        SELECT 'Error occurred in createLink';
    END;

    -- Loop until a unique shortcut is generated
    WHILE collision_flag = 1 DO
        -- Generate a random 6-character string for shortcut
        SET _shortcut = LEFT(MD5(RAND()), 6); -- 6 characters consisting lowercase letter and number. If we want uppercase letter, we need to do it in the app side.

        -- Check if the shortcut already exists
        SELECT COUNT(*) INTO collision_flag FROM links WHERE shortcut = _shortcut;
    END WHILE; -- This while loop in extremely rare cases could be infinite; once we decided how/where to generate shortcut, we can write more defensively.

    -- Insert the new link with the unique shortcut
    INSERT INTO links(destination, shortcut, user_id) VALUES (_destination, _shortcut, _user_id);
    SELECT _shortcut AS generated_shortcut; -- returns generated shortcut
END //
DELIMITER ;

-- deleteLink
DELIMITER //
DROP PROCEDURE IF EXISTS deleteLink;
CREATE PROCEDURE deleteLink(IN _link_id INT)
BEGIN
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        SELECT 'Error occurred in deleteLink';
    END;

    DELETE FROM links WHERE link_id = _link_id;
END //
DELIMITER ;

-- getUserLinks
DELIMITER //
DROP PROCEDURE IF EXISTS getUserLinks;
CREATE PROCEDURE getUserLinks(IN _user_id INT)
BEGIN
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        SELECT 'Error occurred in getUserLinks';
    END;

    SELECT * FROM links WHERE user_id = _user_id;
END //
DELIMITER ;

-- getLinkDestination
DELIMITER //
DROP PROCEDURE IF EXISTS getLinkDestination;
CREATE PROCEDURE getLinkDestination(IN _shortcut VARCHAR(6))
BEGIN
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        SELECT 'Error occurred in getLinkDestination';
    END;

    SELECT destination FROM links WHERE shortcut = _shortcut;
END //
DELIMITER ;
UPDATE user_account
SET
    password_hash = '$argon2id$v=19$m=65536,t=3,p=4$TvtS/znYf4UUnty9hmDdPQ$KYQ+1IAxobgmLJvo46lOfQR1kpp9HRkuUlClDLA9tRU',
    status = 'active'
WHERE username IN ('stage7_importer', 'stage7_reader');

INSERT INTO user_account (
    user_id,
    username,
    password_hash,
    display_name,
    email,
    status
)
VALUES (
    7000003,
    'stage7_collaborator',
    '$argon2id$v=19$m=65536,t=3,p=4$TvtS/znYf4UUnty9hmDdPQ$KYQ+1IAxobgmLJvo46lOfQR1kpp9HRkuUlClDLA9tRU',
    'Stage7 Collaborator',
    'stage7_collaborator@example.com',
    'active'
)
ON CONFLICT (user_id) DO UPDATE
SET
    username = EXCLUDED.username,
    password_hash = EXCLUDED.password_hash,
    display_name = EXCLUDED.display_name,
    email = EXCLUDED.email,
    status = EXCLUDED.status;

INSERT INTO tree_collaborator (
    tree_id,
    user_id,
    access_role,
    invited_by,
    status
)
SELECT
    tree_id,
    7000003,
    'collaborator',
    7000001,
    'active'
FROM family_tree
WHERE tree_id BETWEEN 7001 AND 7010
ON CONFLICT (tree_id, user_id) DO UPDATE
SET
    access_role = EXCLUDED.access_role,
    invited_by = EXCLUDED.invited_by,
    status = EXCLUDED.status;

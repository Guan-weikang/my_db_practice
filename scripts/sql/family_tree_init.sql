BEGIN;

CREATE EXTENSION IF NOT EXISTS pg_trgm;

CREATE TABLE IF NOT EXISTS user_account (
    user_id BIGSERIAL PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    display_name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(20) NOT NULL DEFAULT 'active',
    CONSTRAINT chk_user_status
        CHECK (status IN ('active', 'disabled'))
);

CREATE TABLE IF NOT EXISTS family_tree (
    tree_id BIGSERIAL PRIMARY KEY,
    tree_name VARCHAR(100) NOT NULL,
    surname VARCHAR(50) NOT NULL,
    compiled_at DATE,
    creator_user_id BIGINT NOT NULL,
    description TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_tree_creator
        FOREIGN KEY (creator_user_id)
        REFERENCES user_account(user_id)
);

CREATE TABLE IF NOT EXISTS tree_collaborator (
    tree_id BIGINT NOT NULL,
    user_id BIGINT NOT NULL,
    access_role VARCHAR(20) NOT NULL,
    invited_by BIGINT NOT NULL,
    invited_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(20) NOT NULL DEFAULT 'active',
    CONSTRAINT pk_tree_collaborator
        PRIMARY KEY (tree_id, user_id),
    CONSTRAINT fk_collab_tree
        FOREIGN KEY (tree_id)
        REFERENCES family_tree(tree_id),
    CONSTRAINT fk_collab_user
        FOREIGN KEY (user_id)
        REFERENCES user_account(user_id),
    CONSTRAINT fk_collab_invited_by
        FOREIGN KEY (invited_by)
        REFERENCES user_account(user_id),
    CONSTRAINT chk_collab_role
        CHECK (access_role IN ('collaborator', 'reader')),
    CONSTRAINT chk_collab_status
        CHECK (status IN ('active', 'revoked', 'pending'))
);

CREATE TABLE IF NOT EXISTS member (
    member_id BIGSERIAL PRIMARY KEY,
    tree_id BIGINT NOT NULL,
    name VARCHAR(100) NOT NULL,
    gender VARCHAR(10) NOT NULL,
    birth_date DATE,
    death_date DATE,
    generation_no INT,
    generation_name VARCHAR(50),
    biography TEXT,
    is_alive BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_member_tree_member
        UNIQUE (tree_id, member_id),
    CONSTRAINT fk_member_tree
        FOREIGN KEY (tree_id)
        REFERENCES family_tree(tree_id),
    CONSTRAINT chk_member_gender
        CHECK (gender IN ('male', 'female', 'unknown')),
    CONSTRAINT chk_member_life_span
        CHECK (
            birth_date IS NULL
            OR death_date IS NULL
            OR death_date >= birth_date
        ),
    CONSTRAINT chk_member_alive_death
        CHECK (
            is_alive = FALSE
            OR death_date IS NULL
        ),
    CONSTRAINT chk_generation_no_positive
        CHECK (
            generation_no IS NULL
            OR generation_no > 0
        )
);

CREATE TABLE IF NOT EXISTS parent_child (
    tree_id BIGINT NOT NULL,
    parent_member_id BIGINT NOT NULL,
    child_member_id BIGINT NOT NULL,
    parent_role VARCHAR(10) NOT NULL,
    CONSTRAINT pk_parent_child
        PRIMARY KEY (tree_id, parent_member_id, child_member_id, parent_role),
    CONSTRAINT fk_pc_parent
        FOREIGN KEY (tree_id, parent_member_id)
        REFERENCES member(tree_id, member_id),
    CONSTRAINT fk_pc_child
        FOREIGN KEY (tree_id, child_member_id)
        REFERENCES member(tree_id, member_id),
    CONSTRAINT uq_child_parent_role
        UNIQUE (tree_id, child_member_id, parent_role),
    CONSTRAINT chk_parent_role
        CHECK (parent_role IN ('father', 'mother')),
    CONSTRAINT chk_parent_not_self
        CHECK (parent_member_id <> child_member_id)
);

CREATE TABLE IF NOT EXISTS marriage (
    tree_id BIGINT NOT NULL,
    member_id_1 BIGINT NOT NULL,
    member_id_2 BIGINT NOT NULL,
    married_at DATE,
    ended_at DATE,
    status VARCHAR(20) NOT NULL DEFAULT 'active',
    CONSTRAINT pk_marriage
        PRIMARY KEY (tree_id, member_id_1, member_id_2),
    CONSTRAINT fk_marriage_member_1
        FOREIGN KEY (tree_id, member_id_1)
        REFERENCES member(tree_id, member_id),
    CONSTRAINT fk_marriage_member_2
        FOREIGN KEY (tree_id, member_id_2)
        REFERENCES member(tree_id, member_id),
    CONSTRAINT chk_marriage_distinct
        CHECK (member_id_1 <> member_id_2),
    CONSTRAINT chk_marriage_order
        CHECK (member_id_1 < member_id_2),
    CONSTRAINT chk_marriage_status
        CHECK (status IN ('active', 'ended'))
);

CREATE INDEX IF NOT EXISTS idx_family_tree_creator
ON family_tree(creator_user_id);

CREATE INDEX IF NOT EXISTS idx_tree_collaborator_user_status_tree
ON tree_collaborator(user_id, status, tree_id);

CREATE INDEX IF NOT EXISTS idx_tree_collaborator_tree_status_user
ON tree_collaborator(tree_id, status, user_id);

CREATE INDEX IF NOT EXISTS idx_member_tree_name
ON member(tree_id, name);

CREATE INDEX IF NOT EXISTS idx_member_tree_generation
ON member(tree_id, generation_no);

CREATE INDEX IF NOT EXISTS idx_member_tree_gender_birth
ON member(tree_id, gender, birth_date);

CREATE INDEX IF NOT EXISTS idx_parent_child_tree_parent
ON parent_child(tree_id, parent_member_id);

CREATE INDEX IF NOT EXISTS idx_parent_child_tree_child
ON parent_child(tree_id, child_member_id);

CREATE INDEX IF NOT EXISTS idx_marriage_tree_member1
ON marriage(tree_id, member_id_1);

CREATE INDEX IF NOT EXISTS idx_marriage_tree_member2
ON marriage(tree_id, member_id_2);

CREATE INDEX IF NOT EXISTS idx_member_name_trgm
ON member USING gin (name gin_trgm_ops);

CREATE OR REPLACE FUNCTION prevent_parent_child_cycle()
RETURNS TRIGGER AS $$
DECLARE
    cycle_found BOOLEAN;
BEGIN
    IF NEW.parent_member_id = NEW.child_member_id THEN
        RAISE EXCEPTION 'parent_member_id and child_member_id cannot be identical';
    END IF;

    WITH RECURSIVE ancestor_path AS (
        SELECT
            pc.tree_id,
            pc.parent_member_id,
            pc.child_member_id
        FROM parent_child pc
        WHERE pc.tree_id = NEW.tree_id
          AND pc.child_member_id = NEW.parent_member_id

        UNION ALL

        SELECT
            pc.tree_id,
            pc.parent_member_id,
            pc.child_member_id
        FROM ancestor_path ap
        JOIN parent_child pc
          ON pc.tree_id = ap.tree_id
         AND pc.child_member_id = ap.parent_member_id
    )
    SELECT EXISTS (
        SELECT 1
        FROM ancestor_path
        WHERE parent_member_id = NEW.child_member_id
    )
    INTO cycle_found;

    IF cycle_found THEN
        RAISE EXCEPTION
            'adding parent-child relation (tree_id=%, parent_member_id=%, child_member_id=%) would create an ancestor cycle',
            NEW.tree_id, NEW.parent_member_id, NEW.child_member_id;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_prevent_parent_child_cycle ON parent_child;

CREATE TRIGGER trg_prevent_parent_child_cycle
BEFORE INSERT OR UPDATE ON parent_child
FOR EACH ROW
EXECUTE FUNCTION prevent_parent_child_cycle();

COMMIT;

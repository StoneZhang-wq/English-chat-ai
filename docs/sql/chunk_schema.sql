-- =============================================================================
-- 英语学习 APP - 语块/句型数据库建表语句 (MySQL)
-- 表1: chunk_core 语块/句型核心表
-- 表2: scene_label 场景标签表（一级/二级/三级场景）
-- 表3: chunk_scene_mapping 语块-场景多对多关联表
-- 扩展: user_scene_weight 用户场景权重（多用户时用）、user_chunk_progress 用户语块学习进度
-- =============================================================================

-- 表1：语块/句型核心表（核心业务表，存储学习内容基础信息）
CREATE TABLE IF NOT EXISTS chunk_core (
    chunk_id        BIGINT          NOT NULL AUTO_INCREMENT COMMENT '语块/句型唯一标识',
    chunk           VARCHAR(500)    NOT NULL COMMENT '英语语块/句型原文（核心学习内容）',
    difficulty      TINYINT         NOT NULL COMMENT '难度等级：1=最低，2=中等，3=最高',
    category        TINYINT         NOT NULL COMMENT '内容类型：1=语块，2=句型',
    learn_count     INT             NOT NULL DEFAULT 0 COMMENT '该内容的用户累计学习次数（单用户或聚合）',
    correct_count   INT             NOT NULL DEFAULT 0 COMMENT '该内容的用户累计回答正确次数',
    last_correct    TINYINT         NOT NULL DEFAULT 1 COMMENT '0=上次回答错误，1=上次回答正确',
    weight          DECIMAL(10,2)   NOT NULL DEFAULT 0.00 COMMENT '该内容自身权重（同场景下优先排序）',
    created_at      DATETIME        DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    PRIMARY KEY (chunk_id),
    UNIQUE KEY uk_chunk_core_chunk (chunk(191))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='语块/句型核心表';

-- 表2：场景标签表（存储分级场景信息，关联用户兴趣权重）
CREATE TABLE IF NOT EXISTS scene_label (
    label_id        BIGINT          NOT NULL AUTO_INCREMENT COMMENT '场景标签唯一标识',
    first_scene     VARCHAR(100)    NOT NULL COMMENT '一级场景（如：商务、日常、旅行）',
    second_scene    VARCHAR(100)    NOT NULL COMMENT '二级场景（如：商务-谈判、日常-购物）',
    third_scene     VARCHAR(100)    NOT NULL COMMENT '三级场景（如：商务-谈判-价格协商）',
    weight          DECIMAL(10,2)   NOT NULL DEFAULT 0.00 COMMENT '该场景的用户兴趣权重（优先生成卡片）',
    created_at      DATETIME        DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    PRIMARY KEY (label_id),
    UNIQUE KEY uk_scene_label_hierarchy (first_scene, second_scene, third_scene)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='场景标签表';

-- 表3：语块-场景映照关系表（多对多）
CREATE TABLE IF NOT EXISTS chunk_scene_mapping (
    chunk_id        BIGINT          NOT NULL COMMENT '关联 chunk_core.chunk_id',
    label_id        BIGINT          NOT NULL COMMENT '关联 scene_label.label_id',
    created_at      DATETIME        DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    PRIMARY KEY (chunk_id, label_id),
    KEY idx_chunk_scene_mapping_label (label_id),
    CONSTRAINT fk_csm_chunk FOREIGN KEY (chunk_id) REFERENCES chunk_core(chunk_id) ON DELETE CASCADE,
    CONSTRAINT fk_csm_label FOREIGN KEY (label_id) REFERENCES scene_label(label_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='语块-场景多对多关联表';

-- -----------------------------------------------------------------------------
-- 扩展表（多用户时使用：用户维度的场景权重与语块学习进度）
-- -----------------------------------------------------------------------------

-- 用户场景权重表（每个用户对每个场景的兴趣权重，用于卡片生成排序）
CREATE TABLE IF NOT EXISTS user_scene_weight (
    user_id         VARCHAR(64)     NOT NULL COMMENT '用户标识',
    label_id        BIGINT          NOT NULL COMMENT '关联 scene_label.label_id',
    weight          DECIMAL(10,2)   NOT NULL DEFAULT 0.00 COMMENT '该用户在该场景下的兴趣权重',
    updated_at      DATETIME        DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, label_id),
    KEY idx_usw_label (label_id),
    CONSTRAINT fk_usw_label FOREIGN KEY (label_id) REFERENCES scene_label(label_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户场景权重';

-- 用户语块学习进度表（每个用户对每个语块的学习次数、正确次数、上次是否正确）
CREATE TABLE IF NOT EXISTS user_chunk_progress (
    user_id         VARCHAR(64)     NOT NULL COMMENT '用户标识',
    chunk_id        BIGINT          NOT NULL COMMENT '关联 chunk_core.chunk_id',
    learn_count     INT             NOT NULL DEFAULT 0 COMMENT '该用户对该语块的学习次数',
    correct_count   INT             NOT NULL DEFAULT 0 COMMENT '该用户对该语块的正确次数',
    last_correct    TINYINT         NOT NULL DEFAULT 1 COMMENT '0=上次错误，1=上次正确',
    last_learned_at DATETIME        NULL COMMENT '最后学习时间',
    PRIMARY KEY (user_id, chunk_id),
    KEY idx_ucp_chunk (chunk_id),
    CONSTRAINT fk_ucp_chunk FOREIGN KEY (chunk_id) REFERENCES chunk_core(chunk_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户语块学习进度';

-- -----------------------------------------------------------------------------
-- 枚举说明（应用层约定）
-- chunk_core.difficulty: 1=最低, 2=中等, 3=最高
-- chunk_core.category:   1=语块(含词组/单词/俚语), 2=句型(含语法/句子)
-- chunk_core.last_correct / user_chunk_progress.last_correct: 0=错误, 1=正确
-- =============================================================================

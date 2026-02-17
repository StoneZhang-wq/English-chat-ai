-- Supabase 用户记忆表结构（在 SQL Editor 中执行）
-- 用于 MEMORY_BACKEND=supabase 时：user_profile、diary、npc_learn_progress（学习进度）
-- session_temp 仅当次会话临时数据，不落库。
-- 若之前建过 user_session_temp，可先执行：drop table if exists user_session_temp;

-- 用户表（id = 用户名/账户 ID，profile = user_profile.json 整份内容）
create table if not exists users (
  id text primary key,
  name text,
  profile jsonb default '{}',
  created_at timestamptz default now(),
  last_updated timestamptz
);

-- 用户日记（每用户一行，data = 整份 diary.json）
create table if not exists user_diary (
  user_id text primary key references users(id) on delete cascade,
  data jsonb default '{"version":"1.0","last_updated":null,"entries":[]}',
  last_updated timestamptz
);

-- 用户 NPC 学习进度（各场景下已学完的 NPC，用于解锁与判断）
create table if not exists user_npc_learn_progress (
  user_id text primary key references users(id) on delete cascade,
  data jsonb default '{}',
  updated_at timestamptz default now()
);

-- ---------- 若你已有旧表，可执行以下升级（删除不再使用的表、确保新表存在）----------
-- drop table if exists user_session_temp;
-- 然后执行上面的 create table user_npc_learn_progress（若尚未创建）

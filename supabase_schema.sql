-- Create a table to log uploads
create table if not exists uploads (
  id uuid primary key default gen_random_uuid(),
  user_email text,
  filename text not null,
  n_rows integer,
  n_cols integer,
  uploaded_at timestamp with time zone default now()
);

-- Preferences per user (store goal per dimension/item)
create table if not exists preferences (
  id uuid primary key default gen_random_uuid(),
  user_email text unique,
  goal numeric default 4.0,
  created_at timestamp with time zone default now(),
  updated_at timestamp with time zone default now()
);

-- Enable Row Level Security (optional, tighten as needed)
alter table uploads enable row level security;
alter table preferences enable row level security;

-- Simple policies for authenticated users
create policy "uploads_read_own" on uploads for select
  using (auth.uid() is not null);

create policy "uploads_insert_any" on uploads for insert
  with check (auth.uid() is not null);

create policy "preferences_read_own" on preferences for select
  using (auth.uid() is not null);

create policy "preferences_upsert_own" on preferences for insert with check (auth.uid() is not null);
create policy "preferences_update_own" on preferences for update using (auth.uid() is not null);

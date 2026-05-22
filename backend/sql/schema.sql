-- BookLeaf AI Support Automation Platform schema

create extension if not exists "pgcrypto";

create table if not exists public.authors (
    id uuid primary key default gen_random_uuid(),
    full_name text not null,
    email text unique,
    genre text,
    country text,
    active boolean not null default true,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create index if not exists idx_authors_full_name on public.authors (full_name);

create table if not exists public.books (
    id uuid primary key default gen_random_uuid(),
    author_id uuid not null references public.authors(id) on delete cascade,
    title text not null,
    isbn text unique,
    publication_date date,
    status text not null default 'published',
    support_tier text not null default 'standard',
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create index if not exists idx_books_author_id on public.books (author_id);
create index if not exists idx_books_title on public.books (title);

create table if not exists public.add_on_services (
    id uuid primary key default gen_random_uuid(),
    book_id uuid not null references public.books(id) on delete cascade,
    service_name text not null,
    service_type text not null,
    monthly_fee numeric(10,2) not null,
    status text not null default 'active',
    started_at timestamptz not null default now(),
    ended_at timestamptz,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create index if not exists idx_add_on_services_book_id on public.add_on_services (book_id);

create table if not exists public.queries (
    id uuid primary key default gen_random_uuid(),
    channel text not null default 'web-chat',
    customer_name text,
    customer_email text,
    message text not null,
    intent text,
    status text not null default 'open',
    response_time_ms integer,
    book_id uuid references public.books(id) on delete set null,
    metadata jsonb not null default '{}'::jsonb,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create index if not exists idx_queries_status on public.queries (status);
create index if not exists idx_queries_created_at on public.queries (created_at desc);

create table if not exists public.escalations (
    id uuid primary key default gen_random_uuid(),
    query_id uuid not null references public.queries(id) on delete cascade,
    escalation_level integer not null default 1,
    reason text not null,
    assigned_to text,
    priority text not null default 'medium',
    status text not null default 'open',
    resolved_at timestamptz,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create index if not exists idx_escalations_query_id on public.escalations (query_id);
create index if not exists idx_escalations_status on public.escalations (status);

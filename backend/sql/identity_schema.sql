create table if not exists public.author_identities (
    id uuid primary key default gen_random_uuid(),
    author_id uuid not null references public.authors(id) on delete cascade,
    platform text not null,
    identity_value text not null,
    normalized_value text not null,
    verified boolean not null default true,
    metadata jsonb not null default '{}'::jsonb,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    unique(author_id, platform, normalized_value)
);

create index if not exists idx_author_identities_author_id on public.author_identities(author_id);
create index if not exists idx_author_identities_platform on public.author_identities(platform);
create index if not exists idx_author_identities_normalized on public.author_identities(normalized_value);

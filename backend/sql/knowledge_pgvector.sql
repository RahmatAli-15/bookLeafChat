create extension if not exists vector;

create table if not exists public.knowledge_documents (
    id uuid primary key,
    title text not null,
    source_path text not null,
    metadata jsonb not null default '{}'::jsonb,
    created_at timestamptz not null default now()
);

create table if not exists public.knowledge_chunks (
    id text primary key,
    document_id uuid not null references public.knowledge_documents(id) on delete cascade,
    chunk_index integer not null,
    content text not null,
    embedding vector(384) not null,
    metadata jsonb not null default '{}'::jsonb,
    created_at timestamptz not null default now()
);

create index if not exists idx_knowledge_chunks_document_id on public.knowledge_chunks(document_id);
create index if not exists idx_knowledge_chunks_embedding on public.knowledge_chunks using ivfflat (embedding vector_cosine_ops) with (lists = 100);

create or replace function public.match_knowledge_chunks(
    query_embedding vector(384),
    match_count int default 5,
    match_threshold float default 0.45
)
returns table (
    chunk_id text,
    document_id uuid,
    title text,
    source_path text,
    content text,
    metadata jsonb,
    similarity float
)
language sql
as $$
    select
        kc.id as chunk_id,
        kc.document_id,
        kd.title,
        kd.source_path,
        kc.content,
        kc.metadata,
        1 - (kc.embedding <=> query_embedding) as similarity
    from public.knowledge_chunks kc
    join public.knowledge_documents kd on kd.id = kc.document_id
    where 1 - (kc.embedding <=> query_embedding) >= match_threshold
    order by kc.embedding <=> query_embedding
    limit match_count;
$$;
